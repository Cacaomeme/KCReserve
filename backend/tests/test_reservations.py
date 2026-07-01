"""Tests for reservation APIs."""

from __future__ import annotations

from datetime import datetime, timedelta

from tests.utils import register_user_and_get_token, seed_whitelist


def _reservation_payload(**overrides):
    now = datetime.utcnow()
    payload = {
        "purpose": "登山チームの集まり",
        "displayMessage": "登山チーム",
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


def test_create_reservation_sends_received_notification_when_enabled(client, monkeypatch):
    received_notifications = []

    def fake_send(reservation_id):
        received_notifications.append(reservation_id)

    monkeypatch.setattr(
        "app.routes.reservations.send_reservation_received_notification",
        fake_send,
    )

    token = register_user_and_get_token(
        client,
        email="member-received@example.com",
        password="Secret123!",
        is_admin=False,
    )

    create_resp = client.post(
        "/api/reservations",
        headers={"Authorization": f"Bearer {token}"},
        json=_reservation_payload(notifyApplicant=True),
    )

    assert create_resp.status_code == 201
    reservation_id = create_resp.get_json()["reservation"]["id"]
    assert received_notifications == [reservation_id]


def test_create_reservation_skips_received_notification_when_disabled(client, monkeypatch):
    received_notifications = []

    def fake_send(reservation_id):
        received_notifications.append(reservation_id)

    monkeypatch.setattr(
        "app.routes.reservations.send_reservation_received_notification",
        fake_send,
    )

    token = register_user_and_get_token(
        client,
        email="member-no-received@example.com",
        password="Secret123!",
        is_admin=False,
    )

    create_resp = client.post(
        "/api/reservations",
        headers={"Authorization": f"Bearer {token}"},
        json=_reservation_payload(notifyApplicant=False),
    )

    assert create_resp.status_code == 201
    assert create_resp.get_json()["reservation"]["notifyApplicant"] is False
    assert received_notifications == []


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
    approved_reservation = approve_resp.get_json()["reservation"]
    assert approved_reservation["status"] == "approved"
    assert approved_reservation["visibility"] == "anonymous"
    assert approved_reservation["statusUpdatedBy"]["email"] == "admin2@example.com"

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
    assert admin_reservations[0]["statusUpdatedBy"]["email"] == "admin2@example.com"


def test_admin_status_update_notifies_applicant_when_enabled(client, monkeypatch):
    sent_notifications = []

    def fake_send(reservation_id, previous_status=None):
        sent_notifications.append((reservation_id, previous_status))

    monkeypatch.setattr(
        "app.routes.reservations.send_reservation_status_notification",
        fake_send,
    )

    admin_token = register_user_and_get_token(
        client,
        email="admin-notify@example.com",
        password="Secret123!",
        is_admin=True,
    )
    user_token = register_user_and_get_token(
        client,
        email="member-notify@example.com",
        password="Secret123!",
        is_admin=False,
    )

    create_resp = client.post(
        "/api/reservations",
        headers={"Authorization": f"Bearer {user_token}"},
        json=_reservation_payload(notifyApplicant=True),
    )
    reservation_id = create_resp.get_json()["reservation"]["id"]

    approve_resp = client.patch(
        f"/api/admin/reservations/{reservation_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "approved"},
    )

    assert approve_resp.status_code == 200
    assert sent_notifications == [(reservation_id, "pending")]


def test_admin_export_csv_includes_status_updated_by(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.reservations.send_reservation_status_notification",
        lambda reservation_id, previous_status=None: None,
    )

    admin_token = register_user_and_get_token(
        client,
        email="admin-export@example.com",
        password="Secret123!",
        is_admin=True,
    )
    user_token = register_user_and_get_token(
        client,
        email="member-export@example.com",
        password="Secret123!",
        is_admin=False,
    )

    create_resp = client.post(
        "/api/reservations",
        headers={"Authorization": f"Bearer {user_token}"},
        json=_reservation_payload(),
    )
    reservation_id = create_resp.get_json()["reservation"]["id"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    client.patch(
        f"/api/admin/reservations/{reservation_id}/status",
        headers=admin_headers,
        json={"status": "approved"},
    )

    export_resp = client.get("/api/admin/reservations/export", headers=admin_headers)
    assert export_resp.status_code == 200
    csv_text = export_resp.get_data(as_text=True)
    assert "担当者" in csv_text
    assert "承認済み,Tester,Tester,member-export@example.com" in csv_text


def test_admin_status_update_skips_applicant_notification_when_disabled(client, monkeypatch):
    sent_notifications = []

    def fake_send(reservation_id, previous_status=None):
        sent_notifications.append((reservation_id, previous_status))

    monkeypatch.setattr(
        "app.routes.reservations.send_reservation_status_notification",
        fake_send,
    )

    admin_token = register_user_and_get_token(
        client,
        email="admin-no-notify@example.com",
        password="Secret123!",
        is_admin=True,
    )
    user_token = register_user_and_get_token(
        client,
        email="member-no-notify@example.com",
        password="Secret123!",
        is_admin=False,
    )

    create_resp = client.post(
        "/api/reservations",
        headers={"Authorization": f"Bearer {user_token}"},
        json=_reservation_payload(notifyApplicant=False),
    )
    reservation = create_resp.get_json()["reservation"]
    assert reservation["notifyApplicant"] is False

    approve_resp = client.patch(
        f"/api/admin/reservations/{reservation['id']}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "approved"},
    )

    assert approve_resp.status_code == 200
    assert sent_notifications == []


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
    assert events[public_id]["title"] == "登山チーム (Tester)"  # public reservation shows calendar message
    assert events[public_id]["purpose"] == "登山チームの集まり"
    assert "displayMessage" not in events[public_id]
    assert events[anon_id]["title"] is None        # anonymous hides title

    # Owner sees their anonymous calendar title fallback and private fields
    owner_resp = client.get(
        "/api/reservations/calendar",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    owner_events = {event["id"]: event for event in owner_resp.get_json()["events"]}
    assert owner_events[anon_id]["title"] == "登山チーム"
    assert owner_events[anon_id]["purpose"] == "秘密のイベント"
    assert owner_events[anon_id]["displayMessage"] == "登山チーム"

    # Admin sees purpose but not the owner's editable calendar display message
    admin_resp = client.get(
        "/api/reservations/calendar",
        headers=admin_headers,
    )
    admin_events = {event["id"]: event for event in admin_resp.get_json()["events"]}
    assert admin_events[anon_id]["title"] == "登山チーム"
    assert admin_events[anon_id]["purpose"] == "秘密のイベント"
    assert "displayMessage" not in admin_events[anon_id]
    assert admin_events[anon_id]["statusUpdatedByDisplayName"] == "Tester"
