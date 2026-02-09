import sqlite3
from pathlib import Path

# Adjust path if needed
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "tasks.db"

def add_reminder_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            ALTER TABLE tasks
            ADD COLUMN reminder_sent INTEGER DEFAULT 0
        """)
        conn.commit()
        print("✅ Column 'reminder_sent' added successfully")

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️ Column 'reminder_sent' already exists")
        else:
            print("❌ Error:", e)

    finally:
        conn.close()


if __name__ == "__main__":
    add_reminder_column()
