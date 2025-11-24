"""Serialization helpers for user objects."""

from __future__ import annotations

from app.models import User


def serialize_user(user: User) -> dict[str, object]:
    """Return a JSON-serializable representation of a user."""
    display_name = user.display_name
    if not display_name and user.whitelist_entry:
        display_name = user.whitelist_entry.display_name

    return {
        "id": user.id,
        "email": user.email,
        "displayName": display_name,
        "isAdmin": user.is_admin,
        "isActive": user.is_active,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "updatedAt": user.updated_at.isoformat() if user.updated_at else None,
    }
