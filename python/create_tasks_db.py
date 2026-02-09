import sqlite3
from pathlib import Path

db_path = Path("../database/tasks.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ---------------- TASK CATEGORIES ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS task_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
)
""")

# ---------------- SINGLE TASKS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category_id INTEGER,
    due_date TEXT,
    reminder_time TEXT,
    reminder_type TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES task_categories(id)
)
""")

# ---------------- TASK SERIES ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS task_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES task_categories(id)
)
""")

# ---------------- SERIES TASK ITEMS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS task_series_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER,
    title TEXT NOT NULL,
    due_date TEXT,
    status TEXT DEFAULT 'pending',
    order_index INTEGER,
    FOREIGN KEY (series_id) REFERENCES task_series(id)
)
""")

conn.commit()
conn.close()

print("✅ tasks.db created successfully")
