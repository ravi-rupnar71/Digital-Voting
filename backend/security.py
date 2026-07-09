from functools import wraps

from flask import jsonify, session


def verify_password(stored_password, provided_password):
    stored_password = str(stored_password or "")
    provided_password = str(provided_password or "")
    return stored_password.strip() == provided_password.strip()


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
