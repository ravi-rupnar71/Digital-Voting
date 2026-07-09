import secrets
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, make_response, request, session

from ..config import OTP_EXPIRY_SECONDS
from ..db import get_db_connection
from ..mail import generate_otp, send_otp_email, send_verification_otp
from ..security import verify_password


auth_bp = Blueprint("auth", __name__)

OTP_STATE_STORE = {}


def _store_otp_state(context, otp, token=None):
    token = token or secrets.token_urlsafe(24)
    OTP_STATE_STORE[token] = {
        "otp": otp,
        "otp_time": datetime.now().isoformat(),
        "context": context,
    }
    return token


def _get_otp_state(token):
    if not token:
        return None
    return OTP_STATE_STORE.get(token)


def _update_otp_state(token, context, otp):
    if not token:
        return None
    OTP_STATE_STORE[token] = {
        "otp": otp,
        "otp_time": datetime.now().isoformat(),
        "context": context,
    }
    return token


def _clear_otp_state(token):
    if token:
        OTP_STATE_STORE.pop(token, None)


def _get_client_otp_token(data=None):
    data = data or {}
    return (
        data.get("otp_session_token")
        or request.cookies.get("otp_session_token")
        or session.get("otp_session_token")
    )


def _resolve_otp_data(data=None):
    data = data or {}
    token = _get_client_otp_token(data)
    state = _get_otp_state(token) if token else None
    if state:
        return token, state

    if "pending_voter_id" in session and "otp" in session:
        return None, {
            "otp": session.get("otp"),
            "otp_time": session.get("otp_time"),
            "context": {
                "kind": "voter",
                "voter_id": session.get("pending_voter_id"),
                "voter_name": session.get("pending_voter_name"),
                "voter_email": session.get("pending_voter_email"),
            },
        }

    return None, None


@auth_bp.route("/api/auth/status", methods=["GET"])
def check_auth_status():
    if "role" in session:
        return jsonify({"authenticated": True, "role": session.get("role"), "name": session.get("voter_name", session.get("admin_username", ""))})
    return jsonify({"authenticated": False})


# DEBUG ENDPOINT - Remove in production
@auth_bp.route("/api/debug/otp", methods=["GET"])
def debug_get_otp():
    print(f"DEBUG: Session data: {dict(session)}")
    if "otp" in session and "pending_voter_id" in session:
        return jsonify({"otp": session.get("otp"), "voter_id": session.get("pending_voter_id")})
    return jsonify({"error": "No active OTP session", "session_keys": list(session.keys())}), 400


# DEBUG ENDPOINT - Check voter session
@auth_bp.route("/api/debug/session", methods=["GET"])
def debug_get_session():
    print(f"DEBUG: Full session: {dict(session)}")
    return jsonify({
        "role": session.get("role"),
        "voter_id": session.get("voter_id"),
        "voter_name": session.get("voter_name"),
        "all_keys": list(session.keys())
    })


@auth_bp.route("/api/voter/login", methods=["POST"])
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
    context = {
        "kind": "voter",
        "voter_id": voter["voter_id"],
        "voter_name": voter["name"],
        "voter_email": voter.get("email", ""),
    }
    token = _store_otp_state(context, otp)
    session["pending_voter_id"] = voter["voter_id"]
    session["pending_voter_name"] = voter["name"]
    session["pending_voter_email"] = voter.get("email", "")
    session["otp_session_token"] = token

    send_otp_email(voter.get("email", ""), voter.get("name", ""), otp, "voter")
    response = jsonify({"message": "OTP sent successfully.", "requires_otp": True, "fallback_otp": otp, "otp_session_token": token})
    response.set_cookie("otp_session_token", token, httponly=True, samesite="Lax")
    return response


@auth_bp.route("/api/voter/otp", methods=["POST"])
def api_voter_otp():
    data = request.json or {}
    
    # DEBUG MODE: Allow "999999" as universal OTP for testing
    if data.get("otp") == "999999" and "pending_voter_id" in session:
        voter_id = session.get("pending_voter_id")
        voter_name = session.get("pending_voter_name")
        session.clear()
        session["role"] = "voter"
        session["voter_id"] = voter_id
        session["voter_name"] = voter_name
        session.modified = True  # Mark session as modified
        return jsonify({"message": "Login successful (debug mode)", "role": "voter"})
    
    token, state = _resolve_otp_data(data)
    if not state:
        return jsonify({"error": "Session missing or expired."}), 400

    if data.get("resend"):
        otp = generate_otp()
        context = state.get("context", {})
        token = _update_otp_state(token or _get_client_otp_token(data), context, otp) or token
        if token:
            session["otp_session_token"] = token
        send_otp_email(context.get("voter_email", ""), context.get("voter_name", "Voter"), otp, "voter")
        response = jsonify({"message": "New OTP sent.", "fallback_otp": otp, "otp_session_token": token})
        if token:
            response.set_cookie("otp_session_token", token, httponly=True, samesite="Lax")
        return response

    entered_otp = data.get("otp", "").strip()
    try:
        expiry_time = datetime.fromisoformat(state["otp_time"]) + timedelta(seconds=OTP_EXPIRY_SECONDS)
    except (KeyError, ValueError):
        session.clear()
        return jsonify({"error": "Session corrupted. Please login again."}), 400

    if datetime.now() > expiry_time:
        session.clear()
        _clear_otp_state(token)
        return jsonify({"error": "OTP expired. Please login again."}), 400

    if entered_otp == state["otp"]:
        context = state.get("context", {})
        voter_id = context.get("voter_id")
        voter_name = context.get("voter_name")
        
        # Get fallback values before clearing session
        if not voter_id:
            voter_id = session.get("pending_voter_id")
        if not voter_name:
            voter_name = session.get("pending_voter_name")
        
        _clear_otp_state(token)
        session.clear()
        
        # Set new session data
        session["role"] = "voter"
        session["voter_id"] = voter_id
        session["voter_name"] = voter_name
        session.modified = True  # Mark session as modified to ensure it's saved
        
        return jsonify({"message": "Login successful", "role": "voter"})

    return jsonify({"error": "Incorrect OTP."}), 401


@auth_bp.route("/api/admin/login", methods=["POST"])
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


@auth_bp.route("/api/admin/otp", methods=["POST"])
def api_admin_otp():
    if "pending_admin_username" not in session or "otp" not in session:
        return jsonify({"error": "Session missing or expired."}), 400

    data = request.json or {}
    if data.get("resend"):
        otp = generate_otp()
        session["otp"] = otp
        session["otp_time"] = datetime.now().isoformat()
        send_otp_email(session.get("pending_admin_email", ""), session.get("pending_admin_username", "Admin"), otp, "admin")
        return jsonify({"message": "New OTP sent.", "fallback_otp": otp})

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
        admin_username = session.get("pending_admin_username", "admin")
        
        session.clear()
        
        # Set new session data
        session["role"] = "admin"
        session["admin_username"] = admin_username
        
        response = make_response(jsonify({"message": "Login successful", "role": "admin"}))
        return response

    return jsonify({"error": "Incorrect OTP."}), 401


@auth_bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out successfully."})
