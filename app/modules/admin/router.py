from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import uuid
from app.db.session import get_db
from app.modules.auth.dependencies import get_admin_user
from app.modules.users.models import User
from app.modules.jobs.models import Job, JobStatus
from app.modules.subscriptions.models import UserSubscription, Subscription
from app.modules.subscriptions.service import assign_subscription_to_user, get_subscription_tier_by_name

router = APIRouter()

@router.get("/stats")
def get_system_stats(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get high-level system statistics for admins"""
    total_users = db.query(User).count()
    total_jobs = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.status == JobStatus.RUNNING.value).count()
    
    # Subscriptions distribution
    sub_stats = (
        db.query(Subscription.name, func.count(UserSubscription.id))
        .join(UserSubscription)
        .filter(UserSubscription.status == "active")
        .group_by(Subscription.name)
        .all()
    )
    
    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "subscriptions": {name: count for name, count in sub_stats}
    }

@router.get("/users")
def list_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    is_active: Optional[bool] = None,
):
    query = db.query(User)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at,
            }
            for u in users
        ],
    }


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    active_sub = next((s for s in user.subscriptions if s.status == "active"), None)
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "subscription": active_sub.subscription.name if active_sub else None,
        "total_jobs": len(user.jobs),
    }


@router.patch("/users/{user_id}/ban")
def ban_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot ban another admin")
    user.is_active = False
    db.commit()
    return {"message": f"{user.email} has been banned"}


@router.patch("/users/{user_id}/unban")
def unban_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    return {"message": f"{user.email} has been unbanned"}


@router.get("/subscriptions/tiers")
def list_subscription_tiers(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    tiers = db.query(Subscription).order_by(Subscription.name).all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "job_limit": t.job_limit,
            "rate_limit_per_minute": t.rate_limit_per_minute,
            "max_concurrent_jobs": t.max_concurrent_jobs,
        }
        for t in tiers
    ]


@router.post("/users/{user_id}/subscription")
def assign_subscription(
    user_id: uuid.UUID,
    tier_name: str = Query(..., description="Subscription tier name (e.g. Free, Pro)"),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    tier = get_subscription_tier_by_name(db, tier_name)
    if not tier:
        raise HTTPException(status_code=404, detail=f"Subscription tier '{tier_name}' not found")
    assign_subscription_to_user(db, user_id=user_id, tier_id=tier.id)
    return {"message": f"{user.email} assigned to '{tier_name}' plan"}


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: uuid.UUID,
    role: str = Query(..., description="New role: 'user' or 'admin'"),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    if role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.commit()
    return {"message": f"{user.email} role updated to '{role}'"}


@router.get("/jobs")
def list_all_jobs(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """List all jobs in the system (across all users)"""
    jobs = (
        db.query(Job)
        .order_by(Job.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": str(job.id),
            "user_email": job.user.email,
            "status": job.status,
            "created_at": job.created_at
        }
        for job in jobs
    ]
