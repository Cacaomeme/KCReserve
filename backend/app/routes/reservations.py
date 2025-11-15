"""Reservation-related API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.database import session_scope
from app.models.reservation import Reservation, ReservationStatus, ReservationVisibility
from app.schemas import serialize_reservation

reservations_bp = Blueprint("reservations", __name__)
reservations_admin_bp = Blueprint("reservations_admin", __name__)


def _calendar_payload(reservation: Reservation, *, include_purpose: bool) -> dict[str, object]:
    return {
        "id": reservation.id,
        "start": reservation.start_time.isoformat() if reservation.start_time else None,
        "end": reservation.end_time.isoformat() if reservation.end_time else None,
        "visibility": reservation.visibility.value,
        "status": reservation.status.value,
        "title": reservation.purpose if include_purpose else None,
    }


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _visibility_from_payload(value: str | None) -> ReservationVisibility | None:
    if value is None:
        return None
    try:
        return ReservationVisibility(value)
    except ValueError:
        return None


def _status_from_payload(value: str | None) -> ReservationStatus | None:
    if value is None:
        return None
    try:
        return ReservationStatus(value)
    except ValueError:
        return None


def _is_admin(claims: dict | None) -> bool:
    return bool(claims and claims.get("is_admin"))


def _apply_filters(query, params: dict[str, Any]):
    start = _parse_datetime(params.get("start"))
    end = _parse_datetime(params.get("end"))
    visibility = _visibility_from_payload(params.get("visibility"))

    if start:
        query = query.filter(Reservation.end_time >= start)
    if end:
        query = query.filter(Reservation.start_time <= end)
    if visibility:
        query = query.filter(Reservation.visibility == visibility)
    return query


@reservations_bp.post("/api/reservations")
@jwt_required()
def create_reservation():
    user_id = get_jwt_identity()
    payload = request.get_json() or {}

    start_time = _parse_datetime(payload.get("startTime"))
    end_time = _parse_datetime(payload.get("endTime"))
    visibility = _visibility_from_payload(payload.get("visibility")) or ReservationVisibility.PUBLIC
    purpose = (payload.get("purpose") or "").strip()

    errors = []
    if not start_time or not end_time:
        errors.append("startTime と endTime はISO8601形式で指定してください")
    elif end_time <= start_time:
        errors.append("endTime は startTime より後である必要があります")

    if not purpose:
        errors.append("purpose は必須です")

    if errors:
        return jsonify({"message": "; ".join(errors)}), HTTPStatus.BAD_REQUEST

    reservation = Reservation(
        user_id=int(user_id),
        visibility=visibility,
        purpose=purpose,
        description=payload.get("description"),
        attendee_count=int(payload.get("attendeeCount", 1)),
        allow_additional_members=bool(payload.get("allowAdditionalMembers", False)),
        start_time=start_time,
        end_time=end_time,
    )

    with session_scope() as session:
        session.add(reservation)
        session.flush()
        response_body = serialize_reservation(reservation, include_private=True)

    return jsonify({"reservation": response_body}), HTTPStatus.CREATED


@reservations_bp.get("/api/reservations")
@jwt_required(optional=True)
def list_reservations():
    claims = get_jwt()
    identity = get_jwt_identity()
    include_all = _is_admin(claims)

    params = {
        "start": request.args.get("start"),
        "end": request.args.get("end"),
        "visibility": request.args.get("visibility"),
    }

    with session_scope() as session:
        query = session.query(Reservation).order_by(Reservation.start_time.asc())
        if not include_all:
            query = query.filter(Reservation.status == ReservationStatus.APPROVED)

        query = _apply_filters(query, params)

        reservations = query.all()
        serialized = []
        for reservation in reservations:
            include_private = include_all or (identity is not None and int(identity) == reservation.user_id)
            serialized.append(serialize_reservation(reservation, include_private=include_private))

    return jsonify({"reservations": serialized}), HTTPStatus.OK


@reservations_bp.get("/api/reservations/calendar")
@jwt_required(optional=True)
def calendar_reservations():
    claims = get_jwt()
    identity = get_jwt_identity()
    include_all = _is_admin(claims)

    params = {
        "start": request.args.get("start"),
        "end": request.args.get("end"),
        "visibility": request.args.get("visibility"),
    }

    with session_scope() as session:
        query = session.query(Reservation).order_by(Reservation.start_time.asc())
        if not include_all:
            query = query.filter(Reservation.status == ReservationStatus.APPROVED)
        query = _apply_filters(query, params)
        reservations = query.all()

        viewer_id = int(identity) if identity is not None else None
        events = []
        for reservation in reservations:
            include_purpose = (
                include_all
                or (viewer_id is not None and viewer_id == reservation.user_id)
                or reservation.visibility == ReservationVisibility.PUBLIC
            )
            events.append(_calendar_payload(reservation, include_purpose=include_purpose))

    return jsonify({"events": events}), HTTPStatus.OK


@reservations_bp.get("/api/reservations/mine")
@jwt_required()
def list_my_reservations():
    identity = get_jwt_identity()
    with session_scope() as session:
        reservations = (
            session.query(Reservation)
            .filter(Reservation.user_id == int(identity))
            .order_by(Reservation.start_time.desc())
            .all()
        )
        serialized = [serialize_reservation(r, include_private=True) for r in reservations]
    return jsonify({"reservations": serialized}), HTTPStatus.OK


@reservations_admin_bp.patch("/api/admin/reservations/<int:reservation_id>/status")
@jwt_required()
def update_reservation_status(reservation_id: int):
    claims = get_jwt()
    if not _is_admin(claims):
        return jsonify({"message": "管理者権限が必要です"}), HTTPStatus.FORBIDDEN

    payload = request.get_json() or {}
    new_status = _status_from_payload(payload.get("status"))
    new_visibility = _visibility_from_payload(payload.get("visibility"))

    if new_status is None:
        return jsonify({"message": "status は必須です"}), HTTPStatus.BAD_REQUEST

    with session_scope() as session:
        reservation = session.get(Reservation, reservation_id)
        if reservation is None:
            return jsonify({"message": "予約が見つかりません"}), HTTPStatus.NOT_FOUND

        reservation.status = new_status
        if new_visibility is not None:
            reservation.visibility = new_visibility

        reservation.updated_at = datetime.utcnow()
        session.add(reservation)
        session.flush()

        return jsonify({"reservation": serialize_reservation(reservation, include_private=True)}), HTTPStatus.OK