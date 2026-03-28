import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "task_series.db")

def get_task_series_connection():
    return sqlite3.connect(DB_PATH)
