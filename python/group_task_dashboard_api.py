from flask import Blueprint, request, jsonify
import sqlite3
from pathlib import Path
from datetime import datetime
group_task_dashboard_bp = Blueprint(
    "group_task_dashboard_bp", __name__
)

BASE_DIR = Path(__file__).resolve().parent.parent
USER_DB = BASE_DIR / "database" / "user_data.db"
GROUP_DB = BASE_DIR / "database" / "group_tasks.db"


@group_task_dashboard_bp.route(
    "/group-tasks-dashboard", methods=["GET"]
)
def list_group_tasks_dashboard():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    uconn = sqlite3.connect(USER_DB)
    ucur = uconn.cursor()

    # groups where user is member
    ucur.execute("""
        SELECT
            g.group_id,
            g.title,
            COUNT(m.user_id)
        FROM group_task_series g
        JOIN group_task_members m
            ON g.group_id = m.group_id
        WHERE g.group_id IN (
            SELECT group_id
            FROM group_task_members
            WHERE user_id = ?
        )
        GROUP BY g.group_id
        ORDER BY g.created_at DESC
    """, (user_id,))

    groups = ucur.fetchall()
    uconn.close()

    gconn = sqlite3.connect(GROUP_DB)
    gcur = gconn.cursor()

    result = []

    for group_id, title, member_count in groups:
        gcur.execute("""
            SELECT
                COUNT(*),
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END)
            FROM group_tasks
            WHERE group_id = ?
        """, (group_id,))

        total, completed = gcur.fetchone()
        total = total or 0
        completed = completed or 0
        progress = int((completed / total) * 100) if total else 0

        result.append({
            "group_id": group_id,
            "title": title,
            "member_count": member_count,
            "progress": progress
        })

    gconn.close()
    return jsonify(result)

@group_task_dashboard_bp.route("/create-group-task", methods=["POST"])
def create_group_task():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_id = data.get("user_id")
    title = data.get("title")
    members = data.get("members", [])
    tasks = data.get("tasks", [])

    if not user_id or not title or not tasks:
        return jsonify({"error": "Invalid data"}), 400

    now = datetime.now().isoformat()

    # =====================================================
    # 1️⃣ user_data.db → create group + members
    # =====================================================
    uconn = sqlite3.connect(USER_DB)
    ucur = uconn.cursor()

    ucur.execute("""
        INSERT INTO group_task_series
        (title, creator_id, created_at)
        VALUES (?, ?, ?)
    """, (title, user_id, now))

    group_id = ucur.lastrowid

    # creator
    ucur.execute("""
        INSERT INTO group_task_members
        (group_id, user_id, role, added_at)
        VALUES (?, ?, 'creator', ?)
    """, (group_id, user_id, now))

    # members
    for m in members:
        ucur.execute(
            "SELECT id FROM users WHERE username=? OR email=?",
            (m, m)
        )
        r = ucur.fetchone()
        if r:
            ucur.execute("""
                INSERT OR IGNORE INTO group_task_members
                (group_id, user_id, role, added_at)
                VALUES (?, ?, 'member', ?)
            """, (group_id, r[0], now))

    uconn.commit()
    uconn.close()

    # =====================================================
    # 2️⃣ group_tasks.db → insert tasks
    # =====================================================
    gconn = sqlite3.connect(GROUP_DB)
    gcur = gconn.cursor()

    # 🔑 IMPORTANT: use user_data.db again to resolve users
    uconn = sqlite3.connect(USER_DB)
    ucur = uconn.cursor()

    for t in tasks:
        assigned_raw = t.get("assigned_to")

        # default: ALL
        assigned_to = 0

        # creator
        if str(assigned_raw) == str(user_id):
            assigned_to = int(user_id)

        # username / email
        elif assigned_raw != "ALL":
            ucur.execute(
                "SELECT id FROM users WHERE username=? OR email=?",
                (assigned_raw, assigned_raw)
            )
            r = ucur.fetchone()
            if not r:
                continue
            assigned_to = r[0]

        gcur.execute("""
            INSERT INTO group_tasks
            (group_id, title, description,
            assigned_to, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
        """, (
            group_id,
            t.get("title"),
            t.get("description"),
            assigned_to,   # ALWAYS NOT NULL
            now
        ))


    gconn.commit()
    gconn.close()
    uconn.close()

    return jsonify({
        "success": True,
        "group_id": group_id
    })


