"""Authentication and account management endpoints."""

from __future__ import annotations

from datetime import datetime
from functools import wraps
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import session_scope
from app.models import User, WhitelistEntry
from app.schemas import serialize_user, serialize_whitelist_entry

auth_bp = Blueprint("auth", __name__)
admin_bp = Blueprint("admin", __name__)


def _normalize_email(raw_email: str | None) -> str:
    return (raw_email or "").strip().lower()


def _issue_token(user: User) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"is_admin": user.is_admin})


def admin_required(fn):
    """Decorator to restrict endpoints to admin users."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if not claims.get("is_admin"):
            return jsonify({"message": "管理者権限が必要です"}), HTTPStatus.FORBIDDEN
        return fn(*args, **kwargs)

    return wrapper


@auth_bp.post("/api/auth/register")
def register():
    data = request.get_json() or {}
    email = _normalize_email(data.get("email"))
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"message": "email と password は必須です"}), HTTPStatus.BAD_REQUEST

    with session_scope() as session:
        whitelist_entry = session.query(WhitelistEntry).filter(WhitelistEntry.email == email).first()
        if whitelist_entry is None:
            return jsonify({"message": "ホワイトリストに登録されていません"}), HTTPStatus.FORBIDDEN

        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            return jsonify({"message": "既にユーザーが存在します"}), HTTPStatus.CONFLICT

        user = User(
            email=email,
            hashed_password=generate_password_hash(password),
            is_admin=whitelist_entry.is_admin_default,
            is_active=True,
        )
        session.add(user)
        session.flush()

        token = _issue_token(user)

        return (
            jsonify({"user": serialize_user(user), "accessToken": token}),
            HTTPStatus.CREATED,
        )


@auth_bp.post("/api/auth/login")
def login():
    data = request.get_json() or {}
    email = _normalize_email(data.get("email"))
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"message": "email と password は必須です"}), HTTPStatus.BAD_REQUEST

    with session_scope() as session:
        user = session.query(User).filter(User.email == email).first()
        if user is None or not check_password_hash(user.hashed_password, password):
            return jsonify({"message": "メールアドレスまたはパスワードが違います"}), HTTPStatus.UNAUTHORIZED
        if not user.is_active:
            return jsonify({"message": "アカウントが無効化されています"}), HTTPStatus.FORBIDDEN

        token = _issue_token(user)
        return jsonify({"user": serialize_user(user), "accessToken": token}), HTTPStatus.OK


@auth_bp.get("/api/auth/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    with session_scope() as session:
        user = session.get(User, int(user_id)) if user_id is not None else None
        if user is None:
            return jsonify({"message": "ユーザーが存在しません"}), HTTPStatus.NOT_FOUND

        claims = get_jwt()
        return (
            jsonify({
                "user": serialize_user(user),
                "claims": {"isAdmin": claims.get("is_admin", False)},
            }),
            HTTPStatus.OK,
        )


@auth_bp.get("/api/auth/whitelist-check")
def whitelist_check():
    email = _normalize_email(request.args.get("email"))
    if not email:
        return jsonify({"allowed": False, "message": "email クエリパラメータが必要です"}), HTTPStatus.BAD_REQUEST

    with session_scope() as session:
        entry = session.query(WhitelistEntry).filter(WhitelistEntry.email == email).first()
        if entry is None:
            return jsonify({"allowed": False}), HTTPStatus.OK

        return jsonify({"allowed": True, "defaultAdmin": entry.is_admin_default}), HTTPStatus.OK


@admin_bp.get("/api/admin/whitelist")
@admin_required
def list_whitelist():
    with session_scope() as session:
        entries = (
            session.query(WhitelistEntry)
            .order_by(WhitelistEntry.created_at.desc())
            .all()
        )
        return jsonify({"entries": [serialize_whitelist_entry(e) for e in entries]}), HTTPStatus.OK


@admin_bp.post("/api/admin/whitelist")
@admin_required
def add_whitelist_entry():
    data = request.get_json() or {}
    email = _normalize_email(data.get("email"))
    display_name = data.get("displayName")
    is_admin_default = bool(data.get("isAdminDefault", False))

    if not email:
        return jsonify({"message": "email は必須です"}), HTTPStatus.BAD_REQUEST

    user_id = get_jwt_identity()

    with session_scope() as session:
        exists = session.query(WhitelistEntry).filter(WhitelistEntry.email == email).first()
        if exists:
            return jsonify({"message": "既にホワイトリストに登録されています"}), HTTPStatus.CONFLICT

        entry = WhitelistEntry(
            email=email,
            display_name=display_name,
            is_admin_default=is_admin_default,
            added_by_user_id=int(user_id) if user_id else None,
            created_at=datetime.utcnow(),
        )
        session.add(entry)
        session.flush()

        return jsonify({"entry": serialize_whitelist_entry(entry)}), HTTPStatus.CREATED


@admin_bp.delete("/api/admin/whitelist/<int:entry_id>")
@admin_required
def delete_whitelist_entry(entry_id: int):
    with session_scope() as session:
        entry = session.get(WhitelistEntry, entry_id)
        if entry is None:
            return jsonify({"message": "指定されたIDが見つかりません"}), HTTPStatus.NOT_FOUND

        session.delete(entry)
        return ("", HTTPStatus.NO_CONTENT)
