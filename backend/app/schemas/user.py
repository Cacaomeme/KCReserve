"""Serialization helpers for user objects."""

from __future__ import annotations

from app.models import User


def serialize_user(user: User) -> dict[str, object]:
    """Return a JSON-serializable representation of a user."""
    return {
        "id": user.id,
        "email": user.email,
        "isAdmin": user.is_admin,
        "isActive": user.is_active,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "updatedAt": user.updated_at.isoformat() if user.updated_at else None,
    }
