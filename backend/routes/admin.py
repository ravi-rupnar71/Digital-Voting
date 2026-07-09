from flask import Blueprint, jsonify, request

from ..db import INTEGRITY_ERRORS, get_db_connection, reset_votes
from ..mail import send_verification_otp
from ..security import admin_required


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/api/admin/dashboard", methods=["GET"])
@admin_required
def api_admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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


@admin_bp.route("/api/admin/reset_votes", methods=["POST"])
@admin_required
def api_admin_reset_votes():
    reset_votes()
    return jsonify({"message": "Vote totals reset successfully."})


@admin_bp.route("/api/admin/reconcile", methods=["POST"])
@admin_required
def api_admin_reconcile_votes():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT candidate_id, COUNT(*) FROM votes GROUP BY candidate_id")
    rows = cursor.fetchall()

    cursor.execute("UPDATE candidates SET votes = 0")

    for row in rows:
        candidate_id = row[0]
        count = row[1]
        cursor.execute("UPDATE candidates SET votes = %s WHERE id = %s", (count, candidate_id))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Reconciled candidate vote counts from votes table."})


@admin_bp.route("/api/admin/candidate", methods=["POST"])
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
    verification = send_verification_otp("candidate", candidate_id, email, name)
    return jsonify({
        "message": "Candidate added.",
        "candidate_id": candidate_id,
        "requires_verification": True,
        "verification_otp": verification["otp"],
        "email_sent": verification["email_sent"],
    })


@admin_bp.route("/api/admin/candidate/<int:candidate_id>", methods=["PUT", "DELETE"])
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


@admin_bp.route("/api/admin/voter", methods=["POST"])
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
    verification = send_verification_otp("voter", voter_db_id, email, name)
    return jsonify({
        "message": "Voter added.",
        "voter_db_id": voter_db_id,
        "requires_verification": True,
        "verification_otp": verification["otp"],
        "email_sent": verification["email_sent"],
    })


@admin_bp.route("/api/admin/voter/<int:voter_id>", methods=["PUT", "DELETE"])
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
