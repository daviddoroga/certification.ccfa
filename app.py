import os
import sqlite3
import bcrypt
from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)
SECRET_KEY = os.environ["SECRET_KEY"]
DB_PATH = "users.db"


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400
    if not isinstance(username, str) or len(username) > 64:
        return jsonify({"error": "username must be a string under 64 characters"}), 400
    if not isinstance(password, str) or len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        conn.commit()
        return jsonify({"message": "User created"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username taken"}), 409
    finally:
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    conn = get_db()
    row = conn.execute(
        "SELECT id, role, password FROM users WHERE username=?", (username,)
    ).fetchone()
    conn.close()

    if not row or not verify_password(password, row[2]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({"user_id": row[0], "role": row[1]}, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token})


def get_current_user(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return None


@app.route("/notes", methods=["GET"])
def get_notes():
    user = get_current_user(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    note_id = request.args.get("id")
    conn = get_db()

    if note_id:
        row = conn.execute(
            "SELECT content FROM notes WHERE id=? AND user_id=?",
            (note_id, user["user_id"]),
        ).fetchone()
        conn.close()
        return jsonify({"content": row[0]}) if row else (jsonify({"error": "Not found"}), 404)

    rows = conn.execute(
        "SELECT id, content FROM notes WHERE user_id=?", (user["user_id"],)
    ).fetchall()
    conn.close()
    return jsonify([{"id": r[0], "content": r[1]} for r in rows])


@app.route("/notes", methods=["POST"])
def create_note():
    user = get_current_user(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True) or {}
    content = data.get("content", "")
    if not isinstance(content, str) or not content:
        return jsonify({"error": "content is required"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO notes (user_id, content) VALUES (?, ?)",
        (user["user_id"], content),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Note saved"}), 201


@app.route("/admin/users", methods=["GET"])
def admin_users():
    user = get_current_user(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403

    conn = get_db()
    rows = conn.execute("SELECT id, username, role FROM users").fetchall()
    conn.close()
    return jsonify([{"id": r[0], "username": r[1], "role": r[2]} for r in rows])


@app.route("/search", methods=["GET"])
def search_notes():
    user = get_current_user(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    query = request.args.get("q", "")
    conn = get_db()
    rows = conn.execute(
        "SELECT id, content FROM notes WHERE user_id=? AND content LIKE ?",
        (user["user_id"], f"%{query}%"),
    ).fetchall()
    conn.close()
    return jsonify([{"id": r[0], "content": r[1]} for r in rows])


if __name__ == "__main__":
    init_db()
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug)
