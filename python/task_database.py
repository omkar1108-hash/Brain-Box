import sqlite3

def get_task_connection():
    return sqlite3.connect("../database/tasks.db")
