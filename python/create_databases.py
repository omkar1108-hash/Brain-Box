import sqlite3
from pathlib import Path

# -------------------------------------------------
# BASE PATH
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(exist_ok=True)

# -------------------------------------------------
# USER DATABASE
# -------------------------------------------------
def create_user_db():
    conn = sqlite3.connect(DB_DIR / "user_data.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print("✅ user_data.db created")


# -------------------------------------------------
# TASKS DATABASE
# -------------------------------------------------
def create_tasks_db():
    conn = sqlite3.connect(DB_DIR / "tasks.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print("✅ tasks.db updated")


# -------------------------------------------------
# TASK SERIES DATABASE
# -------------------------------------------------
def create_task_series_db():
    conn = sqlite3.connect(DB_DIR / "task_series.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS task_series (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS task_series_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        series_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        status TEXT DEFAULT 'pending'
    );
    """)

    conn.commit()
    conn.close()
    print("✅ task_series.db updated")


# -------------------------------------------------
# NOTES DATABASE
# -------------------------------------------------
def create_notes_db():
    conn = sqlite3.connect(DB_DIR / "notes.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        content TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print("✅ notes.db updated")


# -------------------------------------------------
# RUN ALL
# -------------------------------------------------
if __name__ == "__main__":
    create_user_db()
    create_tasks_db()
    create_task_series_db()
    create_notes_db()
    print("\n🎉 All databases created successfully")
