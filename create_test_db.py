#!/usr/bin/env python3
"""
Creates a test database and test tables for HabitTracker.
Safe to run multiple times. Uses hardcoded credentials for local setup.
"""

import psycopg2
from psycopg2 import sql

# Superuser connection (used to create DB and role)
SUPER_DB = "postgres"
SUPER_USER = "tutor"
SUPER_PASS = "warren"
PG_HOST = "localhost"
PG_PORT = "5432"

# Test database and role
TEST_DB = "habitdb_test"
TEST_USER = "tutor"
TEST_PASS = "warren"

def ensure_test_db_and_role():
    conn = psycopg2.connect(
        dbname=SUPER_DB,
        user=SUPER_USER,
        password=SUPER_PASS,
        host=PG_HOST,
        port=PG_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Create role if missing
    cur.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{TEST_USER}') THEN
                CREATE ROLE {TEST_USER} LOGIN PASSWORD '{TEST_PASS}';
            END IF;
        END
        $$;
        """
    )

    # Create test database if missing
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB,))
    if not cur.fetchone():
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TEST_DB)))
        print(f"✅ Created test database: {TEST_DB}")
    else:
        print(f"ℹ️ Test database already exists: {TEST_DB}")

    # Grant privileges
    cur.execute(
        sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}")
        .format(sql.Identifier(TEST_DB), sql.Identifier(TEST_USER))
    )

    cur.close()
    conn.close()

def create_test_tables():
    conn = psycopg2.connect(
        dbname=TEST_DB,
        user=TEST_USER,
        password=TEST_PASS,
        host=PG_HOST,
        port=PG_PORT
    )
    cur = conn.cursor()

    # Create habits table for testing
    cur.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            frequency TEXT CHECK (frequency IN ('Daily','Weekly')) NOT NULL
        );
    """)

    # Create habit_completions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS habit_completions (
            id SERIAL PRIMARY KEY,
            habit_id INTEGER REFERENCES habits(id) ON DELETE CASCADE,
            completed_on DATE NOT NULL,
            UNIQUE (habit_id, completed_on)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Test tables created.")

def main():
    try:
        ensure_test_db_and_role()
        create_test_tables()
        print("🎉 Test database setup complete.")
    except Exception as e:
        print("❌ Error during setup:", e)

if __name__ == "__main__":
    main()