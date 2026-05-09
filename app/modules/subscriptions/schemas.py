from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class SubscriptionBase(BaseModel):
    name: str
    job_limit: int
    rate_limit_per_minute: int
    max_concurrent_jobs: int

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionRead(SubscriptionBase):
    id: UUID
    stripe_price_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriptionTierUpdate(BaseModel):
    job_limit: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None
    max_concurrent_jobs: Optional[int] = None
    stripe_price_id: Optional[str] = None

class UserSubscriptionBase(BaseModel):
    subscription_id: UUID
    status: str = "active"

class UserSubscriptionCreate(UserSubscriptionBase):
    user_id: UUID

class UserSubscriptionRead(UserSubscriptionBase):
    id: UUID
    started_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
