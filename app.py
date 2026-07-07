from flask import Flask, jsonify, request, session
from flask_cors import CORS
import mysql.connector
from mysql.connector import IntegrityError as MySQLIntegrityError
import re
import random
import smtplib
import secrets
from functools import wraps
from datetime import datetime, timedelta
from email.message import EmailMessage
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Passwords are stored and compared as plain text in this deployment.
# The application no longer attempts to import or use password hashing.

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(24)

CORS(app, supports_credentials=True, origins=["http://localhost:4200"])

INTEGRITY_ERRORS = (MySQLIntegrityError,)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "root"),
    "database": os.environ.get("DB_NAME", "digital_voting"),
}

class CursorWrapper:
    def __init__(self, cursor, dictionary=False):
        self._cursor = cursor
        self._dictionary = dictionary

    def execute(self, operation, params=()):
        self._cursor.execute(operation, params)
        return self

    def executemany(self, operation, seq_of_params):
        self._cursor.executemany(operation, seq_of_params)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if self._dictionary and row is not None and hasattr(row, "keys"):
            return dict(row)
        return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        if self._dictionary:
            return [dict(row) if row is not None and hasattr(row, "keys") else row for row in rows]
        return rows

    def close(self):
        return self._cursor.close()

    def __getattr__(self, item):
        return getattr(self._cursor, item)


class ConnectionWrapper:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self, dictionary=False):
        cursor = self._connection.cursor(dictionary=dictionary)
        return CursorWrapper(cursor, dictionary=dictionary)

    def commit(self):
        return self._connection.commit()

    def close(self):
        return self._connection.close()

    def __getattr__(self, item):
        return getattr(self._connection, item)


def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return ConnectionWrapper(conn)


