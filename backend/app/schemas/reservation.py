"""Reservation serialization helpers."""

from __future__ import annotations

from app.models.reservation import Reservation, ReservationVisibility


def serialize_reservation(reservation: Reservation, *, include_private: bool = False) -> dict[str, object]:
    """Serialize a reservation into JSON ready dict."""
    data = {
        "id": reservation.id,
        "userId": reservation.user_id,
        "status": reservation.status.value,
        "visibility": reservation.visibility.value,
        "purpose": reservation.purpose if include_private or reservation.visibility == ReservationVisibility.PUBLIC else None,
        "description": reservation.description if include_private and reservation.description else None,
        "attendeeCount": reservation.attendee_count,
        "allowAdditionalMembers": reservation.allow_additional_members,
        "startTime": reservation.start_time.isoformat() if reservation.start_time else None,
        "endTime": reservation.end_time.isoformat() if reservation.end_time else None,
        "createdAt": reservation.created_at.isoformat() if reservation.created_at else None,
        "updatedAt": reservation.updated_at.isoformat() if reservation.updated_at else None,
    }
    return data
