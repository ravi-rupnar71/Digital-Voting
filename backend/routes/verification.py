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
        pending_update = session.pop("pending_update", None)
        if pending_update and pending_update.get("entity") == entity and pending_update.get("entity_id") == entity_id:
            update_data = pending_update.get("data", {})
            if entity == "voter":
                update_fields = []
                values = []
                if "voter_id" in update_data:
                    update_fields.append("voter_id=%s")
                    values.append(update_data["voter_id"])
                if "name" in update_data:
                    update_fields.append("name=%s")
                    values.append(update_data["name"])
                if "email" in update_data:
                    update_fields.append("email=%s")
                    values.append(update_data["email"])
                if "password" in update_data and update_data["password"]:
                    update_fields.append("password=%s")
                    values.append(update_data["password"])
                if update_fields:
                    values.append(entity_id)
                    cursor.execute(f"UPDATE voters SET {', '.join(update_fields)} WHERE id=%s", tuple(values))
            else:
                update_fields = []
                values = []
                if "name" in update_data:
                    update_fields.append("name=%s")
                    values.append(update_data["name"])
                if "party" in update_data:
                    update_fields.append("party=%s")
                    values.append(update_data["party"])
                if "email" in update_data:
                    update_fields.append("email=%s")
                    values.append(update_data["email"])
                if "password" in update_data and update_data["password"]:
                    update_fields.append("password=%s")
                    values.append(update_data["password"])
                if update_fields:
                    values.append(entity_id)
                    cursor.execute(f"UPDATE candidates SET {', '.join(update_fields)} WHERE id=%s", tuple(values))

        cursor.execute(f"UPDATE {table} SET is_verified = 1, verification_otp = '', verification_expires_at = '' WHERE id = %s", (entity_id,))
        conn.commit()
        cursor.close()
        conn.close()
        if entity == 'voter' and not pending_update:
            session.clear()
            session['role'] = 'voter'
            session['voter_id'] = record.get('voter_id') or record.get('id')
            session['voter_name'] = record.get('name', '')
            session.modified = True
            response = make_response(jsonify({"message": "Verified successfully.", "role": "voter"}))
            return response

        if entity == 'candidate' and not pending_update:
            session.modified = True
            return jsonify({"message": "Verified successfully."})

        return jsonify({"message": "Verified successfully."})
    cursor.close()
    conn.close()
    return jsonify({"error": "Invalid or expired verification code."}), 400
