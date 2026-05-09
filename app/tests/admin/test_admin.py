from app.core.config import settings
from app.modules.users.models import User

BASE = settings.API_V1_STR


def _register_login(client, email, password="password123"):
    client.post(f"{BASE}/auth/register", json={"email": email, "password": password})
    client.post(f"{BASE}/auth/login", json={"email": email, "password": password})


def _make_admin(client, db, email="admin@test.com"):
    client.post(f"{BASE}/auth/register", json={"email": email, "password": "password123"})
    user = db.query(User).filter(User.email == email).first()
    user.role = "admin"
    db.commit()
    client.post(f"{BASE}/auth/login", json={"email": email, "password": "password123"})
    return user


def test_stats_requires_admin(client):
    _register_login(client, "notadmin@test.com")
    assert client.get(f"{BASE}/admin/stats").status_code == 403


def test_get_stats(client, db):
    _make_admin(client, db)
    response = client.get(f"{BASE}/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_jobs" in data


def test_list_users(client, db):
    _make_admin(client, db)
    response = client.get(f"{BASE}/admin/users")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 1


def test_list_users_filter_active(client, db):
    _make_admin(client, db)
    response = client.get(f"{BASE}/admin/users?is_active=true")
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert item["is_active"] is True


def test_get_user_detail(client, db):
    _register_login(client, "detail_target@test.com")
    target = db.query(User).filter(User.email == "detail_target@test.com").first()

    _make_admin(client, db, "admin_detail@test.com")
    response = client.get(f"{BASE}/admin/users/{target.id}")
    assert response.status_code == 200
    assert response.json()["email"] == "detail_target@test.com"


def test_ban_and_unban_user(client, db):
    _register_login(client, "victim@test.com")
    victim = db.query(User).filter(User.email == "victim@test.com").first()

    _make_admin(client, db, "admin_ban@test.com")

    assert client.patch(f"{BASE}/admin/users/{victim.id}/ban").status_code == 200
    db.refresh(victim)
    assert victim.is_active is False

    assert client.patch(f"{BASE}/admin/users/{victim.id}/unban").status_code == 200
    db.refresh(victim)
    assert victim.is_active is True


def test_cannot_ban_admin(client, db):
    other_admin = _make_admin(client, db, "otheradmin@test.com")
    _make_admin(client, db, "admin_try@test.com")
    response = client.patch(f"{BASE}/admin/users/{other_admin.id}/ban")
    assert response.status_code == 400


def test_banned_user_cannot_access(client, db):
    _register_login(client, "banned@test.com")
    banned = db.query(User).filter(User.email == "banned@test.com").first()

    _make_admin(client, db, "admin_for_ban@test.com")
    client.patch(f"{BASE}/admin/users/{banned.id}/ban")

    client.post(f"{BASE}/auth/logout")
    client.post(f"{BASE}/auth/login", json={"email": "banned@test.com", "password": "password123"})
    assert client.get(f"{BASE}/users/me").status_code == 403


def test_assign_subscription(client, db):
    _register_login(client, "subassign@test.com")
    target = db.query(User).filter(User.email == "subassign@test.com").first()

    _make_admin(client, db, "admin_sub@test.com")
    response = client.post(f"{BASE}/admin/users/{target.id}/subscription?tier_name=Free")
    assert response.status_code == 200


def test_update_tier_stripe_price(client, db):
    _make_admin(client, db, "admin_tier@test.com")

    tiers = client.get(f"{BASE}/subscriptions/tiers").json()
    free_tier = next(t for t in tiers if t["name"] == "Free")

    response = client.patch(
        f"{BASE}/admin/subscriptions/tiers/{free_tier['id']}",
        json={"stripe_price_id": "price_test_123"},
    )
    assert response.status_code == 200
    assert response.json()["stripe_price_id"] == "price_test_123"
