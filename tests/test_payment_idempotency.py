from tests.conftest import login


def test_payment_idempotency_returns_same_payment(client, db, seeded):
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
    payload = {
        "booking_id": booking["id"],
        "method": "UPI",
        "idempotency_key": "same-key-12345",
    }
    first = client.post("/api/v1/payments", headers=headers, json=payload)
    second = client.post("/api/v1/payments", headers=headers, json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
