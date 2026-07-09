from .admin import admin_bp
from .auth import auth_bp
from .public import public_bp
from .verification import verification_bp
from .voting import voting_bp


def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(voting_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(verification_bp)
