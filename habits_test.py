import os

# Set test DB environment variables BEFORE importing HabitTracker
os.environ["PGHOST"] = "localhost"
os.environ["PGPORT"] = "5432"
os.environ["PGUSER"] = "tutor"
os.environ["PGPASSWORD"] = "warren"
os.environ["PGDATABASE"] = "habitdb_test"



import pytest
import psycopg2
from datetime import date
from Habit_Tracker2 import Habit, HabitTracker

# Use a test database (make sure it's created and isolated)
TEST_DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "user": "tutor",
    "password": "warren",
    "dbname": "habitdb_test"
}

@pytest.fixture
def tracker():
    # Override environment variables for test DB
    for key, value in TEST_DB_CONFIG.items():
        os.environ[f"PG{key.upper()}"] = value
    ht = HabitTracker()
    ht.cursor.execute("DELETE FROM habit_completions;")
    ht.cursor.execute("DELETE FROM habits;")
    ht.conn.commit()
    yield ht
    ht.close()
#> This fixture sets up a clean HabitTracker instance using a test database and clears tables before each test.


## 🧪 Test 1: Adding a habit

#python
def test_add_habit(tracker):
    habit = Habit("Test Habit", "Daily")
    tracker.add_habit(habit)
    habits = tracker.list_all_habits()
    assert len(habits) == 1
    assert habits[0]["name"] == "Test Habit"
    assert habits[0]["frequency"] == "Daily"

def test_list_all_habits(tracker):
    # Add multiple habits
    tracker.add_habit(Habit("Read", "Daily"))
    tracker.add_habit(Habit("Workout", "Weekly"))
    tracker.add_habit(Habit("Meditate", "Daily"))

    habits = tracker.list_all_habits()

    # Check that all habits are returned
    assert len(habits) == 3

    # Extract names and frequencies for easy comparison
    names = [h["name"] for h in habits]
    freqs = [h["frequency"] for h in habits]

    assert "Read" in names
    assert "Workout" in names
    assert "Meditate" in names

    assert freqs.count("Daily") == 2
    assert freqs.count("Weekly") == 1

def test_mark_completed(tracker):
    habit = Habit("Water", "Daily")
    tracker.add_habit(habit)
    habit_id = tracker.list_all_habits()[0]["id"]
    tracker.mark_completed(habit_id)
    tracker.cursor.execute("SELECT * FROM habit_completions WHERE habit_id = %s", (habit_id,))
    completions = tracker.cursor.fetchall()
    assert len(completions) == 1
    assert completions[0]["completed_on"] == date.today()

def test_longest_streak_for_daily(tracker):
    habit = Habit("Meditate", "Daily")
    tracker.add_habit(habit)
    habit_id = tracker.list_all_habits()[0]["id"]

    # Insert 5 consecutive days
    for i in range(5):
        d = date.today().replace(day=date.today().day - i - 1)
        tracker.cursor.execute(
            "INSERT INTO habit_completions (habit_id, completed_on) VALUES (%s, %s)",
            (habit_id, d)
        )
    tracker.conn.commit()
    streak = tracker.longest_streak_for_habit(habit_id)
    assert streak == 5

def test_longest_streak_for_weekly(tracker):
    habit = Habit("Gym", "Weekly")
    tracker.add_habit(habit)
    habit_id = tracker.list_all_habits()[0]["id"]

    # Insert 3 consecutive Mondays
    for i in range(3):
        wk = date.today().replace(day=date.today().day - i * 7 - 1)
        tracker.cursor.execute(
            "INSERT INTO habit_completions (habit_id, completed_on) VALUES (%s, %s)",
            (habit_id, wk)
        )
    tracker.conn.commit()
    streak = tracker.longest_streak_for_habit(habit_id)
    assert streak == 3

from datetime import date, timedelta

def test_longest_streak_all_mixed_frequencies(tracker):
    # Add one daily and one weekly habit
    tracker.add_habit(Habit("Journal", "Daily"))
    tracker.add_habit(Habit("Yoga Class", "Weekly"))

    habits = tracker.list_all_habits()
    habit_ids = {h["name"]: h["id"] for h in habits}

    # Daily habit: 4-day streak ending yesterday
    for i in range(4):
        d = date.today() - timedelta(days=i + 1)
        tracker.cursor.execute(
            "INSERT INTO habit_completions (habit_id, completed_on) VALUES (%s, %s)",
            (habit_ids["Journal"], d)
        )

    # Weekly habit: 5-week streak ending last Monday
    last_monday = date.today() - timedelta(days=date.today().weekday() + 7)
    for i in range(5):
        week_date = last_monday - timedelta(weeks=i)
        tracker.cursor.execute(
            "INSERT INTO habit_completions (habit_id, completed_on) VALUES (%s, %s)",
            (habit_ids["Yoga Class"], week_date)
        )

    tracker.conn.commit()

    result = tracker.longest_streak_all()

    assert result is not None
    assert result[1] == "Yoga Class"
    assert result[2] == 5
