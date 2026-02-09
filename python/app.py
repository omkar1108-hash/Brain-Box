from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import joblib, hashlib
import webbrowser
import threading

from database import get_connection
from task_api import task_bp
from task_dashboard_api import task_dashboard_bp
from task_series_backend import add_task_series, list_task_series, task_series_bp
from task_action_api import task_action_bp
from auth_api import auth_bp
from apscheduler.schedulers.background import BackgroundScheduler
from task_reminder_service import check_and_send_task_reminders
from group_notes_api import group_notes_bp
from group_task_dashboard_api import group_task_dashboard_bp




# =====================================================
# APP SETUP
# =====================================================
app = Flask(
    __name__,
    static_folder="../",
    static_url_path=""
)

CORS(app)

# =====================================================
# REGISTER BLUEPRINTS
# =====================================================
app.register_blueprint(auth_bp)
app.register_blueprint(task_bp)
app.register_blueprint(task_dashboard_bp)
app.register_blueprint(task_action_bp)
app.register_blueprint(task_series_bp)
app.register_blueprint(group_notes_bp)
app.register_blueprint(group_task_dashboard_bp)
# =====================================================
# TASK SERIES API ROUTES
# =====================================================
app.add_url_rule("/add-task-series", view_func=add_task_series, methods=["POST"])
app.add_url_rule("/task-series", view_func=list_task_series, methods=["GET"])

# =====================================================
# ML MODEL
# =====================================================
model = joblib.load("../model/note_classifier.pkl")

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# =====================================================
# NOTES API (SECURED)
# =====================================================
@app.route("/add-note", methods=["POST"])
def add_note():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    password = data.get("password", "")
    force_update = bool(data.get("force_update", False))
    selected_category = data.get("selected_category", "")
    custom_category = data.get("custom_category", "")

    if not title and not content:
        return jsonify({"error": "Title or content required"}), 400

    # ---------- CATEGORY DECISION ----------
    if custom_category:
        category = custom_category
    elif selected_category and selected_category != "Auto":
        category = selected_category
    else:
        text = (title + " " + content).lower()
        if any(k in text for k in ["doctor", "hospital", "medicine"]):
            category = "Medical"
        elif any(k in text for k in ["grocery", "bill", "milk"]):
            category = "Household"
        elif any(k in text for k in ["friend", "party"]):
            category = "Friends"
        elif any(k in text for k in ["family", "parents"]):
            category = "Family"
        elif any(k in text for k in ["goal", "personal"]):
            category = "Personal"
        else:
            probs = model.predict_proba([text])[0]
            category = model.classes_[probs.argmax()] if max(probs) >= 0.30 else "Other"

    hashed_pwd = hash_password(password) if password else None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (category,))
    cursor.execute("SELECT id FROM categories WHERE name=?", (category,))
    category_id = cursor.fetchone()[0]

    cursor.execute(
        "SELECT id FROM notes WHERE title=? AND user_id=?",
        (title, user_id)
    )
    existing = cursor.fetchone()

    if existing and not force_update:
        conn.close()
        return jsonify({"note_exists": True})

    if existing:
        cursor.execute("""
            UPDATE notes
            SET content=?, category_id=?, password=?, updated_at=CURRENT_TIMESTAMP
            WHERE title=? AND user_id=?
        """, (content, category_id, hashed_pwd, title, user_id))
    else:
        cursor.execute("""
            INSERT INTO notes
            (user_id, title, content, category_id, password, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (user_id, title, content, category_id, hashed_pwd))

    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/notes", methods=["GET"])
def get_notes():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    category = request.args.get("category", "All")
    filter_type = request.args.get("filter", "all")

    query = """
        SELECT notes.id, notes.title,
               notes.password IS NOT NULL,
               notes.created_at, notes.updated_at
        FROM notes
        LEFT JOIN categories ON notes.category_id = categories.id
        WHERE notes.user_id = ?
    """
    params = [user_id]

    if category != "All":
        query += " AND categories.name = ?"
        params.append(category)

    if filter_type == "protected":
        query += " AND notes.password IS NOT NULL"
    elif filter_type == "unprotected":
        query += " AND notes.password IS NULL"

    query += " ORDER BY notes.updated_at DESC"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "title": r[1],
            "protected": bool(r[2]),
            "created_at": r[3],
            "updated_at": r[4]
        } for r in rows
    ])


@app.route("/notes/<int:note_id>", methods=["GET"])
def get_note(note_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT notes.title, notes.content, notes.password,
               notes.created_at, notes.updated_at, categories.name
        FROM notes
        LEFT JOIN categories ON notes.category_id = categories.id
        WHERE notes.id=? AND notes.user_id=?
    """, (note_id, user_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "title": row[0],
        "content": row[1],
        "protected": bool(row[2]),
        "created_at": row[3],
        "updated_at": row[4],
        "category": row[5] or "Auto"
    })


