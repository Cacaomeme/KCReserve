"""Application settings loader."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv

# Load variables from a local .env if present so developers can override defaults.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    secret_key: str
    jwt_secret_key: str
    database_url: str
    allowed_origins: list[str]
    access_token_expires_minutes: int
    refresh_token_expires_days: int
    refresh_cookie_secure: bool
    refresh_cookie_samesite: str
    mail_server: str | None
    mail_port: int
    mail_username: str | None
    mail_password: str | None
    mail_use_tls: bool
    mail_default_sender: str | None
    sendgrid_api_key: str | None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    root_dir = Path(__file__).resolve().parent.parent
    default_db = root_dir / "instance" / "app.db"
    os.makedirs(default_db.parent, exist_ok=True)

    secret = os.getenv("SECRET_KEY", "dev-secret-key")
    jwt_secret = os.getenv("JWT_SECRET_KEY", secret)
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{default_db}")
    cors_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

    def _get_int(name: str, default: int) -> int:
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            return max(1, int(raw))
        except ValueError:
            return default

    def _get_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    access_token_minutes = _get_int("JWT_ACCESS_TOKEN_MINUTES", 15)
    refresh_token_days = _get_int("JWT_REFRESH_TOKEN_DAYS", 1)
    refresh_cookie_secure = _get_bool("JWT_REFRESH_COOKIE_SECURE", False)
    refresh_cookie_samesite = os.getenv("JWT_REFRESH_COOKIE_SAMESITE", "Lax")

    mail_server = os.getenv("MAIL_SERVER")
    mail_port = _get_int("MAIL_PORT", 587)
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")
    mail_use_tls = _get_bool("MAIL_USE_TLS", True)
    mail_default_sender = os.getenv("MAIL_DEFAULT_SENDER")
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

    return Settings(
        secret_key=secret,
        jwt_secret_key=jwt_secret,
        database_url=database_url,
        allowed_origins=cors_origins or ["http://localhost:5173"],
        access_token_expires_minutes=access_token_minutes,
        refresh_token_expires_days=refresh_token_days,
        refresh_cookie_secure=refresh_cookie_secure,
        refresh_cookie_samesite=refresh_cookie_samesite,
        mail_server=mail_server,
        mail_port=mail_port,
        mail_username=mail_username,
        mail_password=mail_password,
        mail_use_tls=mail_use_tls,
        mail_default_sender=mail_default_sender,
        sendgrid_api_key=sendgrid_api_key,
    )
