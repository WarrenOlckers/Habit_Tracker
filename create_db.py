"""
Because the database is on a local host the details credentials are given.
- Creates the database and role if missing, creates tables and constraints,
  and seeds idempotent dummy data (last 30 days for Daily, last 6 week-starts for Weekly)
"""
import sys
from datetime import date, timedelta
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

# -------------------------
# Hard-coded connection info
# -------------------------
# Superuser connection params (used to create database and role)
SUPER_DB = "postgres"
SUPER_USER = "tutor"
SUPER_PASS = "warren"

# Application database and role
APP_DB = "habitdb"
APP_USER = "tutor"
APP_PASS = "warren"

PG_HOST = "localhost"
PG_PORT = "5432"
# -------------------------

def ensure_database_and_role():
    """Create application role and database if missing, grant privileges."""
    conn = psycopg2.connect(dbname=SUPER_DB, user=SUPER_USER,
                            password=SUPER_PASS, host=PG_HOST, port=PG_PORT)
    conn.autocommit = True
    cur = conn.cursor()

    # Create role if not exists
    cur.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = %s) THEN
                CREATE ROLE {app_user} LOGIN PASSWORD %s;
            END IF;
        END
        $$;
        """.format(app_user=sql.Identifier(APP_USER).string),
        (APP_USER, APP_PASS)
    )

    # Create database if not exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (APP_DB,))
    if not cur.fetchone():
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(APP_DB)))
        print(f"Created database {APP_DB}")
    else:
        print(f"Database {APP_DB} already exists")

    # Grant privileges on database to app role
    cur.execute(
        sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}")
        .format(sql.Identifier(APP_DB), sql.Identifier(APP_USER))
    )

    cur.close()
    conn.close()


def migrate_and_seed():
    """Create tables, constraints, and insert idempotent seed data."""
    conn = psycopg2.connect(dbname=APP_DB, user=APP_USER,
                            password=APP_PASS, host=PG_HOST, port=PG_PORT,
                            cursor_factory=RealDictCursor)
    cur = conn.cursor()

    # Create habits table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            frequency TEXT CHECK (frequency IN ('Daily','Weekly')) NOT NULL
        );
    """)

    # Add unique constraint on (name, frequency) if missing
    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'habits_name_frequency_unique'
        ) THEN
            ALTER TABLE habits ADD CONSTRAINT habits_name_frequency_unique UNIQUE (name, frequency);
        END IF;
    END
    $$;
    """)

    # Create habit_completions table with UNIQUE to avoid duplicates
    cur.execute("""
        CREATE TABLE IF NOT EXISTS habit_completions (
            id SERIAL PRIMARY KEY,
            habit_id INTEGER REFERENCES habits(id) ON DELETE CASCADE,
            completed_on DATE NOT NULL,
            UNIQUE (habit_id, completed_on)
        );
    """)

    conn.commit()

    # Seed data (idempotent)
    seed_habits = [
        ("run or cycle", "Daily"),
        ("Strength training", "Weekly"),
        ("Study", "Daily"),
        ("Attend lectures", "Weekly"),
        ("Drink water (2 litres)", "Daily"),
    ]

    today = date.today()
    yesterday = today - timedelta(days=1)

    for name, freq in seed_habits:
        # Upsert habit and get id
        cur.execute("""
            INSERT INTO habits (name, frequency)
            VALUES (%s, %s)
            ON CONFLICT (name, frequency) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
        """, (name, freq))
        row = cur.fetchone()
        habit_id = row['id']

        if freq == "Daily":
            # Insert last 30 days including today
            for i in range(30):
                d = yesterday - timedelta(days=i)
                cur.execute("""
                    INSERT INTO habit_completions (habit_id, completed_on)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (habit_id, d))
        else:
            # Insert one completion per week for last 6 weeks (use Monday as week start)
            start_of_week_for_yesterday = yesterday - timedelta(days=today.weekday())
            for i in range(6):
                wk = start_of_week_for_yesterday - timedelta(weeks=i)
                cur.execute("""
                    INSERT INTO habit_completions (habit_id, completed_on)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (habit_id, wk))

    conn.commit()
    cur.close()
    conn.close()
    print("Migration and seeding complete.")


def main():
    try:
        ensure_database_and_role()
    except Exception as e:
        print("Error ensuring database/role:", e)
        sys.exit(1)

    try:
        migrate_and_seed()
    except Exception as e:
        print("Error migrating/seeding:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()