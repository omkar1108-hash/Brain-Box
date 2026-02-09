import sqlite3

conn = sqlite3.connect("../database/notes.db")
cursor = conn.cursor()

# Add password column safely
try:
    cursor.execute("ALTER TABLE notes ADD COLUMN password TEXT")
    print("password column added")
except sqlite3.OperationalError:
    print("password column already exists")

conn.commit()
conn.close()
