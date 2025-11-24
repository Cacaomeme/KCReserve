"""Tests for authentication endpoints."""

from __future__ import annotations

from http.cookies import SimpleCookie

from tests.utils import register_user_and_get_token, seed_whitelist


def _extract_refresh_cookie(response) -> str | None:
    cookie = SimpleCookie()
    for header in response.headers.getlist("Set-Cookie"):
        cookie.load(header)
    morsel = cookie.get("refreshToken")
    return morsel.value if morsel else None


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
    assert _extract_refresh_cookie(register_response) is not None
    register_body = register_response.get_json()
    assert register_body["user"]["email"] == email
    assert register_body["user"]["isAdmin"] is True
    assert register_body["accessToken"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    refresh_cookie = _extract_refresh_cookie(login_response)
    assert refresh_cookie is not None
    access_token = login_response.get_json()["accessToken"]

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    me_body = me_response.get_json()
    assert me_body["user"]["email"] == email
    assert me_body["claims"]["isAdmin"] is True

    # Refresh should rotate the cookie and return a new access token.
    refresh_response = client.post(
        "/api/auth/refresh",
        environ_overrides={"HTTP_COOKIE": f"refreshToken={refresh_cookie}"},
    )
    assert refresh_response.status_code == 200
    new_cookie = _extract_refresh_cookie(refresh_response)
    assert new_cookie is not None and new_cookie != refresh_cookie
    new_access_token = refresh_response.get_json()["accessToken"]
    assert new_access_token != access_token

    # Old cookie should now be invalid.
    invalid_refresh = client.post(
        "/api/auth/refresh",
        environ_overrides={"HTTP_COOKIE": f"refreshToken={refresh_cookie}"},
    )
    assert invalid_refresh.status_code == 401


def test_logout_revokes_refresh_token(client) -> None:
    email = "member@example.com"
    password = "Secret123!"
    seed_whitelist(email, is_admin=False)

    login_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 201
    refresh_cookie = _extract_refresh_cookie(login_response)
    assert refresh_cookie is not None

    logout_response = client.post(
        "/api/auth/logout",
        environ_overrides={"HTTP_COOKIE": f"refreshToken={refresh_cookie}"},
    )
    assert logout_response.status_code == 200
    # Subsequent refresh attempts fail because the token has been revoked + cookie cleared.
    failed_refresh = client.post(
        "/api/auth/refresh",
        environ_overrides={"HTTP_COOKIE": f"refreshToken={refresh_cookie}"},
    )
    assert failed_refresh.status_code in {401, 403}


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
