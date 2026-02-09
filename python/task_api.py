from flask import Blueprint, request, jsonify
from datetime import datetime
from task_database import get_task_connection

task_bp = Blueprint("task_bp", __name__)

# =====================================================
# ADD TASK 🔐
# =====================================================
@task_bp.route("/add-task", methods=["POST"])
def add_task():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    description = data.get("description", "")
    selected_category = data.get("selected_category", "Auto")
    custom_category = data.get("custom_category", "")
    due_date = data.get("due_date")
    reminder_time = data.get("reminder_time")
    reminder_type = data.get("reminder_type")
    priority = int(data.get("priority", 0))
    difficulty = int(data.get("difficulty", 0))
    status = data.get("status", "pending")

    # ---------------- CATEGORY DECISION ----------------
    if custom_category:
        category = custom_category
    elif selected_category != "Auto":
        category = selected_category
    else:
        text = title.lower()
        if any(k in text for k in ["exam", "study", "assignment"]):
            category = "Study"
        elif any(k in text for k in ["buy", "purchase", "shop"]):
            category = "Shopping"
        elif any(k in text for k in ["meeting", "call"]):
            category = "Work"
        else:
            category = "General"

    conn = get_task_connection()
    cursor = conn.cursor()

    # ---------------- DUPLICATE TASK CHECK (USER-SCOPED) ----------------
    cursor.execute("""
        SELECT id FROM tasks
        WHERE LOWER(title) = LOWER(?)
          AND user_id = ?
    """, (title, user_id))

    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Task already exists"}), 409

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
        INSERT INTO tasks
        (user_id, title, description, category_id, due_date,
         reminder_time, reminder_type, priority, difficulty,
         status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, title, description, category_id, due_date,
        reminder_time, reminder_type, priority, difficulty,
        status, now, now
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# =====================================================
# UPDATE TASK (EDIT PAGE) 🔐
# =====================================================
@task_bp.route("/update-task", methods=["POST"])
def update_task():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_id = data.get("user_id")
    task_id = data.get("id")

    if not user_id or not task_id:
        return jsonify({"error": "Unauthorized"}), 401

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    description = data.get("description", "")
    selected_category = data.get("selected_category", "Auto")
    custom_category = data.get("custom_category", "")
    due_date = data.get("due_date")
    priority = int(data.get("priority", 0))
    difficulty = int(data.get("difficulty", 0))
    status = data.get("status", "pending")

    # ---------------- CATEGORY DECISION ----------------
    if custom_category:
        category = custom_category
    elif selected_category != "Auto":
        category = selected_category
    else:
        text = title.lower()
        if any(k in text for k in ["exam", "study", "assignment"]):
            category = "Study"
        elif any(k in text for k in ["buy", "purchase", "shop"]):
            category = "Shopping"
        elif any(k in text for k in ["meeting", "call"]):
            category = "Work"
        else:
            category = "General"

    conn = get_task_connection()
    cursor = conn.cursor()

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
            title = ?,
            description = ?,
            category_id = ?,
            due_date = ?,
            priority = ?,
            difficulty = ?,
            status = ?,
            updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (
        title,
        description,
        category_id,
        due_date,
        priority,
        difficulty,
        status,
        now,
        task_id,
        user_id
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# =====================================================
# LIST TASKS 🔐
# =====================================================
@task_bp.route("/tasks", methods=["GET"])
def list_tasks():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_task_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            tasks.id,
            tasks.title,
            tasks.status,
            tasks.priority,
            tasks.difficulty,
            tasks.due_date,
            task_categories.name
        FROM tasks
        LEFT JOIN task_categories
            ON tasks.category_id = task_categories.id
        WHERE tasks.user_id = ?
        ORDER BY tasks.updated_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "title": r[1],
            "status": r[2],
            "priority": r[3],
            "difficulty": r[4],
            "due_date": r[5],
            "category": r[6]
        }
        for r in rows
    ])

# =====================================================
# LIST TASK CATEGORIES 🔐
# =====================================================
@task_bp.route("/task-categories", methods=["GET"])
def get_task_categories():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_task_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT tc.name
        FROM tasks t
        JOIN task_categories tc ON t.category_id = tc.id
        WHERE t.user_id = ?
        ORDER BY tc.name
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify(["Auto"] + [r[0] for r in rows])