@app.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM notes WHERE id=? AND user_id=?",
        (note_id, user_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/categories", methods=["GET"])
def get_user_note_categories():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT c.name
        FROM notes n
        JOIN categories c ON n.category_id = c.id
        WHERE n.user_id = ?
        ORDER BY c.name
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify(["All"] + [r[0] for r in rows])


@app.route("/verify-password", methods=["POST"])
def verify_password():
    data = request.get_json(silent=True) or {}
    note_id = data.get("note_id")
    password = data.get("password", "")
    user_id = data.get("user_id")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password FROM notes WHERE id=? AND user_id=?",
        (note_id, user_id)
    )
    row = cursor.fetchone()
    conn.close()

    return jsonify({"valid": bool(row and row[0] == hash_password(password))})



# =====================================================
# FRONTEND ROUTES (UNCHANGED)
# =====================================================
@app.route("/")
def root():
    return send_from_directory("../html", "login.html")

@app.route("/notes-dashboard")
def notes_dashboard_page():
    return send_from_directory("../html", "dashboard.html")

@app.route("/notes-create")
def notes_create_page():
    return send_from_directory("../html", "index.html")

@app.route("/notes-edit")
def notes_edit_page():
    return send_from_directory("../html", "edit.html")

@app.route("/task-dashboard")
def task_dashboard_page():
    return send_from_directory("../html", "task_dashboard.html")

@app.route("/task-create")
def task_create_page():
    return send_from_directory("../html", "task_create.html")

@app.route("/task-edit")
def task_edit_page():
    return send_from_directory("../html", "task_edit.html")

@app.route("/task-series-create")
def task_series_create_page():
    return send_from_directory("../html", "task_series_create.html")

@app.route("/task-series-edit")
def task_series_edit_page():
    return send_from_directory("../html", "task_series_edit.html")

@app.route("/login")
def login_page():
    return send_from_directory("../html", "login.html")


@app.route("/register")
def register_page():
    return send_from_directory("../html", "register.html")


@app.route("/group-dashboard")
def group_dashboard_page():
    return send_from_directory("../html", "group_dashboard.html")

@app.route("/group-note-create")
def group_note_create_page():
    return send_from_directory("../html", "group_note_create.html")

@app.route("/group-note-edit")
def group_note_edit_page():
    return send_from_directory("../html", "group_note_edit.html")


@app.route("/group-task-dashboard")
def group_task_dashboard_page():
    return send_from_directory("../html", "group_task_dashboard.html")


@app.route("/group-task-create")
def group_task_create_page():
    return send_from_directory("../html", "group_task_create.html")


@app.route("/group-task-edit")
def group_task_edit_page():
    return send_from_directory("../html", "group_task_edit.html")

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")


scheduler = BackgroundScheduler()
scheduler.add_job(
    check_and_send_task_reminders,
    "interval",
    minutes=5
)
scheduler.start()

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    app.run(debug=True, use_reloader=False)