@group_task_dashboard_bp.route("/group-task/<int:group_id>", methods=["GET"])
def get_group_task(group_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # ---------------- membership check ----------------
    conn = sqlite3.connect(USER_DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT role
        FROM group_task_members
        WHERE group_id=? AND user_id=?
    """, (group_id, user_id))

    role_row = cur.fetchone()
    if not role_row:
        conn.close()
        return jsonify({"error": "Forbidden"}), 403

    my_role = role_row[0]

    # ---------------- group info ----------------
    cur.execute("""
        SELECT title, creator_id
        FROM group_task_series
        WHERE group_id=?
    """, (group_id,))
    title, creator_id = cur.fetchone()

    # ---------------- members ----------------
    cur.execute("""
        SELECT u.id, u.username, m.role
        FROM group_task_members m
        JOIN users u ON u.id = m.user_id
        WHERE m.group_id=?
    """, (group_id,))
    members = cur.fetchall()
    conn.close()

    # ---------------- tasks (NO FILTERING) ----------------
    gconn = sqlite3.connect(GROUP_DB)
    gcur = gconn.cursor()
    gcur.execute("""
        SELECT
            task_id,
            title,
            description,
            assigned_to,
            status
        FROM group_tasks
        WHERE group_id=?
        ORDER BY task_id
    """, (group_id,))
    tasks = gcur.fetchall()
    gconn.close()

    return jsonify({
        "group_id": group_id,
        "title": title,
        "creator_id": creator_id,
        "my_role": my_role,
        "members": [
            {"id": m[0], "name": m[1], "role": m[2]}
            for m in members
        ],
        "tasks": [
            {
                "task_id": t[0],
                "title": t[1],
                "description": t[2],
                "assigned_to": t[3],   # 0 = ALL
                "status": t[4]
            }
            for t in tasks
        ]
    })



@group_task_dashboard_bp.route("/group-task-add-task", methods=["POST"])
def group_task_add_task():
    data = request.get_json(silent=True)

    user_id = data.get("user_id")
    group_id = data.get("group_id")
    title = data.get("title")
    description = data.get("description")
    assigned_raw = data.get("assigned_to", "ALL")

    if not user_id or not group_id or not title:
        return jsonify({"error": "Invalid data"}), 400

    # ---------------- membership check ----------------
    conn = sqlite3.connect(USER_DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT 1
        FROM group_task_members
        WHERE group_id=? AND user_id=?
    """, (group_id, user_id))

    if not cur.fetchone():
        conn.close()
        return jsonify({"error": "Forbidden"}), 403

    # ---------------- resolve assigned_to ----------------
    assigned_to = 0   # 0 = ALL

    if assigned_raw != "ALL":
        cur.execute(
            "SELECT id FROM users WHERE id=? OR username=? OR email=?",
            (assigned_raw, assigned_raw, assigned_raw)
        )
        r = cur.fetchone()
        if not r:
            conn.close()
            return jsonify({"error": "User not found"}), 404
        assigned_to = r[0]

    conn.close()

    # ---------------- insert task ----------------
    gconn = sqlite3.connect(GROUP_DB)
    gcur = gconn.cursor()
    gcur.execute("""
        INSERT INTO group_tasks
        (group_id, title, description,
         assigned_to, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (
        group_id,
        title,
        description,
        assigned_to,   # ALWAYS INTEGER (0 or user_id)
        datetime.now().isoformat()
    ))

    gconn.commit()
    gconn.close()

    return jsonify({"success": True})


@group_task_dashboard_bp.route("/group-task-delete-task", methods=["POST"])
def group_task_delete_task():
    data = request.get_json()
    user_id = data["user_id"]
    task_id = data["task_id"]

    # verify creator
    conn = sqlite3.connect(USER_DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT g.creator_id
        FROM group_task_series g
        JOIN group_tasks t ON g.group_id = t.group_id
        WHERE t.task_id=?
    """, (task_id,))
    creator_id = cur.fetchone()[0]
    conn.close()

    if str(creator_id) != str(user_id):
        return jsonify({"error": "Only creator can delete"}), 403

    gconn = sqlite3.connect(GROUP_DB)
    gcur = gconn.cursor()
    gcur.execute("DELETE FROM group_tasks WHERE task_id=?", (task_id,))
    gconn.commit()
    gconn.close()

    return jsonify({"success": True})


@group_task_dashboard_bp.route("/group-task-toggle-status", methods=["POST"])
def toggle_group_task_status():
    data = request.get_json(silent=True)
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    new_status = data.get("status")

    if not user_id or not task_id or new_status not in ("pending", "completed"):
        return jsonify({"error": "Invalid data"}), 400

    # -------------------------------------------------
    # get task + group info
    # -------------------------------------------------
    gconn = sqlite3.connect(GROUP_DB)
    gcur = gconn.cursor()

    gcur.execute("""
        SELECT group_id, assigned_to
        FROM group_tasks
        WHERE task_id=?
    """, (task_id,))
    row = gcur.fetchone()

    if not row:
        return jsonify({"error": "Task not found"}), 404

    group_id, assigned_to = row

    # -------------------------------------------------
    # check creator
    # -------------------------------------------------
    uconn = sqlite3.connect(USER_DB)
    ucur = uconn.cursor()

    ucur.execute("""
        SELECT creator_id
        FROM group_task_series
        WHERE group_id=?
    """, (group_id,))
    creator_id = ucur.fetchone()[0]

    # -------------------------------------------------
    # permission logic
    # -------------------------------------------------
    allowed = False

    if str(user_id) == str(creator_id):
        allowed = True
    elif assigned_to == 0:
        allowed = False   # ALL = visible, but only creator can complete

    elif str(user_id) == str(assigned_to):
        allowed = True

    if not allowed:
        return jsonify({"error": "Not allowed"}), 403

    # -------------------------------------------------
    # update status
    # -------------------------------------------------
    gcur.execute("""
        UPDATE group_tasks
        SET status=?,
            completed_at=CASE
                WHEN ?='completed' THEN ?
                ELSE NULL
            END
        WHERE task_id=?
    """, (
        new_status,
        new_status,
        datetime.now().isoformat(),
        task_id
    ))

    gconn.commit()
    gconn.close()
    uconn.close()

    return jsonify({"success": True})


@group_task_dashboard_bp.route("/group-task-update-assign", methods=["POST"])
def group_task_update_assign():
    data = request.get_json(silent=True)
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    assigned_raw = data.get("assigned_to")

    if not user_id or not task_id:
        return jsonify({"error": "Invalid data"}), 400

    # -------------------------------------------------
    # get group_id from task
    # -------------------------------------------------
    gconn = sqlite3.connect(GROUP_DB)
    gcur = gconn.cursor()
    gcur.execute(
        "SELECT group_id FROM group_tasks WHERE task_id=?",
        (task_id,)
    )
    row = gcur.fetchone()
    if not row:
        gconn.close()
        return jsonify({"error": "Task not found"}), 404
    group_id = row[0]
    gconn.close()

    # -------------------------------------------------
    # ONLY GROUP CREATOR CAN CHANGE ASSIGNMENT
    # -------------------------------------------------
    uconn = sqlite3.connect(USER_DB)
    ucur = uconn.cursor()

    ucur.execute("""
        SELECT creator_id
        FROM group_task_series
        WHERE group_id=?
    """, (group_id,))
    creator_id = ucur.fetchone()[0]

    if str(user_id) != str(creator_id):
        uconn.close()
        return jsonify({"error": "Only group creator can change assignment"}), 403

    # -------------------------------------------------
    # resolve assigned_to
    # -------------------------------------------------
    assigned_to = 0   # 0 = ALL

    if assigned_raw != "ALL":
        ucur.execute(
            "SELECT id FROM users WHERE id=? OR username=? OR email=?",
            (assigned_raw, assigned_raw, assigned_raw)
        )
        r = ucur.fetchone()
        if not r:
            uconn.close()
            return jsonify({"error": "User not found"}), 404
        assigned_to = r[0]

    uconn.close()

    # -------------------------------------------------
    # update assignment
    # -------------------------------------------------
    gconn = sqlite3.connect(GROUP_DB)
    gcur = gconn.cursor()
    gcur.execute("""
        UPDATE group_tasks
        SET assigned_to=?
        WHERE task_id=?
    """, (assigned_to, task_id))

    gconn.commit()
    gconn.close()

    return jsonify({"success": True})


@group_task_dashboard_bp.route("/group-task-add-member", methods=["POST"])
def group_task_add_member():
    data = request.get_json(silent=True)
    user_id = data.get("user_id")
    group_id = data.get("group_id")
    member = data.get("member")

    if not user_id or not group_id or not member:
        return jsonify({"error": "Invalid data"}), 400

    conn = sqlite3.connect(USER_DB)
    cur = conn.cursor()

    # creator check
    cur.execute("""
        SELECT creator_id FROM group_task_series
        WHERE group_id=?
    """, (group_id,))
    creator_id = cur.fetchone()[0]

    if str(creator_id) != str(user_id):
        return jsonify({"error": "Only creator can add members"}), 403

    # resolve user
    cur.execute(
        "SELECT id FROM users WHERE username=? OR email=?",
        (member, member)
    )
    r = cur.fetchone()
    if not r:
        return jsonify({"error": "User not found"}), 404

    cur.execute("""
        INSERT OR IGNORE INTO group_task_members
        (group_id, user_id, role, added_at)
        VALUES (?, ?, 'member', ?)
    """, (group_id, r[0], datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@group_task_dashboard_bp.route("/group-task-remove-member", methods=["POST"])
def group_task_remove_member():
    data = request.get_json(silent=True)
    user_id = data.get("user_id")
    group_id = data.get("group_id")
    member_id = data.get("member_id")

    if not user_id or not group_id or not member_id:
        return jsonify({"error": "Invalid data"}), 400

    conn = sqlite3.connect(USER_DB)
    cur = conn.cursor()

    # creator check
    cur.execute("""
        SELECT creator_id FROM group_task_series
        WHERE group_id=?
    """, (group_id,))
    creator_id = cur.fetchone()[0]

    if str(creator_id) != str(user_id):
        return jsonify({"error": "Only creator can remove members"}), 403

    # prevent removing creator
    if str(member_id) == str(creator_id):
        return jsonify({"error": "Cannot remove creator"}), 400

    cur.execute("""
        DELETE FROM group_task_members
        WHERE group_id=? AND user_id=?
    """, (group_id, member_id))

    conn.commit()
    conn.close()

    return jsonify({"success": True})
