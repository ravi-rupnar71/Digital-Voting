from flask import Blueprint, jsonify, request, session

from ..db import INTEGRITY_ERRORS, get_db_connection
from ..mail import send_email
from ..security import voter_required


voting_bp = Blueprint("voting", __name__)


# PUBLIC ENDPOINT FOR TESTING - Remove in production
@voting_bp.route("/api/candidates-test", methods=["GET"])
def api_get_candidates_test():
    """Test endpoint without authentication"""
    print(f"DEBUG: /candidates-test called. Session: {dict(session)}")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, party FROM candidates ORDER BY name")
    candidates = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({
        "has_voted": False, 
        "candidates": candidates, 
        "voter_name": "Test Voter",
        "debug": True
    })


@voting_bp.route("/api/candidates", methods=["GET"])
# @voter_required  # TEMPORARILY DISABLED FOR TESTING
def api_get_vote_candidates():
    """Get candidates - temporarily public for debugging"""
    print(f"DEBUG: /candidates called. Session role: {session.get('role')}, voter_id: {session.get('voter_id')}")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Try to get voter info from session, but don't require it for now
    voter_name = "Voter"
    if session.get("voter_id"):
        try:
            cursor.execute("SELECT * FROM voters WHERE voter_id = %s", (session["voter_id"],))
            voter = cursor.fetchone()
            if voter:
                voter_name = voter["name"]
                if voter["has_voted"] == 1:
                    cursor.close()
                    conn.close()
                    return jsonify({"has_voted": True}), 200
        except:
            pass

    cursor.execute("SELECT id, name, party FROM candidates ORDER BY name")
    candidates = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"has_voted": False, "candidates": candidates, "voter_name": voter_name})


# Public test endpoint for debugging (remove in production)
@voting_bp.route("/api/candidates-public", methods=["GET"])
def api_get_candidates_public():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, party FROM candidates ORDER BY name")
    candidates = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"candidates": candidates, "test_mode": True})


@voting_bp.route("/api/vote", methods=["POST"])
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
