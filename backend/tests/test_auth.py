"""Tests for authentication endpoints."""

from __future__ import annotations

from datetime import datetime

from app.database import session_scope
from app.models import WhitelistEntry


def seed_whitelist(email: str, is_admin: bool = False) -> None:
    with session_scope() as session:
        entry = WhitelistEntry(
            email=email,
            display_name="Tester",
            is_admin_default=is_admin,
            created_at=datetime.utcnow(),
        )
        session.add(entry)


def register_user_and_get_token(client, email: str, password: str, *, is_admin: bool) -> str:
    seed_whitelist(email, is_admin=is_admin)
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.get_json()["accessToken"]


def test_registration_requires_whitelist(client) -> None:
    payload = {"email": "nope@example.com", "password": "secret123"}
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 403
    assert response.json["message"].startswith("ホワイトリスト")


def test_register_and_login_flow(client) -> None:
    email = "member@example.com"
    password = "Secret123!"

    seed_whitelist(email, is_admin=True)

    register_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )

    assert register_response.status_code == 201
    register_body = register_response.get_json()
    assert register_body["user"]["email"] == email
    assert register_body["user"]["isAdmin"] is True
    assert register_body["accessToken"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    access_token = login_response.get_json()["accessToken"]

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    me_body = me_response.get_json()
    assert me_body["user"]["email"] == email
    assert me_body["claims"]["isAdmin"] is True


def test_admin_whitelist_requires_admin_claim(client) -> None:
    member_token = register_user_and_get_token(
        client,
        email="member2@example.com",
        password="Secret123!",
        is_admin=False,
    )

    response = client.post(
        "/api/admin/whitelist",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"email": "new@example.com"},
    )

    assert response.status_code == 403
    assert "管理者" in response.get_json()["message"]


def test_admin_can_manage_whitelist_entries(client) -> None:
    admin_token = register_user_and_get_token(
        client,
        email="admin@example.com",
        password="Secret123!",
        is_admin=True,
    )

    headers = {"Authorization": f"Bearer {admin_token}"}

    create_resp = client.post(
        "/api/admin/whitelist",
        headers=headers,
        json={
            "email": "guest@example.com",
            "displayName": "Guest",
            "isAdminDefault": False,
        },
    )

    assert create_resp.status_code == 201
    entry_id = create_resp.get_json()["entry"]["id"]

    list_resp = client.get("/api/admin/whitelist", headers=headers)
    assert list_resp.status_code == 200
    entries = list_resp.get_json()["entries"]
    assert any(entry["email"] == "guest@example.com" for entry in entries)

    delete_resp = client.delete(f"/api/admin/whitelist/{entry_id}", headers=headers)
    assert delete_resp.status_code == 204

    list_resp2 = client.get("/api/admin/whitelist", headers=headers)
    emails_after = [entry["email"] for entry in list_resp2.get_json()["entries"]]
    assert "guest@example.com" not in emails_after
