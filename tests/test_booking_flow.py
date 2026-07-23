from tests.conftest import login


def test_complete_booking_flow(client, db, seeded):
    headers = login(client, "customer@example.com")
    show = seeded["show"]
    show_seat = seeded["show_seats"][0]

    lock = client.post(
        "/api/v1/seat-locks",
        headers=headers,
        json={"show_id": show.id, "show_seat_ids": [show_seat.id]},
    )
    assert lock.status_code == 201, lock.text

    booking = client.post(
        "/api/v1/bookings",
        headers=headers,
        json={"lock_token": lock.json()["lock_token"]},
    )
    assert booking.status_code == 201, booking.text
    assert booking.json()["status"] == "PENDING_PAYMENT"

    payment = client.post(
        "/api/v1/payments",
        headers=headers,
        json={
            "booking_id": booking.json()["id"],
            "method": "UPI",
            "idempotency_key": "payment-key-0001",
        },
    )
    assert payment.status_code == 201, payment.text

    confirmed = client.post(
        f"/api/v1/payments/{payment.json()['id']}/mock-result",
        headers=headers,
        json={"success": True, "gateway_reference": "gw-123"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "SUCCESS"

    fetched = client.get(f"/api/v1/bookings/{booking.json()['id']}", headers=headers)
    assert fetched.json()["status"] == "CONFIRMED"


def test_second_user_cannot_lock_same_seat(client, db, seeded):
    first_headers = login(client, "customer@example.com")
    second_headers = login(client, "other@example.com")
    show = seeded["show"]
    seat = seeded["show_seats"][0]

    first = client.post(
        "/api/v1/seat-locks",
        headers=first_headers,
        json={"show_id": show.id, "show_seat_ids": [seat.id]},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/seat-locks",
        headers=second_headers,
        json={"show_id": show.id, "show_seat_ids": [seat.id]},
    )
    assert second.status_code == 409


def test_failed_payment_releases_seat(client, db, seeded):
    headers = login(client, "customer@example.com")
    show = seeded["show"]
    seat = seeded["show_seats"][0]

    lock = client.post(
        "/api/v1/seat-locks",
        headers=headers,
        json={"show_id": show.id, "show_seat_ids": [seat.id]},
    ).json()
    booking = client.post(
        "/api/v1/bookings", headers=headers, json={"lock_token": lock["lock_token"]}
    ).json()
    payment = client.post(
        "/api/v1/payments",
        headers=headers,
        json={
            "booking_id": booking["id"],
            "method": "CARD",
            "idempotency_key": "payment-key-0002",
        },
    ).json()
    result = client.post(
        f"/api/v1/payments/{payment['id']}/mock-result",
        headers=headers,
        json={"success": False, "failure_reason": "Declined"},
    )
    assert result.status_code == 200
    assert result.json()["status"] == "FAILED"

    seats = client.get(f"/api/v1/shows/{show.id}/seats").json()
    selected = next(item for item in seats if item["id"] == seat.id)
    assert selected["status"] == "AVAILABLE"
