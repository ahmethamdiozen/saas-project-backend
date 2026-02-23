from datetime import datetime, timezone
import time

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.modules.jobs.models import Job, JobResult, JobStatus

def process_job(job_id: str):
    db: Session = SessionLocal()

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        db.close()
        return
    
    try:
        # RUNNING
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        time.sleep(10)

        result_payload = {
            "answer": 42
        }

        # RESULT RECORD

        result = JobResult(
            job_id=job.id,
            result_data=result_payload
        )
        db.add(result)

        # SUCCESS

        job.status = JobStatus.SUCCESS.value
        job.finished_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        result = JobResult(
            job_id=job.id,
            error_message=str(e)
        )
        db.add(result)

        job.status = JobStatus.FAILED.value
        job.finished_at = datetime.now(timezone.utc)
        db.commit()

    finally:
        db.close()