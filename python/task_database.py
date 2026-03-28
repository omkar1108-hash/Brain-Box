import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "tasks.db")

def get_task_connection():
    return sqlite3.connect(DB_PATH)
