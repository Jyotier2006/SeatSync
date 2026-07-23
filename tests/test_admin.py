from datetime import UTC, datetime, timedelta

from tests.conftest import login


def test_customer_cannot_use_admin_endpoint(client, db, seeded):
    headers = login(client, "customer@example.com")
    response = client.post(
        "/api/v1/admin/movies",
        headers=headers,
        json={
            "title": "Forbidden",
            "description": "",
            "duration_minutes": 100,
            "language": "English",
            "certificate": "U",
        },
    )
    assert response.status_code == 403


def test_admin_can_create_movie(client, db, seeded):
    headers = login(client, "admin@example.com")
    response = client.post(
        "/api/v1/admin/movies",
        headers=headers,
        json={
            "title": "Created by Admin",
            "description": "",
            "duration_minutes": 100,
            "language": "English",
            "certificate": "U",
        },
    )
    assert response.status_code == 201, response.text
