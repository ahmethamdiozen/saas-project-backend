from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from app.worker.redis_queue import job_queue
from app.worker.tasks import process_job
from app.modules.jobs.models import Job, JobStatus
from app.modules.subscriptions.service import get_user_active_subscription
from rq import Retry

def create_job(db: Session, user_id):
    # Get user's active subscription
    user_sub = get_user_active_subscription(db, user_id)
    
    if not user_sub:
        raise ValueError("User has no active subscription. Please subscribe to a plan.")
    
    tier = user_sub.subscription
    
    # 1. Check Concurrent Jobs Limit
    active_jobs_count = db.query(Job).filter(
        Job.user_id == user_id,
        Job.status == JobStatus.RUNNING.value
    ).count()
    
    if active_jobs_count >= tier.max_concurrent_jobs:
        raise ValueError(
            f"Concurrency limit reached. Your current plan '{tier.name}' "
            f"allows only {tier.max_concurrent_jobs} concurrent jobs."
        )

    # 2. Check Daily Job Limit
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    jobs_today_count = db.query(Job).filter(
        Job.user_id == user_id,
        Job.created_at >= today_start
    ).count()
    
    if jobs_today_count >= tier.job_limit:
        raise ValueError(
            f"Daily job limit reached. Your current plan '{tier.name}' "
            f"allows only {tier.job_limit} jobs per day."
        )

    # If all checks pass, create the job
    job = Job(
        user_id=user_id,
        status=JobStatus.PENDING.value,
        job_type="demo"
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    job_queue.enqueue(
        process_job, 
        str(job.id),
        retry=Retry(
            max=3,
            interval={10, 30, 120}
        ),
        job_timeout=300
    )

    return job

    
    

