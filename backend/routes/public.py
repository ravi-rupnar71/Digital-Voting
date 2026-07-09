from flask import Blueprint, jsonify

from ..db import get_db_connection


public_bp = Blueprint("public", __name__)


@public_bp.route("/api/results", methods=["GET"])
def api_results():
    print("DEBUG: /api/results endpoint called!")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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

    cursor.execute("SELECT COUNT(*) AS total FROM votes")
    total_row = cursor.fetchone()
    total_votes = total_row["total"] if total_row and isinstance(total_row, dict) and "total" in total_row else (total_row[0] if total_row else 0)

    cursor.close()
    conn.close()
    
    result = {"candidates": candidates, "total_votes": total_votes}
    print(f"DEBUG: Returning results: {result}")
    return jsonify(result)
