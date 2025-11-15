"""Application factory for the mountain hut reservation backend."""

from flask import Flask
from flask_cors import CORS

from .config import get_settings
from .routes.health import health_bp

# Import models so Alembic autogenerate can discover metadata.
from . import models  # noqa: F401


def create_app() -> Flask:
    """Create and configure the Flask application instance."""
    settings = get_settings()

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    CORS(app, origins=settings.allowed_origins, supports_credentials=True)

    app.register_blueprint(health_bp)

    @app.get("/api/ping")
    def ping() -> tuple[dict[str, str], int]:
        """Lightweight endpoint useful for uptime checks."""
        return {"message": "pong"}, 200

    return app
