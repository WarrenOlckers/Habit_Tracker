import psycopg2
from datetime import date, timedelta
import argparse
import os
from psycopg2.extras import RealDictCursor

class Habit:
    def __init__(self, name, frequency):
        if frequency not in ["Daily", "Weekly"]:
            raise ValueError("Frequency must be 'Daily' or 'Weekly'")
        self.name = name
        self.frequency = frequency

class HabitTracker:
    def __init__(self):
        self.conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        user=os.getenv("PGUSER", "tutor"),
        password=os.getenv("PGPASSWORD", "warren"),
        dbname=os.getenv("PGDATABASE", "habitdb"),
        cursor_factory=RealDictCursor
    )
        self.cursor = self.conn.cursor()
        self.setup_tables()

    def setup_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                frequency TEXT CHECK (frequency IN ('Daily', 'Weekly')) NOT NULL
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS habit_completions (
                id SERIAL PRIMARY KEY,
                habit_id INTEGER REFERENCES habits(id),
                completed_on DATE NOT NULL
            );
        """)
        self.conn.commit()
        print("Tables setup!")
        print("Type: \"python habit_tracker.py -h\" for help")


    def add_habit(self, habit):
        self.cursor.execute(
            "INSERT INTO habits (name, frequency) VALUES (%s, %s)",
            (habit.name, habit.frequency)
        )
        self.conn.commit()
        print("habit added successfully!")

    def list_all_habits(self):
        self.cursor.execute("SELECT id, name, frequency FROM habits")
        return self.cursor.fetchall()

    def list_habits_by_frequency(self, frequency):
        self.cursor.execute(
            "SELECT id, name FROM habits WHERE frequency = %s", (frequency,)
        )
        return self.cursor.fetchall()

    def mark_completed(self, habit_id):
        today = date.today()
        self.cursor.execute(
            "INSERT INTO habit_completions (habit_id, completed_on) VALUES (%s, %s)",
            (habit_id, today)
        )
        self.conn.commit()

    def longest_streak_for_habit(self, habit_id):
        self.cursor.execute("SELECT frequency FROM habits WHERE id = %s", (habit_id,))
        freq = self.cursor.fetchone()['frequency']

        if freq == "Daily":
            query = """
                SELECT COUNT(*) FROM (
                    SELECT completed_on - ROW_NUMBER() OVER (ORDER BY completed_on) * INTERVAL '1 day' AS grp
                    FROM habit_completions
                    WHERE habit_id = %s
                ) streaks
                GROUP BY grp
                ORDER BY COUNT(*) DESC
                LIMIT 1
            """
        elif freq == "Weekly":
            query = """
                SELECT COUNT(*) FROM (
                    SELECT DATE_TRUNC('week', completed_on) - ROW_NUMBER() OVER (ORDER BY DATE_TRUNC('week', completed_on)) * INTERVAL '1 week' AS grp
                    FROM (
                        SELECT DISTINCT DATE_TRUNC('week', completed_on) AS completed_on
                        FROM habit_completions
                        WHERE habit_id = %s
                    ) weeks
                ) streaks
                GROUP BY grp
                ORDER BY COUNT(*) DESC
                LIMIT 1
            """
        else:
            return 0

        self.cursor.execute(query, (habit_id,))
        result = self.cursor.fetchone()
        return result['count'] if result else 0

    def longest_streak_all(self):
        self.cursor.execute("SELECT id, name FROM habits")
        habits = self.cursor.fetchall()
        max_streak = 0
        best_habit = None

        for habit in habits:

            habit_id = habit['id']
            name = habit['name']

            try:
                streak = self.longest_streak_for_habit(habit_id)
            except Exception as e:
                print(f"Error calculating streak for habit {habit_id}: {e}")
            continue
            
            if streak > max_streak:
                max_streak = streak
                best_habit = (habit_id, name)

        return (*best_habit, max_streak) if best_habit else None

    def insert_dummy_data(self):
        habits = [
            ("Morning Meditation", "Daily"),
            ("Weekly Gym Session", "Weekly"),
            ("Read 10 Pages", "Daily"),
            ("Sunday Meal Prep", "Weekly"),
            ("Write Journal Entry", "Daily")
        ]
        for name, freq in habits:
            self.cursor.execute("INSERT INTO habits (name, frequency) VALUES (%s, %s)", (name, freq))
        self.conn.commit()

        completions = {
            1: [date(2025, 9, 22) + timedelta(days=i) for i in range(28)],
            2: [date(2025, 9, 23), date(2025, 9, 30), date(2025, 10, 7), date(2025, 10, 14)],
            3: [date(2025, 9, 22), date(2025, 9, 23), date(2025, 9, 25), date(2025, 9, 27),
                date(2025, 9, 30), date(2025, 10, 1), date(2025, 10, 3), date(2025, 10, 5),
                date(2025, 10, 8), date(2025, 10, 10), date(2025, 10, 12), date(2025, 10, 14),
                date(2025, 10, 17), date(2025, 10, 19)],
            4: [date(2025, 9, 28), date(2025, 10, 5), date(2025, 10, 12), date(2025, 10, 19)],
            5: [date(2025, 9, 22) + timedelta(days=i) for i in range(14)] +
               [date(2025, 10, 13) + timedelta(days=i) for i in range(7)]
        }

        for habit_id, dates in completions.items():
            for d in dates:
                self.cursor.execute(
                    "INSERT INTO habit_completions (habit_id, completed_on) VALUES (%s, %s)",
                    (habit_id, d)
                )
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()

def main():
    parser = argparse.ArgumentParser(description=" Welcome to Habit Tracker Interface")
    parser.add_argument("action", choices=[
        
        "add",
        "\n   list_all", 
        "\n   list_by_frequency", 
        "\n   complete",
        "\n   longest_streak_for", 
        "\n   longest_streak_all", 
        "\n   insert_dummy"
    ])
    parser.add_argument("--name", help="Habit name")
    parser.add_argument("--frequency", help="Daily or Weekly")
    parser.add_argument("--id", type=int, help="Habit ID")
    args = parser.parse_args()

    tracker = HabitTracker()

    if args.action == "add":
        if args.name and args.frequency:
            habit = Habit(args.name, args.frequency)
            tracker.add_habit(habit)
            print("Habit added.")
        else:
            print("Please provide --name and --frequency.")
    elif args.action == "list_all":
        habits = tracker.list_all_habits()
        for h in habits:
            print(f"{h['id']}: {h['name']} ({h['frequency']})")
    elif args.action == "list_by_frequency":
        if args.frequency:
            habits = tracker.list_habits_by_frequency(args.frequency)
            for h in habits:
                print(f"{h['id']}: {h['name']}")
        else:
            print("Please provide --frequency Daily or Weekly.")
    elif args.action == "complete":
        if args.id:
            tracker.mark_completed(args.id)
            print("Habit marked as completed.")
        else:
            print("Please provide --id.")
    elif args.action == "longest_streak_for":
        if args.id:
            streak = tracker.longest_streak_for_habit(args.id)
            print(f"Longest streak for habit {args.id}: {streak}")
        else:
            print("Please provide --id.")
    elif args.action == "longest_streak_all":
        result = tracker.longest_streak_all()
        if result:
            print(f"Longest streak: {result[2]} (Habit {result[0]}: {result[1]})")
        else:
            print("No streaks found.")
    elif args.action == "insert_dummy":
        tracker.insert_dummy_data()
        print("Dummy data inserted.")



    tracker.close()

if __name__ == "__main__":
    main()
