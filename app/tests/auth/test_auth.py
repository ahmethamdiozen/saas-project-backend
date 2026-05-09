from app.core.config import settings
from app.core.tokens import create_password_reset_token, create_email_verification_token

BASE = settings.API_V1_STR


def test_register_user(client):
    response = client.post(f"{BASE}/auth/register", json={"email": "register@test.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "register@test.com"
    assert "id" in data
    assert data["is_verified"] is False


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


def test_refresh_token(client):
    client.post(f"{BASE}/auth/register", json={"email": "refresh@test.com", "password": "password123"})
    client.post(f"{BASE}/auth/login", json={"email": "refresh@test.com", "password": "password123"})
    response = client.post(f"{BASE}/auth/refresh")
    assert response.status_code == 200
    assert "access_token" in response.cookies


def test_change_password(client):
    client.post(f"{BASE}/auth/register", json={"email": "chpass@test.com", "password": "oldpass123"})
    client.post(f"{BASE}/auth/login", json={"email": "chpass@test.com", "password": "oldpass123"})
    response = client.post(
        f"{BASE}/users/me/change-password",
        json={"current_password": "oldpass123", "new_password": "newpass123"},
    )
    assert response.status_code == 200
    client.post(f"{BASE}/auth/logout")
    assert client.post(f"{BASE}/auth/login", json={"email": "chpass@test.com", "password": "newpass123"}).status_code == 200


def test_change_password_wrong_current(client):
    client.post(f"{BASE}/auth/register", json={"email": "chpass2@test.com", "password": "pass123"})
    client.post(f"{BASE}/auth/login", json={"email": "chpass2@test.com", "password": "pass123"})
    response = client.post(
        f"{BASE}/users/me/change-password",
        json={"current_password": "WRONG", "new_password": "newpass123"},
    )
    assert response.status_code == 400


def test_forgot_password_always_200(client):
    response = client.post(f"{BASE}/auth/forgot-password", json={"email": "nonexistent@test.com"})
    assert response.status_code == 200


def test_reset_password(client):
    reg = client.post(f"{BASE}/auth/register", json={"email": "resetpw@test.com", "password": "oldpass123"})
    user_id = str(reg.json()["id"])

    token = create_password_reset_token(user_id)

    response = client.post(f"{BASE}/auth/reset-password", json={"token": token, "new_password": "newpass123"})
    assert response.status_code == 200

    assert client.post(f"{BASE}/auth/login", json={"email": "resetpw@test.com", "password": "newpass123"}).status_code == 200


def test_reset_password_invalid_token(client):
    response = client.post(f"{BASE}/auth/reset-password", json={"token": "invalid-token", "new_password": "newpass123"})
    assert response.status_code == 400


def test_reset_password_token_single_use(client):
    reg = client.post(f"{BASE}/auth/register", json={"email": "singleuse@test.com", "password": "oldpass123"})
    user_id = str(reg.json()["id"])
    token = create_password_reset_token(user_id)

    client.post(f"{BASE}/auth/reset-password", json={"token": token, "new_password": "newpass123"})
    response = client.post(f"{BASE}/auth/reset-password", json={"token": token, "new_password": "anotherpass123"})
    assert response.status_code == 400


def test_verify_email(client):
    reg = client.post(f"{BASE}/auth/register", json={"email": "verify@test.com", "password": "pass123"})
    user_id = str(reg.json()["id"])

    token = create_email_verification_token(user_id)
    response = client.get(f"{BASE}/auth/verify-email?token={token}")
    assert response.status_code == 200

    client.post(f"{BASE}/auth/login", json={"email": "verify@test.com", "password": "pass123"})
    profile = client.get(f"{BASE}/users/me")
    assert profile.json()["is_verified"] is True


def test_verify_email_invalid_token(client):
    response = client.get(f"{BASE}/auth/verify-email?token=bogus")
    assert response.status_code == 400


def test_resend_verification_already_verified(client):
    reg = client.post(f"{BASE}/auth/register", json={"email": "reverify@test.com", "password": "pass123"})
    user_id = str(reg.json()["id"])
    token = create_email_verification_token(user_id)
    client.get(f"{BASE}/auth/verify-email?token={token}")

    client.post(f"{BASE}/auth/login", json={"email": "reverify@test.com", "password": "pass123"})
    response = client.post(f"{BASE}/auth/resend-verification")
    assert response.status_code == 400
