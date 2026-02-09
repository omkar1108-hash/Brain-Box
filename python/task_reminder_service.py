from datetime import datetime, timedelta
from task_database import get_task_connection
import sqlite3
from email_utils import send_email
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
USER_DB = BASE_DIR / "database" / "user_data.db"


def check_and_send_task_reminders():
    now = datetime.now()
    reminder_window = now + timedelta(hours=24)   # due in next 24 hrs

    conn = get_task_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.id,
            t.title,
            t.due_date,
            t.user_id
        FROM tasks t
        WHERE t.due_date IS NOT NULL
          AND t.reminder_sent = 0
          AND t.status != 'completed'
    """)

    tasks = cursor.fetchall()

    for task_id, title, due_date, user_id in tasks:
        due_dt = datetime.fromisoformat(due_date)

        if now <= due_dt <= reminder_window:
            # fetch user email
            uconn = sqlite3.connect(USER_DB)
            ucur = uconn.cursor()
            ucur.execute(
                "SELECT email FROM users WHERE id = ?",
                (user_id,)
            )
            row = ucur.fetchone()
            uconn.close()

            if not row:
                continue

            email = row[0]

            send_email(
                email,
                "⏰ Task Due Reminder",
                f"Your task '{title}' is due on {due_dt.strftime('%Y-%m-%d %H:%M')}."
            )

            # mark reminder sent
            cursor.execute(
                "UPDATE tasks SET reminder_sent = 1 WHERE id = ?",
                (task_id,)
            )

    conn.commit()
    conn.close()
