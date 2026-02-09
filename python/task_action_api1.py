from flask import Blueprint, request, jsonify
from datetime import datetime
from task_database import get_task_connection

task_action_bp = Blueprint("task_action_bp", __name__)

# =====================================================
# GET SINGLE TASK
# =====================================================
@task_action_bp.route("/task/<int:task_id>", methods=["GET"])
def get_task(task_id):
    conn = get_task_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            tasks.id,
            tasks.title,
            tasks.description,
            tasks.due_date,
            tasks.reminder_time,
            tasks.reminder_type,
            tasks.priority,
            tasks.difficulty,
            tasks.status,
            tasks.created_at,
            tasks.updated_at,
            task_categories.name
        FROM tasks
        LEFT JOIN task_categories
        ON tasks.category_id = task_categories.id
        WHERE tasks.id=?
    """, (task_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "due_date": row[3],
        "reminder_time": row[4],
        "reminder_type": row[5],
        "priority": row[6],
        "difficulty": row[7],
        "status": row[8],
        "created_at": row[9],
        "updated_at": row[10],
        "category": row[11] or ""
    })


# =====================================================
# UPDATE TASK
# =====================================================
@task_action_bp.route("/task/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    description = data.get("description", "")
    custom_category = data.get("custom_category", "")
    due_date = data.get("due_date")
    reminder_time = data.get("reminder_time")
    reminder_type = data.get("reminder_type")
    priority = int(data.get("priority", 0))
    difficulty = int(data.get("difficulty", 0))
    status = data.get("status", "pending")

    # -------- CATEGORY DECISION --------
    category = custom_category if custom_category else "General"

    conn = get_task_connection()
    cursor = conn.cursor()

    # ensure category exists
    cursor.execute(
        "INSERT OR IGNORE INTO task_categories(name) VALUES (?)",
        (category,)
    )
    cursor.execute(
        "SELECT id FROM task_categories WHERE name=?",
        (category,)
    )
    category_id = cursor.fetchone()[0]

    now = datetime.now().isoformat()

    cursor.execute("""
        UPDATE tasks
        SET
            title=?,
            description=?,
            category_id=?,
            due_date=?,
            reminder_time=?,
            reminder_type=?,
            priority=?,
            difficulty=?,
            status=?,
            updated_at=?
        WHERE id=?
    """, (
        title, description, category_id, due_date,
        reminder_time, reminder_type, priority, difficulty,
        status, now, task_id
    ))

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# =====================================================
# DELETE TASK
# =====================================================
@task_action_bp.route("/task/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_task_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"success": True})
