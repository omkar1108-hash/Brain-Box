import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "task_series.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ---------- SERIES CATEGORIES ----------
cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_series_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
""")

# ---------- TASK SERIES ----------
cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_series (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT UNIQUE NOT NULL,
        category_id INTEGER,
        status TEXT DEFAULT 'pending',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (category_id)
            REFERENCES task_series_categories(id)
    )
""")

# ---------- TASK SERIES ITEMS ----------
cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_series_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        series_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        priority INTEGER DEFAULT 0,
        difficulty INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (series_id)
            REFERENCES task_series(id)
            ON DELETE CASCADE
    )
""")

conn.commit()
conn.close()

print("✅ NEW task_series.db created successfully")
