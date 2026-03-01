from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.modules.auth.dependencies import get_admin_user
from app.modules.users.models import User
from app.modules.jobs.models import Job, JobStatus
from app.modules.subscriptions.models import UserSubscription, Subscription

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
