from app.core.config import settings

BASE = settings.API_V1_STR


def test_register_user(client):
    response = client.post(f"{BASE}/auth/register", json={"email": "register@test.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "register@test.com"
    assert "id" in data


def test_register_duplicate_email(client):
    payload = {"email": "dup@test.com", "password": "password123"}
    client.post(f"{BASE}/auth/register", json=payload)
    response = client.post(f"{BASE}/auth/register", json=payload)
    assert response.status_code == 400


def test_login_sets_cookies(client):
    client.post(f"{BASE}/auth/register", json={"email": "login@test.com", "password": "password123"})
    response = client.post(f"{BASE}/auth/login", json={"email": "login@test.com", "password": "password123"})
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_login_invalid_password(client):
    client.post(f"{BASE}/auth/register", json={"email": "wrong@test.com", "password": "password123"})
    response = client.post(f"{BASE}/auth/login", json={"email": "wrong@test.com", "password": "WRONGPASSWORD"})
    assert response.status_code == 401


def test_logout_clears_cookies(client):
    client.post(f"{BASE}/auth/register", json={"email": "logout@test.com", "password": "password123"})
    client.post(f"{BASE}/auth/login", json={"email": "logout@test.com", "password": "password123"})
    response = client.post(f"{BASE}/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


def test_refresh_token(client):
    client.post(f"{BASE}/auth/register", json={"email": "refresh@test.com", "password": "password123"})
    client.post(f"{BASE}/auth/login", json={"email": "refresh@test.com", "password": "password123"})
    response = client.post(f"{BASE}/auth/refresh")
    assert response.status_code == 200
    assert response.json()["message"] == "Token refreshed"
    assert "access_token" in response.cookies
