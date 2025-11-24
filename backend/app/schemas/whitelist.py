"""Whitelist serialization utilities."""

from __future__ import annotations

from app.models import WhitelistEntry


def serialize_whitelist_entry(entry: WhitelistEntry) -> dict[str, object]:
    """Return a serializable representation of a whitelist entry."""
    return {
        "id": entry.id,
        "email": entry.email,
        "display_name": entry.display_name,
        "is_admin_default": entry.is_admin_default,
        "added_by_user_id": entry.added_by_user_id,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }
