from flask import Blueprint, request, jsonify
import sqlite3
import os
import shutil
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
import traceback

auth_bp = Blueprint("auth_bp", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ Writable DB path (Render)
DB_PATH = "/tmp/user_data.db"

# ✅ Original DB
ORIGINAL_DB = BASE_DIR / "database" / "user_data.db"

# =====================================================
# INIT DB (SAFE COPY)
# =====================================================
def init_db():
    try:
        if not os.path.exists(DB_PATH):
            shutil.copy(ORIGINAL_DB, DB_PATH)
            print("✅ DB copied to /tmp")
        else:
            print("ℹ️ Using existing /tmp DB")

    except Exception as e:
        print("❌ DB INIT ERROR:", str(e))
        traceback.print_exc()

init_db()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
# REGISTER
# =====================================================
@auth_bp.route("/register", methods=["POST"])
def register():
    print("🔥 REGISTER API HIT")

    try:
        data = request.get_json(silent=True)
        print("DATA:", data)

        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400

        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not username or not email or not password:
            return jsonify({"success": False, "error": "All fields required"}), 400

        password_hash = generate_password_hash(password)

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        """, (username, email, password_hash))

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "error": "Username or email already exists"
        }), 409

    except Exception as e:
        print("❌ REGISTER ERROR:", str(e))
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =====================================================
# LOGIN
# =====================================================
@auth_bp.route("/login", methods=["POST"])
def login():
    print("🔥 LOGIN API HIT")

    try:
        data = request.get_json(silent=True)
        print("DATA:", data)

        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400

        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"success": False, "error": "Missing fields"}), 400

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, password_hash
            FROM users
            WHERE username = ? OR email = ?
        """, (username, username.lower()))

        user = cur.fetchone()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({
                "success": False,
                "error": "Invalid credentials"
            }), 401

        return jsonify({
            "success": True,
            "user_id": user["id"]
        })

    except Exception as e:
        print("❌ LOGIN ERROR:", str(e))
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
