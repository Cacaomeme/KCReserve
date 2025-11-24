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
    refresh_token_days = _get_int("JWT_REFRESH_TOKEN_DAYS", 14)
    refresh_cookie_secure = _get_bool("JWT_REFRESH_COOKIE_SECURE", False)
    refresh_cookie_samesite = os.getenv("JWT_REFRESH_COOKIE_SAMESITE", "Lax")

    return Settings(
        secret_key=secret,
        jwt_secret_key=jwt_secret,
        database_url=database_url,
        allowed_origins=cors_origins or ["http://localhost:5173"],
        access_token_expires_minutes=access_token_minutes,
        refresh_token_expires_days=refresh_token_days,
        refresh_cookie_secure=refresh_cookie_secure,
        refresh_cookie_samesite=refresh_cookie_samesite,
    )
