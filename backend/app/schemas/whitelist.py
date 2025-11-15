"""Whitelist serialization utilities."""

from __future__ import annotations

from app.models import WhitelistEntry


def serialize_whitelist_entry(entry: WhitelistEntry) -> dict[str, object]:
    """Return a serializable representation of a whitelist entry."""
    return {
        "id": entry.id,
        "email": entry.email,
        "displayName": entry.display_name,
        "isAdminDefault": entry.is_admin_default,
        "addedByUserId": entry.added_by_user_id,
        "createdAt": entry.created_at.isoformat() if entry.created_at else None,
    }
