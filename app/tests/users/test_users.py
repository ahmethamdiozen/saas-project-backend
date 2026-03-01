from app.core.config import settings

def test_read_me(client):
    # Register and login to get access token
    email = "me@example.com"
    password = "password123"
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email, "password": password}
    )
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": password}
    )
    access_token = login_response.json()["access_token"]
    
    # Get profile
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "id" in data

def test_read_me_unauthorized(client):
    response = client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 401
