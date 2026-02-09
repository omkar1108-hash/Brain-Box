from flask import Blueprint, request, jsonify
from datetime import datetime
from task_database import get_task_connection
from task_series_database import get_task_series_connection

task_action_bp = Blueprint("task_action_bp", __name__)
print("🔥 task_action_api.py LOADED")


# =====================================================
# GET SINGLE TASK (EDIT PAGE) 🔐
# =====================================================
@task_action_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_task_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.id,
            t.title,
            t.description,
            t.due_date,
            t.reminder_time,
            t.reminder_type,
            t.priority,
            t.difficulty,
            t.status,
            t.created_at,
            c.name
        FROM tasks t
        LEFT JOIN task_categories c
            ON t.category_id = c.id
        WHERE t.id = ? AND t.user_id = ?
    """, (task_id, user_id))

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
        "category": row[10]
    })


# =====================================================
# UPDATE TASK (EDIT PAGE) 🔐
# =====================================================
@task_action_bp.route("/update-task", methods=["POST"])
def update_task():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_id = data.get("user_id")
    task_id = data.get("id")

    if not user_id or not task_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_task_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET
            title = ?,
            description = ?,
            due_date = ?,
            priority = ?,
            difficulty = ?,
            status = ?,
            updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (
        data.get("title"),
        data.get("description"),
        data.get("due_date"),
        data.get("priority", 0),
        data.get("difficulty", 0),
        data.get("status", "pending"),
        datetime.now().isoformat(),
        task_id,
        user_id
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# =====================================================
# DELETE TASK (EDIT PAGE) 🔐
# =====================================================
@task_action_bp.route("/task/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_task_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )

    conn.commit()
    conn.close()
    return jsonify({"success": True})


# =====================================================
# UPDATE TASK STATUS (DASHBOARD CHECKBOX) 🔐
# =====================================================
@task_action_bp.route("/update-task-status", methods=["POST"])
def update_task_status():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    task_id = data.get("id")

    if not user_id or not task_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_task_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET status = ?
        WHERE id = ? AND user_id = ?
    """, (
        data.get("status"),
        task_id,
        user_id
    ))

    conn.commit()
    conn.close()
    return jsonify({"success": True})


# =====================================================
# DELETE TASK FROM DASHBOARD 🔐
# =====================================================
@task_action_bp.route("/delete-task", methods=["POST"])
def delete_task_dashboard():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    task_id = data.get("id")

    if not user_id or not task_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_task_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )

    conn.commit()
    conn.close()
    return jsonify({"success": True})


# =====================================================
# DELETE TASK SERIES 🔐
# =====================================================
@task_action_bp.route("/delete-task-series", methods=["POST"])
def delete_task_series():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    series_id = data.get("id")

    if not user_id or not series_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_task_series_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM task_series WHERE id = ? AND user_id = ?",
        (series_id, user_id)
    )

    conn.commit()
    conn.close()
    return jsonify({"success": True})
