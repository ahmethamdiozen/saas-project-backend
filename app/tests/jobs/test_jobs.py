from app.core.config import settings

BASE = settings.API_V1_STR


def _login(client, email):
    client.post(f"{BASE}/auth/register", json={"email": email, "password": "password123"})
    client.post(f"{BASE}/auth/login", json={"email": email, "password": "password123"})


def test_create_job(client):
    _login(client, "create_job@test.com")
    response = client.post(f"{BASE}/jobs/")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"


def test_list_jobs(client):
    _login(client, "list_jobs@test.com")
    client.post(f"{BASE}/jobs/")
    client.post(f"{BASE}/jobs/")
    response = client.get(f"{BASE}/jobs/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


def test_get_job_detail(client):
    _login(client, "detail_job@test.com")
    job_id = client.post(f"{BASE}/jobs/").json()["job_id"]
    response = client.get(f"{BASE}/jobs/{job_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["status"] == "PENDING"


def test_cancel_job(client):
    _login(client, "cancel_job@test.com")
    job_id = client.post(f"{BASE}/jobs/").json()["job_id"]
    response = client.post(f"{BASE}/jobs/{job_id}/cancel")
    assert response.status_code == 200
    assert response.json()["message"] == "Job cancelled"
    assert client.get(f"{BASE}/jobs/{job_id}/").json()["status"] == "CANCELLED"


def test_cancel_job_unauthorized(client):
    _login(client, "owner@test.com")
    job_id = client.post(f"{BASE}/jobs/").json()["job_id"]

    # Login as a different user and try to cancel
    _login(client, "attacker@test.com")
    response = client.post(f"{BASE}/jobs/{job_id}/cancel")
    assert response.status_code in (403, 404)


def test_list_jobs_unauthenticated(client):
    response = client.get(f"{BASE}/jobs/")
    assert response.status_code == 401
