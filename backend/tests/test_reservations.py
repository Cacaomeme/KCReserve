"""Tests for reservation APIs."""

from __future__ import annotations

from datetime import datetime, timedelta

from tests.utils import register_user_and_get_token, seed_whitelist


def _reservation_payload(**overrides):
    now = datetime.utcnow()
    payload = {
        "purpose": "登山チームの集まり",
        "description": "テスト予約",
        "attendeeCount": 4,
        "allowAdditionalMembers": True,
        "visibility": "public",
        "startTime": (now + timedelta(days=1)).isoformat(),
        "endTime": (now + timedelta(days=2)).isoformat(),
    }
    payload.update(overrides)
    return payload


def test_create_reservation_requires_auth(client):
    response = client.post("/api/reservations", json=_reservation_payload())
    assert response.status_code == 401


def test_user_can_create_and_view_their_reservation(client):
    token = register_user_and_get_token(
        client,
        email="member3@example.com",
        password="Secret123!",
        is_admin=False,
    )

    headers = {"Authorization": f"Bearer {token}"}
    create_resp = client.post("/api/reservations", headers=headers, json=_reservation_payload())
    assert create_resp.status_code == 201
    reservation = create_resp.get_json()["reservation"]
    assert reservation["status"] == "pending"

    mine_resp = client.get("/api/reservations/mine", headers=headers)
    assert mine_resp.status_code == 200
    mine_list = mine_resp.get_json()["reservations"]
    assert len(mine_list) == 1
    assert mine_list[0]["purpose"] == "登山チームの集まり"


def test_admin_can_approve_and_public_list_shows_it(client):
    admin_token = register_user_and_get_token(
        client,
        email="admin2@example.com",
        password="Secret123!",
        is_admin=True,
    )
    user_token = register_user_and_get_token(
        client,
        email="member4@example.com",
        password="Secret123!",
        is_admin=False,
    )

    user_headers = {"Authorization": f"Bearer {user_token}"}
    create_resp = client.post("/api/reservations", headers=user_headers, json=_reservation_payload())
    reservation_id = create_resp.get_json()["reservation"]["id"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    approve_resp = client.patch(
        f"/api/admin/reservations/{reservation_id}/status",
        headers=admin_headers,
        json={"status": "approved", "visibility": "anonymous"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.get_json()["reservation"]["status"] == "approved"
    assert approve_resp.get_json()["reservation"]["visibility"] == "anonymous"

    public_resp = client.get("/api/reservations")
    reservations = public_resp.get_json()["reservations"]
    assert len(reservations) == 1
    returned = reservations[0]
    assert returned["status"] == "approved"
    assert returned["purpose"] is None  # anonymous hides details

    # Admin listing should show details and pending ones when include_all flag applies
    admin_list = client.get("/api/reservations", headers=admin_headers)
    admin_reservations = admin_list.get_json()["reservations"]
    assert len(admin_reservations) == 1
    assert admin_reservations[0]["purpose"] == "登山チームの集まり"


def test_reservation_filters_by_visibility_and_date(client):
    admin_token = register_user_and_get_token(
        client,
        email="admin3@example.com",
        password="Secret123!",
        is_admin=True,
    )
    member_token = register_user_and_get_token(
        client,
        email="member5@example.com",
        password="Secret123!",
        is_admin=False,
    )

    headers = {"Authorization": f"Bearer {member_token}"}
    future_payload = _reservation_payload(
        startTime=(datetime.utcnow() + timedelta(days=10)).isoformat(),
        endTime=(datetime.utcnow() + timedelta(days=11)).isoformat(),
        visibility="public",
    )
    past_payload = _reservation_payload(
        startTime=(datetime.utcnow() - timedelta(days=5)).isoformat(),
        endTime=(datetime.utcnow() - timedelta(days=4)).isoformat(),
        visibility="anonymous",
    )

    # Create two reservations and approve them with differing visibility values
    future_id = client.post("/api/reservations", headers=headers, json=future_payload).get_json()[
        "reservation"
    ]["id"]
    past_id = client.post("/api/reservations", headers=headers, json=past_payload).get_json()[
        "reservation"
    ]["id"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    client.patch(
        f"/api/admin/reservations/{future_id}/status",
        headers=admin_headers,
        json={"status": "approved", "visibility": "public"},
    )
    client.patch(
        f"/api/admin/reservations/{past_id}/status",
        headers=admin_headers,
        json={"status": "approved", "visibility": "anonymous"},
    )

    # Filter only public
    public_resp = client.get("/api/reservations", query_string={"visibility": "public"})
    public_items = public_resp.get_json()["reservations"]
    assert len(public_items) == 1
    assert public_items[0]["visibility"] == "public"

    # Filter by date range capturing only the past reservation
    past_resp = client.get(
        "/api/reservations",
        query_string={
            "start": (datetime.utcnow() - timedelta(days=6)).isoformat(),
            "end": (datetime.utcnow() - timedelta(days=3)).isoformat(),
        },
    )
    past_items = past_resp.get_json()["reservations"]
    assert len(past_items) == 1
    assert past_items[0]["visibility"] == "anonymous"


def test_calendar_endpoint_masks_titles_for_anonymous(client):
    admin_token = register_user_and_get_token(
        client,
        email="admin4@example.com",
        password="Secret123!",
        is_admin=True,
    )
    member_token = register_user_and_get_token(
        client,
        email="member6@example.com",
        password="Secret123!",
        is_admin=False,
    )

    headers = {"Authorization": f"Bearer {member_token}"}
    public_id = client.post("/api/reservations", headers=headers, json=_reservation_payload()).get_json()[
        "reservation"
    ]["id"]
    anonymous_payload = _reservation_payload(visibility="anonymous", purpose="秘密のイベント")
    anon_id = client.post("/api/reservations", headers=headers, json=anonymous_payload).get_json()[
        "reservation"
    ]["id"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    client.patch(
        f"/api/admin/reservations/{public_id}/status",
        headers=admin_headers,
        json={"status": "approved", "visibility": "public"},
    )
    client.patch(
        f"/api/admin/reservations/{anon_id}/status",
        headers=admin_headers,
        json={"status": "approved", "visibility": "anonymous"},
    )

    # Public view without token hides anonymous title
    calendar_resp = client.get("/api/reservations/calendar")
    events = {event["id"]: event for event in calendar_resp.get_json()["events"]}
    assert events[public_id]["title"] is not None  # public reservation keeps title
    assert events[anon_id]["title"] is None        # anonymous hides title

    # Owner sees their anonymous title
    owner_resp = client.get(
        "/api/reservations/calendar",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    owner_events = {event["id"]: event for event in owner_resp.get_json()["events"]}
    assert owner_events[anon_id]["title"] == "秘密のイベント"

    # Admin also sees titles
    admin_resp = client.get(
        "/api/reservations/calendar",
        headers=admin_headers,
    )
    admin_events = {event["id"]: event for event in admin_resp.get_json()["events"]}
    assert admin_events[anon_id]["title"] == "秘密のイベント"
