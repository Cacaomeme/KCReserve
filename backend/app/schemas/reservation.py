"""Reservation serialization helpers."""

from __future__ import annotations

from app.models.reservation import Reservation, ReservationVisibility
from app.schemas.user import serialize_user


def serialize_reservation(reservation: Reservation, *, include_private: bool = False) -> dict[str, object]:
    """Serialize a reservation into JSON ready dict."""
    def format_dt(dt):
        if not dt:
            return None
        # If the datetime is naive, assume it is UTC and append 'Z'
        if dt.tzinfo is None:
            return dt.isoformat() + 'Z'
        return dt.isoformat()

    data = {
        "id": reservation.id,
        "userId": reservation.user_id,
        "user": serialize_user(reservation.user) if include_private and reservation.user else None,
        "status": reservation.status.value,
        "visibility": reservation.visibility.value,
        "purpose": reservation.purpose if include_private or reservation.visibility == ReservationVisibility.PUBLIC else None,
        "displayMessage": reservation.display_message if include_private or reservation.visibility == ReservationVisibility.PUBLIC else None,
        "description": reservation.description if include_private else None,
        "cancellationReason": reservation.cancellation_reason if include_private else None,
        "rejectionReason": reservation.rejection_reason if include_private else None,
        "approvalMessage": reservation.approval_message if include_private else None,
        "attendeeCount": reservation.attendee_count,
        "allowAdditionalMembers": reservation.allow_additional_members,
        "startTime": format_dt(reservation.start_time),
        "endTime": format_dt(reservation.end_time),
        "createdAt": format_dt(reservation.created_at),
        "updatedAt": format_dt(reservation.updated_at),
    }
    return data
