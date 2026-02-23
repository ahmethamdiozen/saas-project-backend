from fastapi import APIRouter, HTTPException
from uuid import uuid4
from app.modules.jobs.service import enqueue_job
from fastapi import Depends
from sqlalchemy.orm import Session
from app.modules.auth.router import get_db
from app.modules.jobs.models import Job

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/")
def create_job():
    job_id = str(uuid4())

    enqueue_job(job_id)
    
    return {
        "job_id": job_id,
        "status": "queued"
    }

@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(404, "Job not found")
    
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
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at
    }