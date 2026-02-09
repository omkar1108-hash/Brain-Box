import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FOLDER = os.path.join(BASE_DIR, "database")

USER_DB = os.path.join(DB_FOLDER, "user_data.db")
GROUP_TASK_DB = os.path.join(DB_FOLDER, "group_tasks.db")


def create_user_data_tables():
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()

    # Group Task Series (Container)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS group_task_series (
        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        creator_id INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # Group Task Members
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS group_task_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        role TEXT CHECK(role IN ('creator', 'member')) NOT NULL,
        added_at TEXT NOT NULL,
        UNIQUE(group_id, user_id)
    )
    """)

    conn.commit()
    conn.close()


def create_group_task_db():
    conn = sqlite3.connect(GROUP_TASK_DB)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS group_tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        assigned_to INTEGER NOT NULL,
        status TEXT CHECK(status IN ('pending', 'completed')) DEFAULT 'pending',
        created_at TEXT NOT NULL,
        completed_at TEXT
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    os.makedirs(DB_FOLDER, exist_ok=True)

    create_user_data_tables()
    create_group_task_db()

    print("✅ Group Task databases initialized successfully.")
