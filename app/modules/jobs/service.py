from sqlalchemy.orm import Session
from app.worker.redis_queue import job_queue
from app.worker.tasks import process_job
from app.modules.jobs.models import Job, JobStatus

def create_job(db: Session, user_id):
    job = Job(
        user_id=user_id,
        status=JobStatus.PENDING.value,
        job_type="demo"
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    job_queue.enqueue(process_job, str(job.id))

    return job

    
    

