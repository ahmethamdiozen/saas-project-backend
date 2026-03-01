from app.core.config import settings

def test_register_user(client):
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "testuser@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "id" in data

def test_login_user(client):
    # First, register a user
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "login@example.com", "password": "password123"}
    )
    
    # Attempt login
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    # Check if refresh_token cookie is set
    assert "refresh_token" in response.cookies

def test_login_invalid_password(client):
    # Register user
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "wrongpass@example.com", "password": "password123"}
    )
    
    # Try with wrong password
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "wrongpass@example.com", "password": "WRONGPASSWORD"}
    )
    assert response.status_code == 401
