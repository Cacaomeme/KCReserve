"""Pytest fixtures and helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure the project root is available on sys.path so `import app` works when
# tests are executed via `uv run pytest`.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "tests" / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from app.config import get_settings

get_settings.cache_clear()

from app import create_app
from app.database import Base, engine


@pytest.fixture(autouse=True)
def _prepare_database():
    """Recreate the schema for each test for isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client
