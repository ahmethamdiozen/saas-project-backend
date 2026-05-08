import stripe
from fastapi import HTTPException
from app.core.config import settings


def _get_client() -> stripe.StripeClient:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Payment system not configured")
    return stripe.StripeClient(settings.STRIPE_SECRET_KEY)


def get_or_create_customer(user_id: str, email: str) -> str:
    client = _get_client()
    results = client.customers.search(query=f'metadata["user_id"]:"{user_id}"')
    if results.data:
        return results.data[0].id
    customer = client.customers.create(params={"email": email, "metadata": {"user_id": user_id}})
    return customer.id


def create_checkout_session(customer_id: str, price_id: str, success_url: str, cancel_url: str) -> str:
    client = _get_client()
    session = client.checkout.sessions.create(params={
        "customer": customer_id,
        "payment_method_types": ["card"],
        "line_items": [{"price": price_id, "quantity": 1}],
        "mode": "subscription",
        "success_url": success_url,
        "cancel_url": cancel_url,
    })
    return session.url


def create_billing_portal_session(customer_id: str, return_url: str) -> str:
    client = _get_client()
    session = client.billing_portal.sessions.create(params={
        "customer": customer_id,
        "return_url": return_url,
    })
    return session.url


def retrieve_subscription(subscription_id: str) -> dict:
    client = _get_client()
    return client.subscriptions.retrieve(subscription_id)


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    try:
        return stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