def ensure_column(conn, table_name, column_name, column_definition):
    cursor = conn.cursor()
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE %s", (column_name,))
    if cursor.fetchone() is None:
        cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN {column_definition}")
    cursor.close()


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            party VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) DEFAULT '',
            votes INT NOT NULL DEFAULT 0,
            is_verified INT NOT NULL DEFAULT 0,
            verification_otp VARCHAR(10) DEFAULT '',
            verification_expires_at VARCHAR(255) DEFAULT ''
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            id INT AUTO_INCREMENT PRIMARY KEY,
            voter_id VARCHAR(255) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            has_voted INT NOT NULL DEFAULT 0,
            is_verified INT NOT NULL DEFAULT 0,
            verification_otp VARCHAR(10) DEFAULT '',
            verification_expires_at VARCHAR(255) DEFAULT ''
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            voter_id VARCHAR(255) NOT NULL,
            candidate_id INT NOT NULL,
            UNIQUE(voter_id, candidate_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL DEFAULT 'admin@example.com'
        )
    """)

    ensure_column(conn, "candidates", "password", "`password` VARCHAR(255) DEFAULT ''")
    ensure_column(conn, "candidates", "is_verified", "is_verified INT NOT NULL DEFAULT 0")
    ensure_column(conn, "candidates", "verification_otp", "verification_otp VARCHAR(10) DEFAULT ''")
    ensure_column(conn, "candidates", "verification_expires_at", "verification_expires_at VARCHAR(255) DEFAULT ''")
    ensure_column(conn, "voters", "is_verified", "is_verified INT NOT NULL DEFAULT 0")
    ensure_column(conn, "voters", "verification_otp", "verification_otp VARCHAR(10) DEFAULT ''")
    ensure_column(conn, "voters", "verification_expires_at", "verification_expires_at VARCHAR(255) DEFAULT ''")
    ensure_column(conn, "admin", "email", "email VARCHAR(255) NOT NULL DEFAULT 'admin@example.com'")

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admin WHERE username = %s", ("admin",))
    admin_user = cursor.fetchone()

    if admin_user is None:
        cursor.execute(
            "INSERT INTO admin (username, password, email) VALUES (%s, %s, %s)",
            ("admin", "admin123", "admin@example.com"),
        )
    else:
        password_value = admin_user["password"] if isinstance(admin_user, dict) else admin_user[2]
        if password_value != "admin123":
            cursor.execute(
                "UPDATE admin SET password = %s WHERE id = %s",
                ("admin123", admin_user["id"] if isinstance(admin_user, dict) else admin_user[0]),
            )

    conn.commit()
    cursor.close()
    conn.close()


def reset_votes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE candidates SET votes = 0")
    cursor.execute("UPDATE voters SET has_voted = 0")
    cursor.execute("DELETE FROM votes")
    conn.commit()
    cursor.close()
    conn.close()


init_db()

# ================= EMAIL/OTP SETUP =================
OTP_EXPIRY_SECONDS = 120
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email):
    return bool(EMAIL_REGEX.match(email or ""))


def generate_otp(length=6):
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def verify_password(stored_password, provided_password):
    stored_password = str(stored_password or "")
    provided_password = str(provided_password or "")
    # Simple exact match comparison (no hashing)
    return stored_password.strip() == provided_password.strip()


def send_email(to_email, subject, body):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return False, "Email credentials not configured."
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return True, "Email sent successfully."
    except Exception as e:
        return False, f"Could not send email to {to_email} ({e})."


def send_otp_email(recipient_email, recipient_name, otp, purpose):
    subject = "Your OTP for Digital Voting System"
    body = (
        f"Hello {recipient_name},\n\n"
        f"Your OTP is: {otp}\n"
        f"It is valid for {OTP_EXPIRY_SECONDS // 60} minutes.\n\n"
        f"Enter this code to continue."
    )
    if purpose == "admin":
        subject = "Admin login verification"
        body = (
            f"Hello {recipient_name},\n\n"
            f"Your admin OTP is: {otp}\n"
            f"It expires in {OTP_EXPIRY_SECONDS // 60} minutes.\n\n"
            f"Enter this code to continue."
        )
    return send_email(recipient_email, subject, body)


def save_otp_for_record(record_type, record_id, otp, expires_at):
    conn = get_db_connection()
    cursor = conn.cursor()
    if record_type == "voter":
        cursor.execute("UPDATE voters SET verification_otp = %s, verification_expires_at = %s WHERE id = %s", (otp, expires_at, record_id))
    else:
        cursor.execute("UPDATE candidates SET verification_otp = %s, verification_expires_at = %s WHERE id = %s", (otp, expires_at, record_id))
    conn.commit()
    cursor.close()
    conn.close()


def send_verification_otp(record_type, record_id, recipient_email, recipient_name):
    otp = generate_otp()
    expires_at = (datetime.now() + timedelta(seconds=OTP_EXPIRY_SECONDS)).isoformat()
    save_otp_for_record(record_type, record_id, otp, expires_at)
    subject = "Verify your email"
    body = (
        f"Hello {recipient_name},\n\n"
        f"Your verification code is: {otp}\n"
        f"It expires in {OTP_EXPIRY_SECONDS // 60} minutes.\n\n"
        f"Open the verification page to activate your account."
    )
    return send_email(recipient_email, subject, body)


# ================= DECORATORS =================
def voter_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "voter":
            return jsonify({"error": "Unauthorized. Please login as a voter."}), 401
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"error": "Unauthorized. Please login as admin."}), 401
        return f(*args, **kwargs)
    return wrapper


@app.route("/api/auth/status", methods=["GET"])
def check_auth_status():
    if "role" in session:
        return jsonify({"authenticated": True, "role": session.get("role"), "name": session.get("voter_name", session.get("admin_username", ""))})
    return jsonify({"authenticated": False})


@app.route("/api/voter/login", methods=["POST"])
def api_voter_login():
    data = request.json or {}
    voter_id = data.get("voter_id") or data.get("voterId") or ""
    password = data.get("password", "")

    if not voter_id or not password:
        return jsonify({"error": "Voter ID and password required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM voters WHERE voter_id = %s", (voter_id,))
        voter = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

    if not voter or not verify_password(voter.get("password", ""), password):
        return jsonify({"error": "Invalid Voter ID or password."}), 401

    if voter.get("is_verified", 0) != 1:
        send_verification_otp("voter", voter["id"], voter["email"], voter["name"])
        return jsonify({"error": "Account not verified.", "requires_verification": True, "voter_db_id": voter["id"]}), 403

    otp = generate_otp()
    session.clear()
    session["pending_voter_id"] = voter["voter_id"]
    session["pending_voter_name"] = voter["name"]
    session["pending_voter_email"] = voter.get("email", "")
    session["otp"] = otp
    session["otp_time"] = datetime.now().isoformat()

    send_otp_email(voter.get("email", ""), voter.get("name", ""), otp, "voter")
    return jsonify({"message": "OTP sent successfully.", "requires_otp": True, "fallback_otp": otp})


@app.route("/api/voter/otp", methods=["POST"])
def api_voter_otp():
    if "pending_voter_id" not in session or "otp" not in session:
        return jsonify({"error": "Session missing or expired."}), 400

    data = request.json or {}
    if data.get("resend"):
        otp = generate_otp()
        session["otp"] = otp
        session["otp_time"] = datetime.now().isoformat()
        send_otp_email(session.get("pending_voter_email", ""), session.get("pending_voter_name", "Voter"), otp, "voter")
        return jsonify({"message": "New OTP sent."})

    entered_otp = data.get("otp", "").strip()
    try:
        expiry_time = datetime.fromisoformat(session["otp_time"]) + timedelta(seconds=OTP_EXPIRY_SECONDS)
    except (KeyError, ValueError):
        session.clear()
        return jsonify({"error": "Session corrupted. Please login again."}), 400

    if datetime.now() > expiry_time:
        session.clear()
        return jsonify({"error": "OTP expired. Please login again."}), 400

    if entered_otp == session["otp"]:
        voter_id = session["pending_voter_id"]
        voter_name = session["pending_voter_name"]
        session.clear()
        session["role"] = "voter"
        session["voter_id"] = voter_id
        session["voter_name"] = voter_name
        return jsonify({"message": "Login successful", "role": "voter"})

    return jsonify({"error": "Incorrect OTP."}), 401


@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin WHERE username = %s", (username,))
        admin_user = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

    if not admin_user or not verify_password(admin_user.get("password", ""), password):
        return jsonify({"error": "Invalid admin credentials."}), 401

    otp = generate_otp()
    session.clear()
    session["pending_admin_username"] = admin_user["username"]
    session["pending_admin_email"] = admin_user.get("email", "")
    session["otp"] = otp
    session["otp_time"] = datetime.now().isoformat()

    send_otp_email(admin_user.get("email", ""), admin_user.get("username", "admin"), otp, "admin")
    return jsonify({"message": "OTP sent successfully.", "requires_otp": True, "fallback_otp": otp})


@app.route("/api/admin/otp", methods=["POST"])
def api_admin_otp():
    if "pending_admin_username" not in session or "otp" not in session:
        return jsonify({"error": "Session missing or expired."}), 400

    data = request.json or {}
    if data.get("resend"):
        otp = generate_otp()
        session["otp"] = otp
        session["otp_time"] = datetime.now().isoformat()
        send_otp_email(session.get("pending_admin_email", ""), session.get("pending_admin_username", "Admin"), otp, "admin")
        return jsonify({"message": "New OTP sent."})

    entered_otp = data.get("otp", "").strip()
    try:
        expiry_time = datetime.fromisoformat(session["otp_time"]) + timedelta(seconds=OTP_EXPIRY_SECONDS)
    except (KeyError, ValueError):
        session.clear()
        return jsonify({"error": "Session corrupted."}), 400

    if datetime.now() > expiry_time:
        session.clear()
        return jsonify({"error": "OTP expired."}), 400

    if entered_otp == session["otp"]:
        session.clear()
        session["role"] = "admin"
        session["admin_username"] = session.get("pending_admin_username", "admin")
        return jsonify({"message": "Login successful", "role": "admin"})

    return jsonify({"error": "Incorrect OTP."}), 401


@app.route("/api/candidates", methods=["GET"])
@voter_required
def api_get_vote_candidates():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM voters WHERE voter_id = %s", (session["voter_id"],))
    voter = cursor.fetchone()

    if voter["has_voted"] == 1:
        cursor.close()
        conn.close()
        return jsonify({"has_voted": True}), 200

    cursor.execute("SELECT id, name, party FROM candidates")
    candidates = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"has_voted": False, "candidates": candidates, "voter_name": voter["name"]})


@app.route("/api/vote", methods=["POST"])
@voter_required
def api_submit_vote():
    data = request.json or {}
    candidate_id = data.get("candidate_id") or data.get("candidateId")

    if not candidate_id:
        return jsonify({"error": "No candidate selected."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM voters WHERE voter_id = %s", (session["voter_id"],))
    voter = cursor.fetchone()

    if voter["has_voted"] == 1:
        cursor.close()
        conn.close()
        return jsonify({"error": "Already voted."}), 403

    try:
        cursor.execute("INSERT INTO votes (voter_id, candidate_id) VALUES (%s, %s)", (voter["voter_id"], candidate_id))
        cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE id = %s", (candidate_id,))
        cursor.execute("UPDATE voters SET has_voted = 1 WHERE voter_id = %s", (voter["voter_id"],))
        conn.commit()
    except INTEGRITY_ERRORS:
        cursor.close()
        conn.close()
        return jsonify({"error": "Already voted."}), 403

    cursor.close()
    conn.close()
    send_email(
        voter["email"],
        "Your vote has been recorded",
        f"Hello {voter['name']},\n\nThis confirms your vote has been recorded successfully."
    )
    return jsonify({"message": "Vote recorded successfully."})


@app.route("/api/results", methods=["GET"])
def api_results():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Compute votes per candidate from the votes table to avoid inconsistencies
    cursor.execute("""
        SELECT c.id, c.name, c.party, COALESCE(v.count, 0) AS votes
        FROM candidates c
        LEFT JOIN (
            SELECT candidate_id, COUNT(*) AS count
            FROM votes
            GROUP BY candidate_id
        ) v ON c.id = v.candidate_id
        ORDER BY votes DESC
    """)
    candidates = cursor.fetchall()

    # Total votes derived from the votes table
    cursor.execute("SELECT COUNT(*) AS total FROM votes")
    total_row = cursor.fetchone()
    total_votes = total_row["total"] if total_row and isinstance(total_row, dict) and "total" in total_row else (total_row[0] if total_row else 0)

    cursor.close()
    conn.close()
    return jsonify({"candidates": candidates, "total_votes": total_votes})


@app.route("/api/admin/dashboard", methods=["GET"])
@admin_required
def api_admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Return candidates with vote counts computed from votes table
    cursor.execute("""
        SELECT c.id, c.name, c.party, c.email, COALESCE(v.count, 0) AS votes, c.is_verified
        FROM candidates c
        LEFT JOIN (
            SELECT candidate_id, COUNT(*) AS count
            FROM votes
            GROUP BY candidate_id
        ) v ON c.id = v.candidate_id
        ORDER BY c.id
    """)
    candidates = cursor.fetchall()

    cursor.execute("SELECT id, voter_id, name, email, has_voted, is_verified FROM voters ORDER BY id")
    voters = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"candidates": candidates, "voters": voters})


@app.route("/api/admin/reset_votes", methods=["POST"])
@admin_required
def api_admin_reset_votes():
    reset_votes()
    return jsonify({"message": "Vote totals reset successfully."})


@app.route("/api/admin/reconcile", methods=["POST"])
@admin_required
def api_admin_reconcile_votes():
    """Recompute `candidates.votes` from the `votes` table and update the candidates table.
    This helps fix inconsistencies caused by manual edits or earlier bugs."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get counts per candidate
    cursor.execute("SELECT candidate_id, COUNT(*) FROM votes GROUP BY candidate_id")
    rows = cursor.fetchall()

    # Reset all to 0 first
    cursor.execute("UPDATE candidates SET votes = 0")

    for row in rows:
        candidate_id = row[0]
        count = row[1]
        cursor.execute("UPDATE candidates SET votes = %s WHERE id = %s", (count, candidate_id))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Reconciled candidate vote counts from votes table."})


