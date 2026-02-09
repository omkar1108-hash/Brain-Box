from flask import Blueprint, request, jsonify
import sqlite3
from pathlib import Path

group_notes_bp = Blueprint("group_notes_bp", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent
GROUP_DB = BASE_DIR / "database" / "group_notes.db"
USER_DB = BASE_DIR / "database" / "user_data.db"


# =====================================================
# GET GROUP NOTES FOR DASHBOARD (FIXED)
# =====================================================
@group_notes_bp.route("/group-notes", methods=["GET"])
def get_group_notes():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # 1️⃣ get memberships from user_data.db
    conn = sqlite3.connect(USER_DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT group_note_id, role
        FROM group_note_members
        WHERE user_id = ?
    """, (user_id,))

    memberships = cur.fetchall()
    conn.close()

    if not memberships:
        return jsonify([])

    note_ids = [m[0] for m in memberships]
    role_map = {m[0]: m[1] for m in memberships}

    # 2️⃣ get note data from group_notes.db
    conn = sqlite3.connect(GROUP_DB)
    cur = conn.cursor()

    placeholders = ",".join("?" for _ in note_ids)

    cur.execute(f"""
        SELECT id, title, created_at
        FROM group_notes
        WHERE id IN ({placeholders})
        ORDER BY updated_at DESC
    """, note_ids)

    rows = cur.fetchall()
    conn.close()

    # 3️⃣ merge result
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "title": r[1],
            "created_at": r[2],
            "role": role_map.get(r[0], "viewer")
        })

    return jsonify(result)


# =====================================================
# CREATE GROUP NOTE (OK, only small improvement)
# =====================================================
@group_notes_bp.route("/create-group-note", methods=["POST"])
def create_group_note():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    title = (data.get("title") or "").strip()
    content = data.get("content", "")
    members = data.get("members", [])

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if not title:
        return jsonify({"error": "Title required"}), 400

    # ---------------------------
    # CREATE NOTE
    # ---------------------------
    conn = sqlite3.connect(GROUP_DB)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO group_notes (title, created_by)
        VALUES (?, ?)
    """, (title, user_id))

    group_note_id = cur.lastrowid

    cur.execute("""
        INSERT INTO group_note_blocks
        (group_note_id, content, created_by)
        VALUES (?, ?, ?)
    """, (group_note_id, content, user_id))

    conn.commit()
    conn.close()

    # ---------------------------
    # ADD MEMBERS
    # ---------------------------
    conn = sqlite3.connect(USER_DB)
    cur = conn.cursor()

    # creator = owner
    cur.execute("""
        INSERT INTO group_note_members
        (group_note_id, user_id, email, role)
        VALUES (?, ?, '', 'owner')
    """, (group_note_id, user_id))

    for email in members:
        cur.execute("""
            INSERT OR IGNORE INTO group_note_members
            (group_note_id, email, role)
            VALUES (?, ?, 'viewer')
        """, (group_note_id, email))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "id": group_note_id})


@group_notes_bp.route("/group-note/<int:note_id>", methods=["GET"])
def get_group_note(note_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = sqlite3.connect(GROUP_DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT title, created_at, updated_at
        FROM group_notes
        WHERE id = ?
    """, (note_id,))
    note = cur.fetchone()

    cur.execute("""
        SELECT content
        FROM group_note_blocks
        WHERE group_note_id = ?
        ORDER BY id ASC
        LIMIT 1
    """, (note_id,))
    block = cur.fetchone()

    conn.close()

    return jsonify({
        "title": note[0],
        "content": block[0] if block else "",
        "created_at": note[1],
        "updated_at": note[2]
    })


@group_notes_bp.route("/group-note/<int:note_id>", methods=["POST"])
def update_group_note(note_id):
    data = request.get_json() or {}
    user_id = data.get("user_id")
    blocks = data.get("blocks", [])

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = sqlite3.connect(GROUP_DB)
    cur = conn.cursor()

    # clear old blocks (simple approach)
    cur.execute(
        "DELETE FROM group_note_blocks WHERE group_note_id=?",
        (note_id,)
    )

    for b in blocks:
        cur.execute("""
            INSERT INTO group_note_blocks
            (group_note_id, content, created_by, editable_by)
            VALUES (?, ?, ?, ?)
        """, (
            note_id,
            b["content"],
            b["created_by"],
            b["editable_by"]
        ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})
