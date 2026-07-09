from datetime import datetime

from flask import Blueprint, jsonify, request, session, make_response

from ..db import get_db_connection
from ..mail import send_verification_otp


verification_bp = Blueprint("verification", __name__)


@verification_bp.route("/api/verify/<entity>/<int:entity_id>", methods=["POST"])
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
        # If a voter verified their email, create a session so they are immediately authenticated
        if entity == 'voter':
            session.clear()
            session['role'] = 'voter'
            # prefer voter_id if present, otherwise fall back to numeric id
            session['voter_id'] = record.get('voter_id') or record.get('id')
            session['voter_name'] = record.get('name', '')
            response = make_response(jsonify({"message": "Verified successfully.", "role": "voter"}))
            return response

        return jsonify({"message": "Verified successfully."})
    cursor.close()
    conn.close()
    return jsonify({"error": "Invalid or expired verification code."}), 400
