import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "tasks.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    ALTER TABLE task_series
    ADD COLUMN status TEXT DEFAULT 'pending'
""")

conn.commit()
conn.close()

print("✅ status column added to task_series")