@app.route("/api/admin/candidate", methods=["POST"])
@admin_required
def api_add_candidate():
    data = request.json or {}
    name = data.get("name", "").strip()
    party = data.get("party", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not name or not party or not email or not password:
        return jsonify({"error": "All fields required."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO candidates (name, party, email, password) VALUES (%s, %s, %s, %s)", (name, party, email, password))
        candidate_id = cursor.lastrowid
        conn.commit()
    except INTEGRITY_ERRORS:
        cursor.close()
        conn.close()
        return jsonify({"error": "Email already exists."}), 409
    cursor.close()
    conn.close()
    send_verification_otp("candidate", candidate_id, email, name)
    return jsonify({"message": "Candidate added.", "candidate_id": candidate_id, "requires_verification": True})


@app.route("/api/admin/candidate/<int:candidate_id>", methods=["PUT", "DELETE"])
@admin_required
def api_manage_candidate(candidate_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == "DELETE":
        cursor.execute("DELETE FROM votes WHERE candidate_id = %s", (candidate_id,))
        cursor.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Candidate deleted."})

    data = request.json or {}
    name = data.get("name", "").strip()
    party = data.get("party", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    if password:
        cursor.execute("UPDATE candidates SET name=%s, party=%s, email=%s, password=%s WHERE id=%s", (name, party, email, password, candidate_id))
    else:
        cursor.execute("UPDATE candidates SET name=%s, party=%s, email=%s WHERE id=%s", (name, party, email, candidate_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Candidate updated."})


@app.route("/api/admin/voter", methods=["POST"])
@admin_required
def api_add_voter():
    data = request.json or {}
    voter_id = data.get("voter_id", "").strip().upper()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not voter_id or not name or not email or not password:
        return jsonify({"error": "All fields required."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO voters (voter_id, name, email, password) VALUES (%s, %s, %s, %s)", (voter_id, name, email, password))
        voter_db_id = cursor.lastrowid
        conn.commit()
    except INTEGRITY_ERRORS:
        cursor.close()
        conn.close()
        return jsonify({"error": "Voter ID or Email already exists."}), 409
    cursor.close()
    conn.close()
    send_verification_otp("voter", voter_db_id, email, name)
    return jsonify({"message": "Voter added.", "voter_db_id": voter_db_id, "requires_verification": True})


@app.route("/api/admin/voter/<int:voter_id>", methods=["PUT", "DELETE"])
@admin_required
def api_manage_voter(voter_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == "DELETE":
        cursor.execute("SELECT has_voted, voter_id FROM voters WHERE id = %s", (voter_id,))
        voter = cursor.fetchone()
        if voter and voter["has_voted"] == 1:
            cursor.close()
            conn.close()
            return jsonify({"error": "Voter has already voted, cannot delete."}), 403
        cursor.execute("DELETE FROM votes WHERE voter_id = %s", (voter["voter_id"],))
        cursor.execute("DELETE FROM voters WHERE id = %s", (voter_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Voter deleted."})

    data = request.json or {}
    v_id = data.get("voter_id", "").strip().upper()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    if password:
        cursor.execute("UPDATE voters SET voter_id=%s, name=%s, email=%s, password=%s WHERE id=%s", (v_id, name, email, password, voter_id))
    else:
        cursor.execute("UPDATE voters SET voter_id=%s, name=%s, email=%s WHERE id=%s", (v_id, name, email, voter_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Voter updated."})


@app.route("/api/verify/<entity>/<int:entity_id>", methods=["POST"])
def api_verify_account(entity, entity_id):
    if entity not in ["voter", "candidate"]:
        return jsonify({"error": "Invalid entity."}), 400
    data = request.json or {}
    table = "voters" if entity == "voter" else "candidates"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table} WHERE id = %s", (entity_id,))
    record = cursor.fetchone()
    if not record:
        cursor.close()
        conn.close()
        return jsonify({"error": f"{entity.capitalize()} not found."}), 404
    if data.get("resend"):
        send_verification_otp(entity, record["id"], record["email"], record["name"])
        cursor.close()
        conn.close()
        return jsonify({"message": "New verification code sent."})
    entered_otp = data.get("otp", "").strip()
    expires_at = record.get("verification_expires_at")
    if expires_at and datetime.now() < datetime.fromisoformat(expires_at) and entered_otp == record.get("verification_otp"):
        cursor.execute(f"UPDATE {table} SET is_verified = 1, verification_otp = '', verification_expires_at = '' WHERE id = %s", (entity_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Verified successfully."})
    cursor.close()
    conn.close()
    return jsonify({"error": "Invalid or expired verification code."}), 400


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out successfully."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
