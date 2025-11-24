"""Reservation-related API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import or_

from app.database import session_scope
from app.models.reservation import Reservation, ReservationStatus, ReservationVisibility
from app.schemas import serialize_reservation
from app.utils.email import send_new_reservation_notification, send_cancellation_request_notification

reservations_bp = Blueprint("reservations", __name__)
reservations_admin_bp = Blueprint("reservations_admin", __name__)


def _calendar_payload(reservation: Reservation) -> dict[str, object]:
    def format_dt(dt):
        if not dt:
            return None
        if dt.tzinfo is None:
            return dt.isoformat() + 'Z'
        return dt.isoformat()

    return {
        "id": reservation.id,
        "start": format_dt(reservation.start_time),
        "end": format_dt(reservation.end_time),
        "visibility": reservation.visibility.value,
        "status": reservation.status.value,
    }


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Handle 'Z' suffix for UTC which fromisoformat doesn't support in older Python versions
        if value.endswith('Z'):
            value = value[:-1] + '+00:00'
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
        display_message=payload.get("displayMessage"),
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
        reservation_id = reservation.id

    # Send notification email to admins
    send_new_reservation_notification(reservation_id)

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
            if identity:
                query = query.filter(
                    or_(
                        Reservation.status == ReservationStatus.APPROVED,
                        Reservation.user_id == int(identity)
                    )
                )
            else:
                query = query.filter(Reservation.status == ReservationStatus.APPROVED)

        query = _apply_filters(query, params)
        reservations = query.all()

        viewer_id = int(identity) if identity is not None else None
        events = []
        for reservation in reservations:
            is_owner = viewer_id is not None and viewer_id == reservation.user_id
            
            payload = _calendar_payload(reservation)
            payload["isOwner"] = is_owner
            
            if include_all or is_owner:
                payload["title"] = reservation.purpose
                payload["description"] = reservation.description
                payload["displayMessage"] = reservation.display_message
                payload["attendeeCount"] = reservation.attendee_count
                payload["userDisplayName"] = reservation.user.display_name if reservation.user else "Unknown"
                if reservation.status == ReservationStatus.REJECTED:
                    payload["rejectionReason"] = reservation.rejection_reason
                if reservation.status in [ReservationStatus.APPROVED, ReservationStatus.CANCELLED]:
                    payload["approvalMessage"] = reservation.approval_message
                if reservation.status == ReservationStatus.CANCELLATION_REQUESTED:
                    payload["cancellationReason"] = reservation.cancellation_reason
            elif reservation.visibility == ReservationVisibility.PUBLIC:
                user_name = reservation.user.display_name if reservation.user else "Unknown"
                if user_name is None:
                    user_name = "Unknown"
                msg = reservation.display_message or "予約"
                payload["title"] = f"{msg} ({user_name})"
                payload["description"] = reservation.description
                payload["attendeeCount"] = reservation.attendee_count
                payload["userDisplayName"] = user_name
            else:
                payload["title"] = "匿名"
            
            events.append(payload)

    return jsonify({"events": events}), HTTPStatus.OK


@reservations_bp.patch("/api/reservations/<int:reservation_id>")
@jwt_required()
def update_reservation(reservation_id: int):
    user_id = get_jwt_identity()
    payload = request.get_json() or {}
    
    with session_scope() as session:
        reservation = session.get(Reservation, reservation_id)
        if reservation is None:
            return jsonify({"message": "予約が見つかりません"}), HTTPStatus.NOT_FOUND
            
        if reservation.user_id != int(user_id):
             return jsonify({"message": "権限がありません"}), HTTPStatus.FORBIDDEN

        if "description" in payload:
            reservation.description = payload["description"]
        
        if "displayMessage" in payload:
            reservation.display_message = payload["displayMessage"]
        
        if payload.get("status") == "cancellation_requested":
            if reservation.status == ReservationStatus.APPROVED:
                reservation.status = ReservationStatus.CANCELLATION_REQUESTED
                if "cancellationReason" in payload:
                    reservation.cancellation_reason = payload["cancellationReason"]
                
                # Send notification email to admins
                send_cancellation_request_notification(reservation.id)
            else:
                return jsonify({"message": "承認済みの予約のみキャンセル申請できます"}), HTTPStatus.BAD_REQUEST
            
        reservation.updated_at = datetime.utcnow()
        session.add(reservation)
        session.flush()
        
        return jsonify({"reservation": serialize_reservation(reservation, include_private=True)}), HTTPStatus.OK


@reservations_bp.get("/api/reservations/mine")
@jwt_required()
def list_my_reservations():
    user_id = get_jwt_identity()

    with session_scope() as session:
        reservations = (
            session.query(Reservation)
            .filter(Reservation.user_id == int(user_id))
            .order_by(Reservation.start_time.desc())
            .all()
        )
        serialized = [serialize_reservation(r, include_private=True) for r in reservations]

    return jsonify({"reservations": serialized}), HTTPStatus.OK


@reservations_admin_bp.get("/api/admin/reservations/pending-count")
@jwt_required()
def get_pending_count():
    claims = get_jwt()
    if not _is_admin(claims):
        return jsonify({"message": "管理者権限が必要です"}), HTTPStatus.FORBIDDEN

    with session_scope() as session:
        count = session.query(Reservation).filter(
            or_(
                Reservation.status == ReservationStatus.PENDING,
                Reservation.status == ReservationStatus.CANCELLATION_REQUESTED
            )
        ).count()

    return jsonify({"count": count}), HTTPStatus.OK


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
        
        if new_status == ReservationStatus.REJECTED:
            reservation.rejection_reason = payload.get("rejectionReason")
        elif new_status == ReservationStatus.APPROVED:
            reservation.approval_message = payload.get("approvalMessage")
        elif new_status == ReservationStatus.CANCELLED:
            reservation.approval_message = payload.get("approvalMessage")

        reservation.updated_at = datetime.utcnow()
        session.add(reservation)
        session.flush()

        return jsonify({"reservation": serialize_reservation(reservation, include_private=True)}), HTTPStatus.OK


@reservations_admin_bp.delete("/api/admin/reservations/<int:reservation_id>")
@jwt_required()
def delete_reservation(reservation_id: int):
    claims = get_jwt()
    if not _is_admin(claims):
        return jsonify({"message": "管理者権限が必要です"}), HTTPStatus.FORBIDDEN

    with session_scope() as session:
        reservation = session.get(Reservation, reservation_id)
        if reservation is None:
            return jsonify({"message": "予約が見つかりません"}), HTTPStatus.NOT_FOUND

        session.delete(reservation)
        return "", HTTPStatus.NO_CONTENT