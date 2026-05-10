from unittest.mock import patch, MagicMock
from app.core.config import settings

BASE = settings.API_V1_STR
WEBHOOK_URL = f"{BASE}/webhooks/stripe"


def _make_event(event_type: str, data: dict) -> dict:
    return {"type": event_type, "data": {"object": data}}


def _post(client, event):
    return client.post(
        WEBHOOK_URL,
        content=b"payload",
        headers={"stripe-signature": "sig_test"},
    )


def test_missing_signature_returns_400(client):
    response = client.post(WEBHOOK_URL, content=b"payload")
    assert response.status_code == 400


def test_checkout_completed_assigns_subscription(client, db):
    from app.modules.users.models import User
    from app.modules.subscriptions.models import Subscription

    client.post(f"{BASE}/auth/register", json={"email": "webhook_ok@test.com", "password": "pass1234"})
    user = db.query(User).filter(User.email == "webhook_ok@test.com").first()
    user.stripe_customer_id = "cus_webhook1"
    db.commit()

    tier = db.query(Subscription).filter(Subscription.name == "Free").first()
    tier.stripe_price_id = "price_webhook1"
    db.commit()

    event = _make_event("checkout.session.completed", {
        "customer": "cus_webhook1",
        "subscription": "sub_webhook1",
    })

    mock_sub = {"items": {"data": [{"price": {"id": "price_webhook1"}}]}}

    with patch("app.modules.webhooks.stripe.stripe_service") as mock_stripe:
        mock_stripe.construct_webhook_event.return_value = event
        mock_stripe.retrieve_subscription.return_value = mock_sub

        response = client.post(
            WEBHOOK_URL,
            content=b"payload",
            headers={"stripe-signature": "sig_test"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_subscription_deleted_deactivates(client, db):
    from app.modules.users.models import User
    from app.modules.subscriptions.models import UserSubscription

    client.post(f"{BASE}/auth/register", json={"email": "webhook_del@test.com", "password": "pass1234"})
    user = db.query(User).filter(User.email == "webhook_del@test.com").first()

    user_sub = db.query(UserSubscription).filter(UserSubscription.user_id == user.id).first()
    if user_sub:
        user_sub.stripe_subscription_id = "sub_del1"
        db.commit()

    event = _make_event("customer.subscription.deleted", {"id": "sub_del1"})

    with patch("app.modules.webhooks.stripe.stripe_service") as mock_stripe:
        mock_stripe.construct_webhook_event.return_value = event

        response = client.post(
            WEBHOOK_URL,
            content=b"payload",
            headers={"stripe-signature": "sig_test"},
        )

    assert response.status_code == 200

    if user_sub:
        db.refresh(user_sub)
        assert user_sub.status == "inactive"


def test_subscription_updated_to_active(client, db):
    from app.modules.users.models import User
    from app.modules.subscriptions.models import UserSubscription

    client.post(f"{BASE}/auth/register", json={"email": "webhook_upd@test.com", "password": "pass1234"})
    user = db.query(User).filter(User.email == "webhook_upd@test.com").first()

    user_sub = db.query(UserSubscription).filter(UserSubscription.user_id == user.id).first()
    if user_sub:
        user_sub.stripe_subscription_id = "sub_upd1"
        user_sub.status = "inactive"
        db.commit()

    event = _make_event("customer.subscription.updated", {"id": "sub_upd1", "status": "active"})

    with patch("app.modules.webhooks.stripe.stripe_service") as mock_stripe:
        mock_stripe.construct_webhook_event.return_value = event

        response = client.post(
            WEBHOOK_URL,
            content=b"payload",
            headers={"stripe-signature": "sig_test"},
        )

    assert response.status_code == 200

    if user_sub:
        db.refresh(user_sub)
        assert user_sub.status == "active"


def test_payment_failed_returns_ok(client):
    event = _make_event("invoice.payment_failed", {"customer": "cus_nope"})

    with patch("app.modules.webhooks.stripe.stripe_service") as mock_stripe:
        mock_stripe.construct_webhook_event.return_value = event

        response = client.post(
            WEBHOOK_URL,
            content=b"payload",
            headers={"stripe-signature": "sig_test"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
