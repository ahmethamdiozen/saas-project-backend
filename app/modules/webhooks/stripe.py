from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.users.models import User
from app.modules.subscriptions.models import Subscription, UserSubscription
from app.modules.subscriptions.service import assign_subscription_to_user
from app.core import stripe_service
from app.core.logging import logger

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    event = stripe_service.construct_webhook_event(payload, sig_header)
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(db, data)

    elif event_type in ("customer.subscription.deleted", "customer.subscription.paused"):
        _handle_subscription_deactivated(db, data)

    elif event_type == "customer.subscription.updated":
        _handle_subscription_updated(db, data)

    elif event_type == "invoice.payment_failed":
        logger.warning(f"Payment failed for customer {data.get('customer')}")

    return {"status": "ok"}


def _handle_checkout_completed(db: Session, session: dict):
    customer_id = session.get("customer")
    stripe_sub_id = session.get("subscription")
    if not customer_id or not stripe_sub_id:
        return

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.warning(f"No user found for Stripe customer {customer_id}")
        return

    stripe_sub = stripe_service.retrieve_subscription(stripe_sub_id)
    price_id = stripe_sub["items"]["data"][0]["price"]["id"]

    tier = db.query(Subscription).filter(Subscription.stripe_price_id == price_id).first()
    if not tier:
        logger.warning(f"No tier found for Stripe price {price_id}")
        return

    user_sub = assign_subscription_to_user(db, user_id=user.id, tier_id=tier.id)
    user_sub.stripe_subscription_id = stripe_sub_id
    db.commit()
    logger.info(f"Assigned '{tier.name}' to user {user.email}")


def _handle_subscription_deactivated(db: Session, stripe_sub: dict):
    sub_id = stripe_sub.get("id")
    user_sub = db.query(UserSubscription).filter(
        UserSubscription.stripe_subscription_id == sub_id
    ).first()
    if user_sub:
        user_sub.status = "inactive"
        db.commit()
        logger.info(f"Deactivated subscription {sub_id}")


def _handle_subscription_updated(db: Session, stripe_sub: dict):
    sub_id = stripe_sub.get("id")
    stripe_status = stripe_sub.get("status")
    user_sub = db.query(UserSubscription).filter(
        UserSubscription.stripe_subscription_id == sub_id
    ).first()
    if not user_sub:
        return
    if stripe_status == "active":
        user_sub.status = "active"
    elif stripe_status in ("canceled", "unpaid", "past_due"):
        user_sub.status = "inactive"
    db.commit()
