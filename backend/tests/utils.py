"""Helper functions shared across API tests."""

from __future__ import annotations

from datetime import datetime

from app.database import session_scope
from app.models import WhitelistEntry


def seed_whitelist(email: str, *, is_admin: bool = False) -> None:
    with session_scope() as session:
        entry = WhitelistEntry(
            email=email,
            display_name="Tester",
            is_admin_default=is_admin,
            created_at=datetime.utcnow(),
        )
        session.add(entry)


def register_user_and_get_token(client, *, email: str, password: str, is_admin: bool) -> str:
    """Seed whitelist, register a user, and return its JWT token."""
    seed_whitelist(email, is_admin=is_admin)
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    return body["accessToken"]
