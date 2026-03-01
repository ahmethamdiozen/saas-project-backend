from app.core.config import settings

def get_auth_headers(client, email="jobs@example.com"):
    # Register and login to get access token
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email, "password": "password123"}
    )
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": "password123"}
    )
    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

def test_create_job(client):
    headers = get_auth_headers(client, "create_job@example.com")
    response = client.post(f"{settings.API_V1_STR}/jobs/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"

def test_list_jobs(client):
    headers = get_auth_headers(client, "list_jobs@example.com")
    # Create two jobs
    client.post(f"{settings.API_V1_STR}/jobs/", headers=headers)
    client.post(f"{settings.API_V1_STR}/jobs/", headers=headers)
    
    response = client.get(f"{settings.API_V1_STR}/jobs/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2

def test_get_job_detail(client):
    headers = get_auth_headers(client, "detail_job@example.com")
    # Create a job
    create_response = client.post(f"{settings.API_V1_STR}/jobs/", headers=headers)
    job_id = create_response.json()["job_id"]
    
    # Get details
    response = client.get(f"{settings.API_V1_STR}/jobs/{job_id}/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["status"] == "PENDING"

def test_cancel_job(client):
    headers = get_auth_headers(client, "cancel_job@example.com")
    # Create a job
    create_response = client.post(f"{settings.API_V1_STR}/jobs/", headers=headers)
    job_id = create_response.json()["job_id"]
    
    # Cancel it
    response = client.post(f"{settings.API_V1_STR}/jobs/{job_id}/cancel", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Job cancelled"
    
    # Verify status changed
    detail_response = client.get(f"{settings.API_V1_STR}/jobs/{job_id}/", headers=headers)
    assert detail_response.json()["status"] == "CANCELLED"
