"""Application factory for the mountain hut reservation backend."""

from datetime import timedelta

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .config import get_settings
from .routes.auth import admin_bp, auth_bp
from .routes.health import health_bp
from .routes.reservations import reservations_admin_bp, reservations_bp
from .routes.system_settings import bp as system_settings_bp

# Import models so Alembic autogenerate can discover metadata.
from . import models  # noqa: F401

jwt = JWTManager()


def create_app() -> Flask:
    """Create and configure the Flask application instance."""
    settings = get_settings()

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=settings.jwt_secret_key,
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=settings.access_token_expires_minutes),
        JWT_TOKEN_LOCATION=("headers",),
    )

    CORS(app, origins=settings.allowed_origins, supports_credentials=True)
    jwt.init_app(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(reservations_admin_bp)
    app.register_blueprint(system_settings_bp)

    @app.get("/api/ping")
    def ping() -> tuple[dict[str, str], int]:
        """Lightweight endpoint useful for uptime checks."""
        return {"message": "pong"}, 200

    return app
