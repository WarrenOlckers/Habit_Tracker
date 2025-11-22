import os
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

def test_longest_streak_all(tracker):
    tracker.add_habit(Habit("A", "Daily"))
    tracker.add_habit(Habit("B", "Daily"))
    ids = [h["id"] for h in tracker.list_all_habits()]

    # Habit A: 2-day streak
    for i in range(2):
        d = date.today().replace(day=date.today().day - i - 1)
        tracker.cursor.execute("INSERT INTO habit_completions (habit_id, completed_on) VALUES (%s, %s)", (ids[0], d))
        
    # Habit B: 4-day streak
    for i in range(4):
        d = date.today().replace(day=date.today().day - i - 1)
        tracker.cursor.execute("INSERT INTO habit_completions (habit_id, completed_on) VALUES (%s, %s)", (ids[1], d))
    tracker.conn.commit()
    result = tracker.longest_streak_all()
    assert result[0] == ids[1]
    assert result[2] == 4