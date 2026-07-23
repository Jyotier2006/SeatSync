def test_register_and_login(client):
    payload = {
        "email": "new@example.com",
        "full_name": "New User",
        "password": "StrongPassword123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["user"]["email"] == "new@example.com"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_duplicate_registration(client):
    payload = {
        "email": "duplicate@example.com",
        "full_name": "User",
        "password": "StrongPassword123",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
