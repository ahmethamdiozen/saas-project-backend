from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.modules.subscriptions.schemas import SubscriptionRead, SubscriptionCreate, UserSubscriptionRead
from app.modules.subscriptions.service import (
    create_subscription_tier,
    get_user_active_subscription,
    get_subscription_tier_by_name,
)
from app.modules.auth.dependencies import get_current_user, get_admin_user
from app.modules.users.models import User
from app.core.config import settings
from app.core import stripe_service

router = APIRouter()

@router.post("/tiers", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
def create_tier(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    existing = get_subscription_tier_by_name(db, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="Subscription tier already exists")
    
    return create_subscription_tier(db, payload)

@router.get("/me", response_model=UserSubscriptionRead)
def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = get_user_active_subscription(db, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return sub


@router.post("/checkout")
def create_checkout(
    tier_name: str = Query(..., description="Subscription tier name (e.g. Pro)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tier = get_subscription_tier_by_name(db, tier_name)
    if not tier:
        raise HTTPException(status_code=404, detail=f"Tier '{tier_name}' not found")
    if not tier.stripe_price_id:
        raise HTTPException(status_code=400, detail=f"Tier '{tier_name}' has no Stripe price configured")

    if not current_user.stripe_customer_id:
        customer_id = stripe_service.get_or_create_customer(str(current_user.id), current_user.email)
        current_user.stripe_customer_id = customer_id
        db.commit()
    else:
        customer_id = current_user.stripe_customer_id

    checkout_url = stripe_service.create_checkout_session(
        customer_id=customer_id,
        price_id=tier.stripe_price_id,
        success_url=f"{settings.FRONTEND_URL}/subscription/success",
        cancel_url=f"{settings.FRONTEND_URL}/subscription/cancel",
    )
    return {"checkout_url": checkout_url}


@router.post("/portal")
def create_portal(
    current_user: User = Depends(get_current_user),
):
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found. Subscribe first.")
    portal_url = stripe_service.create_billing_portal_session(
        customer_id=current_user.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/account",
    )
    return {"portal_url": portal_url}
