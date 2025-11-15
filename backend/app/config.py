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

    return Settings(
        secret_key=secret,
        jwt_secret_key=jwt_secret,
        database_url=database_url,
        allowed_origins=cors_origins or ["http://localhost:5173"],
    )
