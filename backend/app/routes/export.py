"""CSV export endpoint for reservation data (admin only)."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from http import HTTPStatus

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt, jwt_required

from app.database import session_scope
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User

export_bp = Blueprint("export", __name__)

JST = timezone(timedelta(hours=9))

STATUS_LABELS = {
    "pending": "申請中",
    "approved": "承認済み",
    "rejected": "却下",
    "cancelled": "キャンセル済み",
    "cancellation_requested": "キャンセル申請中",
}

VISIBILITY_LABELS = {
    "public": "公開",
    "anonymous": "匿名",
}


def _format_jst(dt: datetime | None) -> str:
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(JST).strftime("%Y/%m/%d %H:%M")


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@export_bp.get("/api/admin/reservations/export")
@jwt_required()
def export_reservations_csv():
    claims = get_jwt()
    if not claims.get("is_admin"):
        return {"message": "管理者権限が必要です"}, HTTPStatus.FORBIDDEN

    # Parse query parameters for filtering
    status_filter = request.args.get("status")  # e.g. "approved", "pending"
    start_from = _parse_date(request.args.get("startFrom"))
    start_to = _parse_date(request.args.get("startTo"))

    with session_scope() as session:
        query = (
            session.query(Reservation)
            .join(User, Reservation.user_id == User.id)
            .order_by(Reservation.start_time.asc())
        )

        # Apply filters
        if status_filter:
            try:
                status_enum = ReservationStatus(status_filter)
                query = query.filter(Reservation.status == status_enum)
            except ValueError:
                pass

        if start_from:
            query = query.filter(Reservation.start_time >= start_from)
        if start_to:
            query = query.filter(Reservation.start_time <= start_to)

        reservations = query.all()

        # Build CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "予約ID",
            "ステータス",
            "申請者名",
            "申請者メール",
            "目的",
            "利用開始日時",
            "利用終了日時",
            "人数",
            "公開設定",
            "詳細",
            "表示メッセージ",
            "却下理由",
            "キャンセル理由",
            "申請日時",
        ])

        # Data rows
        for r in reservations:
            writer.writerow([
                r.id,
                STATUS_LABELS.get(r.status.value, r.status.value),
                r.user.display_name or "" if r.user else "",
                r.user.email if r.user else "",
                r.purpose,
                _format_jst(r.start_time),
                _format_jst(r.end_time),
                r.attendee_count,
                VISIBILITY_LABELS.get(r.visibility.value, r.visibility.value),
                r.description or "",
                r.display_message or "",
                r.rejection_reason or "",
                r.cancellation_reason or "",
                _format_jst(r.created_at),
            ])

    csv_content = output.getvalue()

    # Add BOM for Excel compatibility with Japanese characters
    bom = "\ufeff"
    now_jst = datetime.now(JST).strftime("%Y%m%d_%H%M%S")
    filename = f"reservations_{now_jst}.csv"

    return Response(
        bom + csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
