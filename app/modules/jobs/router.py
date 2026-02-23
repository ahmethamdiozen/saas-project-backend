from fastapi import APIRouter
from uuid import uuid4
from app.modules.jobs.service import enqueue_job

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/")
def create_job():
    job_id = str(uuid4())

    enqueue_job(job_id)
    
    return {
        "job_id": job_id,
        "status": "queued"
    }

