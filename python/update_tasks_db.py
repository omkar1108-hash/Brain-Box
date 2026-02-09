import sqlite3

conn = sqlite3.connect("../database/tasks.db")
cursor = conn.cursor()

def add_column(column_sql):
    try:
        cursor.execute(column_sql)
        print("Column added:", column_sql)
    except sqlite3.OperationalError:
        print("Column already exists")

# Add priority (0–10)
add_column(
    "ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 0"
)

# Add difficulty (0–10)
add_column(
    "ALTER TABLE tasks ADD COLUMN difficulty INTEGER DEFAULT 0"
)

conn.commit()
conn.close()

print("✅ tasks.db updated successfully")
