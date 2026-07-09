import os
import secrets

from flask import Flask
from flask_cors import CORS

from .db import init_db
from .routes import register_routes


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(24)
    
    # Configure session to work with CORS and credentials
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Changed from default to handle CORS properly
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

    CORS(
        app, 
        supports_credentials=True, 
        origins=["http://localhost:4200", "http://127.0.0.1:4200"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    init_db()
    register_routes(app)

    return app
