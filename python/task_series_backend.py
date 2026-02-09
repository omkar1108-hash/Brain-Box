from flask import Blueprint, request, jsonify
import sqlite3
from datetime import datetime
from pathlib import Path
from task_series_database import get_task_series_connection

task_series_bp = Blueprint("task_series_bp", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "task_series.db"


# =====================================================
# CATEGORY RESOLVER (UNCHANGED)
# =====================================================
def resolve_task_series_category(title, selected_category, custom_category):
    if custom_category:
        return custom_category
    if selected_category and selected_category != "Auto":
        return selected_category

    text = title.lower()
    if any(k in text for k in ["exam", "study", "assignment"]):
        return "Study"
    if any(k in text for k in ["buy", "purchase", "shop"]):
        return "Shopping"
    if any(k in text for k in ["project", "meeting", "call"]):
        return "Work"

    return "General"


# =====================================================
# ADD TASK SERIES 🔐
# =====================================================
def add_task_series():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Series title required"}), 400

    tasks = data.get("tasks", [])
    if not tasks or not isinstance(tasks, list):
        return jsonify({"error": "At least one task required"}), 400

    selected_category = data.get("selected_category", "Auto")
    custom_category = data.get("custom_category", "")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # USER-SCOPED DUPLICATE CHECK
    cursor.execute("""
        SELECT id FROM task_series
        WHERE title = ? AND user_id = ?
    """, (title, user_id))

    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Task series with this title already exists"}), 409

    category_name = resolve_task_series_category(
        title, selected_category, custom_category
    )

    cursor.execute(
        "INSERT OR IGNORE INTO task_series_categories(name) VALUES (?)",
        (category_name,)
    )
    cursor.execute(
        "SELECT id FROM task_series_categories WHERE name=?",
        (category_name,)
    )
    category_id = cursor.fetchone()[0]

    now = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO task_series
        (user_id, title, category_id, status, created_at, updated_at)
        VALUES (?, ?, ?, 'pending', ?, ?)
    """, (user_id, title, category_id, now, now))

    series_id = cursor.lastrowid

    for t in tasks:
        task_title = t.get("title", "").strip()
        if not task_title:
            continue

        cursor.execute("""
            INSERT INTO task_series_items
            (series_id, user_id, title, description, due_date,
             priority, difficulty, status,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            series_id,
            user_id,
            task_title,
            t.get("description"),
            t.get("due_date"),
            int(t.get("priority", 0)),
            int(t.get("difficulty", 0)),
            t.get("status", "pending"),
            now,
            now
        ))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "series_id": series_id})


# =====================================================
# LIST TASK SERIES 🔐
# =====================================================
def list_task_series():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ts.id,
            ts.title,
            tc.name,
            COUNT(ti.id),
            SUM(CASE WHEN ti.status='completed' THEN 1 ELSE 0 END)
        FROM task_series ts
        LEFT JOIN task_series_items ti ON ts.id = ti.series_id
        LEFT JOIN task_series_categories tc ON ts.category_id = tc.id
        WHERE ts.user_id = ?
        GROUP BY ts.id
        ORDER BY ts.updated_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        total = r[3] or 0
        completed = r[4] or 0
        progress = int((completed / total) * 100) if total else 0

        result.append({
            "id": r[0],
            "title": r[1],
            "category": r[2],
            "total_tasks": total,
            "completed_tasks": completed,
            "progress": progress
        })

    return jsonify(result)


# =====================================================
# UPDATE TASK SERIES 🔐
# =====================================================
@task_series_bp.route("/update-task-series", methods=["POST"])
def update_task_series():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_id = data.get("user_id")
    series_id = data.get("id")
    title = data.get("title", "").strip()
    tasks = data.get("tasks", [])

    if not user_id or not series_id or not title:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_task_series_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    # UPDATE SERIES (OWNERSHIP ENFORCED)
    cursor.execute("""
        UPDATE task_series
        SET title=?, updated_at=?
        WHERE id=? AND user_id=?
    """, (title, now, series_id, user_id))

    # DELETE OLD ITEMS (USER-SCOPED)
    cursor.execute("""
        DELETE FROM task_series_items
        WHERE series_id=? AND user_id=?
    """, (series_id, user_id))

    # INSERT UPDATED ITEMS
    for t in tasks:
        task_title = t.get("title", "").strip()
        if not task_title:
            continue

        cursor.execute("""
            INSERT INTO task_series_items
            (series_id, user_id, title, description, due_date,
             priority, difficulty, status,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            series_id,
            user_id,
            task_title,
            t.get("description"),
            t.get("due_date"),
            int(t.get("priority", 0)),
            int(t.get("difficulty", 0)),
            t.get("status", "pending"),
            now,
            now
        ))

    # AUTO UPDATE SERIES STATUS
    cursor.execute("""
        SELECT
            COUNT(*),
            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END)
        FROM task_series_items
        WHERE series_id=? AND user_id=?
    """, (series_id, user_id))

    total, completed = cursor.fetchone()
    series_status = "completed" if total and total == completed else "pending"

    cursor.execute("""
        UPDATE task_series
        SET status=?, updated_at=?
        WHERE id=? AND user_id=?
    """, (series_status, now, series_id, user_id))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# =====================================================
# LIST TASK SERIES CATEGORIES 🔐
# =====================================================
@task_series_bp.route("/task-series-categories", methods=["GET"])
def get_task_series_categories():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT tc.name
        FROM task_series ts
        JOIN task_series_categories tc ON ts.category_id = tc.id
        WHERE ts.user_id = ?
        ORDER BY tc.name
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify(["Auto"] + [r[0] for r in rows])
