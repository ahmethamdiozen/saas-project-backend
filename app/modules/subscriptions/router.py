from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.modules.subscriptions.schemas import SubscriptionRead, SubscriptionCreate, UserSubscriptionRead
from app.modules.subscriptions.service import (
    create_subscription_tier, 
    get_user_active_subscription,
    get_subscription_tier_by_name
)
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User

router = APIRouter()

@router.post("/tiers", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
def create_tier(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db)
):
    existing = get_subscription_tier_by_name(db, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="Subscription tier already exists")
    
    return create_subscription_tier(db, payload)

@router.get("/me", response_model=UserSubscriptionRead)
def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sub = get_user_active_subscription(db, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return sub
