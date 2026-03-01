from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone
from app.modules.subscriptions.models import Subscription, UserSubscription
from app.modules.subscriptions.schemas import SubscriptionCreate, UserSubscriptionCreate
from app.core.logging import logger
from app.core.cache import cache

def create_subscription_tier(db: Session, tier: SubscriptionCreate) -> Subscription:
    db_tier = Subscription(
        name=tier.name,
        job_limit=tier.job_limit,
        rate_limit_per_minute=tier.rate_limit_per_minute,
        max_concurrent_jobs=tier.max_concurrent_jobs
    )
    db.add(db_tier)
    db.commit()
    db.refresh(db_tier)
    logger.info(f"Created subscription tier: {tier.name}")
    return db_tier

def get_subscription_tier_by_name(db: Session, name: str) -> Subscription | None:
    return db.query(Subscription).filter(Subscription.name == name).first()

def assign_subscription_to_user(db: Session, user_id: UUID, tier_id: UUID) -> UserSubscription:
    db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id,
        UserSubscription.status == "active"
    ).update({"status": "inactive"})
    
    db_user_sub = UserSubscription(
        user_id=user_id,
        subscription_id=tier_id,
        status="active",
        started_at=datetime.now(timezone.utc)
    )
    db.add(db_user_sub)
    db.commit()
    db.refresh(db_user_sub)
    
    cache.delete(f"user_sub:{user_id}")
    return db_user_sub

def get_user_active_subscription(db: Session, user_id: UUID) -> UserSubscription | None:
    # We bypass cache for the router's /me call to return a real SQLAlchemy model
    # but the rate_limiter can still use cache if we separate them.
    # For now, let's just query the DB to be safe with FastAPI's response_model.
    return db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id,
        UserSubscription.status == "active"
    ).first()

def get_or_create_free_tier(db: Session) -> Subscription:
    free_tier = get_subscription_tier_by_name(db, "Free")
    if not free_tier:
        free_tier = create_subscription_tier(db, SubscriptionCreate(
            name="Free",
            job_limit=10,
            rate_limit_per_minute=2,
            max_concurrent_jobs=1
        ))
    return free_tier
