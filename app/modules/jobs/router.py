from fastapi import APIRouter, HTTPException
from uuid import uuid4
from app.modules.jobs.service import create_job
from fastapi import Depends
from sqlalchemy.orm import Session
from app.modules.auth.router import get_db
from app.modules.jobs.models import Job, JobExecution, JobStatus
from app.modules.users.models import User
from app.modules.auth.dependencies import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/")
def create_job_endpoint(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    job: Job = create_job(db, current_user.id)

    return {
        "job_id": str(job.id),
        "status": job.status
    }


@router.get("/{job_id}/")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(404, "Job not found")

    latest_execution = (
        db.query(JobExecution)
        .filter(JobExecution.job_id == job.id)
        .order_by(JobExecution.attempt_number.desc())
        .first()
    )

    result_data = None
    error = None

    if job.result:
        result_data = job.result.result_data
        error = job.result.error_message

    return {
        "id": str(job.id),
        "status": job.status,
        "result": result_data,
        "error": error,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "execution": {
            "attempt_number": latest_execution.attempt_number,
            "status": latest_execution.status,
            "progress": latest_execution.progress,
            "current_step": latest_execution.current_step,
            "duration_seconds": latest_execution.duration_seconds,
        } if latest_execution else None
    }

@router.post("/{job_id}/cancel")
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user : User  = Depends(get_current_user)
):
    job: Job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(404, "Job not found")
    
    # ownership check
    if job.user_id != current_user.id:
        raise HTTPException((403, "Not allowed"))

    # only PENDING and RUNNING jobs can be cancelled.
    if job.status not in (
                        JobStatus.PENDING.value, 
                        JobStatus.RUNNING.value):
        raise HTTPException(400, "Job already finished")
    
    job.status = JobStatus.CANCELLED.value
    job.finished_at = datetime.now(timezone.utc)

    db.commit()

    return {"message": "Job cancelled"}