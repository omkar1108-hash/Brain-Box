import sqlite3
from pathlib import Path

# -------------------------------------------------
# PATHS
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"

TASKS_DB = DB_DIR / "tasks.db"
TASK_SERIES_DB = DB_DIR / "task_series.db"
NOTES_DB = DB_DIR / "notes.db"

ADMIN_ID = 1   # admin user id


# -------------------------------------------------
# ADD COLUMN IF NOT EXISTS
# -------------------------------------------------
def add_user_id_column(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # check if column already exists
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cur.fetchall()]

    if "user_id" not in columns:
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN user_id INTEGER")
        conn.commit()
        print(f"➕ user_id column added to {table_name}")
    else:
        print(f"ℹ️ user_id already exists in {table_name}")

    conn.close()


# -------------------------------------------------
# ASSIGN ADMIN TO OLD DATA
# -------------------------------------------------
def assign_admin(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE {table_name}
        SET user_id = ?
        WHERE user_id IS NULL
    """, (ADMIN_ID,))

    conn.commit()
    conn.close()
    print(f"✅ Existing data assigned to admin in {table_name}")


# -------------------------------------------------
# RUN MIGRATION
# -------------------------------------------------
if __name__ == "__main__":

    # tasks.db
    add_user_id_column(TASKS_DB, "tasks")
    assign_admin(TASKS_DB, "tasks")

    # task_series.db
    add_user_id_column(TASK_SERIES_DB, "task_series")
    assign_admin(TASK_SERIES_DB, "task_series")

    add_user_id_column(TASK_SERIES_DB, "task_series_items")
    assign_admin(TASK_SERIES_DB, "task_series_items")

    # notes.db
    add_user_id_column(NOTES_DB, "notes")
    assign_admin(NOTES_DB, "notes")

    print("\n🎉 Migration completed successfully")
