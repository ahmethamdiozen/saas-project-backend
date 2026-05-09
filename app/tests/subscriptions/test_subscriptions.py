from unittest.mock import patch, MagicMock
from app.core.config import settings

BASE = settings.API_V1_STR


def _login(client, email="sub_user@test.com"):
    client.post(f"{BASE}/auth/register", json={"email": email, "password": "password123"})
    client.post(f"{BASE}/auth/login", json={"email": email, "password": "password123"})


def test_list_tiers_public(client):
    _login(client, "tier_lister@test.com")  # triggers Free tier creation
    client.post(f"{BASE}/auth/logout")
    response = client.get(f"{BASE}/subscriptions/tiers")
    assert response.status_code == 200
    tiers = response.json()
    assert isinstance(tiers, list)
    assert any(t["name"] == "Free" for t in tiers)


def test_get_my_subscription(client):
    _login(client, "mysub@test.com")
    response = client.get(f"{BASE}/subscriptions/me")
    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_checkout_tier_not_found(client):
    _login(client, "checkout_404@test.com")
    response = client.post(f"{BASE}/subscriptions/checkout?tier_name=NonExistent")
    assert response.status_code == 404


def test_checkout_tier_no_stripe_price(client):
    _login(client, "checkout_400@test.com")
    response = client.post(f"{BASE}/subscriptions/checkout?tier_name=Free")
    assert response.status_code == 400


def test_checkout_creates_stripe_session(client):
    _login(client, "checkout_ok@test.com")

    with patch("app.modules.subscriptions.router.stripe_service") as mock_stripe:
        mock_stripe.get_or_create_customer.return_value = "cus_test123"
        mock_stripe.create_checkout_session.return_value = "https://checkout.stripe.com/test"

        with patch("app.modules.subscriptions.router.get_subscription_tier_by_name") as mock_tier:
            tier = MagicMock()
            tier.stripe_price_id = "price_test123"
            mock_tier.return_value = tier

            response = client.post(f"{BASE}/subscriptions/checkout?tier_name=Pro")

    assert response.status_code == 200
    assert "checkout_url" in response.json()


def test_portal_no_customer(client):
    _login(client, "portal_no_cust@test.com")
    response = client.post(f"{BASE}/subscriptions/portal")
    assert response.status_code == 400


def test_portal_with_customer(client, db):
    from app.modules.users.models import User
    _login(client, "portal_ok@test.com")
    user = db.query(User).filter(User.email == "portal_ok@test.com").first()
    user.stripe_customer_id = "cus_test456"
    db.commit()

    with patch("app.modules.subscriptions.router.stripe_service") as mock_stripe:
        mock_stripe.create_billing_portal_session.return_value = "https://billing.stripe.com/test"
        response = client.post(f"{BASE}/subscriptions/portal")

    assert response.status_code == 200
    assert "portal_url" in response.json()
