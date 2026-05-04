from app.core.config import settings

BASE = settings.API_V1_STR


def _login(client, email="me@test.com"):
    client.post(f"{BASE}/auth/register", json={"email": email, "password": "password123"})
    client.post(f"{BASE}/auth/login", json={"email": email, "password": "password123"})


def test_read_me(client):
    _login(client, "me@test.com")
    response = client.get(f"{BASE}/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@test.com"
    assert "id" in data


def test_read_me_unauthorized(client):
    response = client.get(f"{BASE}/users/me")
    assert response.status_code == 401
