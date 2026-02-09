import sqlite3

def get_task_series_connection():
    return sqlite3.connect("../database/task_series.db")
