from flask import Blueprint, request, jsonify
from task_database import get_task_connection
from task_series_database import get_task_series_connection

task_dashboard_bp = Blueprint("task_dashboard_bp", __name__)

# =====================================================
# GET TASK CATEGORIES (GLOBAL – OK)
# =====================================================
@task_dashboard_bp.route("/task-categories", methods=["GET"])
def get_task_categories():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_task_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT c.name
        FROM tasks t
        JOIN task_categories c ON t.category_id = c.id
        WHERE t.user_id = ?
        ORDER BY c.name
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify(["All"] + [r[0] for r in rows])

# =====================================================
# LIST TASKS + TASK SERIES (DASHBOARD) 🔐
# =====================================================
@task_dashboard_bp.route("/tasks-dashboard", methods=["GET"])
def list_tasks_dashboard():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    category = request.args.get("category", "All")
    status = request.args.get("status", "all")

    result = []

    # =====================================================
    # REGULAR TASKS
    # =====================================================
    conn = get_task_connection()
    cursor = conn.cursor()

    task_query = """
        SELECT
            t.id,
            t.title,
            t.status,
            t.priority,
            t.difficulty,
            t.due_date,
            c.name
        FROM tasks t
        LEFT JOIN task_categories c
            ON t.category_id = c.id
        WHERE t.user_id = ?
    """
    task_params = [user_id]

    if category != "All":
        task_query += " AND c.name = ?"
        task_params.append(category)

    if status != "all":
        task_query += " AND t.status = ?"
        task_params.append(status)

    cursor.execute(task_query, task_params)

    for r in cursor.fetchall():
        result.append({
            "id": r[0],
            "title": r[1],
            "status": r[2],
            "priority": r[3],
            "difficulty": r[4],
            "due_date": r[5],
            "category": r[6],
            "type": "task"
        })

    conn.close()

    # =====================================================
    # TASK SERIES
    # =====================================================
    conn = get_task_series_connection()
    cursor = conn.cursor()

    series_query = """
        SELECT
            s.id,
            s.title,
            s.status,
            c.name,
            COUNT(si.id) AS total_tasks,
            SUM(CASE WHEN si.status='completed' THEN 1 ELSE 0 END)
        FROM task_series s
        LEFT JOIN task_series_items si
            ON s.id = si.series_id
        LEFT JOIN task_series_categories c
            ON s.category_id = c.id
        WHERE s.user_id = ?
        GROUP BY s.id
    """
    series_params = [user_id]

    if category != "All":
        series_query += " AND c.name = ?"
        series_params.append(category)

    if status != "all":
        series_query += " AND s.status = ?"
        series_params.append(status)

    cursor.execute(series_query, series_params)

    for r in cursor.fetchall():
        total = r[4] or 0
        completed = r[5] or 0
        progress = int((completed / total) * 100) if total else 0

        result.append({
            "id": r[0],
            "title": r[1],
            "status": r[2],
            "priority": None,
            "difficulty": None,
            "due_date": None,
            "category": r[3],
            "type": "series",
            "progress": progress
        })

    conn.close()

    # =====================================================
    # SORT (UNCHANGED)
    # =====================================================
    result.sort(
        key=lambda x: (
            x["priority"] if x["priority"] is not None else -1,
            1 if x["type"] == "series" else 0
        ),
        reverse=True
    )

    return jsonify(result)


# =====================================================
# GET SINGLE TASK (EDIT PAGE) 🔐
# =====================================================
@task_dashboard_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_single_task(task_id):
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
            t.status,
            t.priority,
            t.difficulty,
            t.due_date,
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
        "status": row[3],
        "priority": row[4],
        "difficulty": row[5],
        "due_date": row[6],
        "category": row[7] or "Auto"
    })


# =====================================================
# GET SINGLE TASK SERIES (EDIT PAGE) 🔐
# =====================================================
@task_dashboard_bp.route("/task-series/<int:series_id>", methods=["GET"])
def get_single_task_series(series_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_task_series_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.id,
            s.title,
            s.status,
            c.name
        FROM task_series s
        LEFT JOIN task_series_categories c
            ON s.category_id = c.id
        WHERE s.id = ? AND s.user_id = ?
    """, (series_id, user_id))

    series = cursor.fetchone()
    if not series:
        conn.close()
        return jsonify({"error": "Series not found"}), 404

    cursor.execute("""
        SELECT
            id,
            title,
            description,
            due_date,
            priority,
            difficulty,
            status
        FROM task_series_items
        WHERE series_id = ?
        ORDER BY id
    """, (series_id,))

    tasks = cursor.fetchall()
    conn.close()

    return jsonify({
        "id": series[0],
        "title": series[1],
        "status": series[2],
        "category": series[3] or "Auto",
        "tasks": [
            {
                "id": t[0],
                "title": t[1],
                "description": t[2],
                "due_date": t[3],
                "priority": t[4],
                "difficulty": t[5],
                "status": t[6]
            } for t in tasks
        ]
    })
