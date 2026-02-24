from datetime import datetime, timezone
import time

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.modules.jobs.models import Job, JobResult, JobStatus
from app.worker.locks import acquire_job_lock, release_job_lock

def process_job(job_id: str):

    #distributed lock
    if not acquire_job_lock(job_id):
        print(f"Job {job_id} already running elsewhere")
        return

    db: Session = SessionLocal()

    #job load
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        db.close()
        return
    
    try:

        #idempotency guard
        if job.status in (JobStatus.SUCCESS.value, JobStatus.FAILED.value):
            print(f"Job {job_id} already finished. Skipping.")
            return

        #mark RUNNING
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        job.finished_at = None
        db.commit()

        #execution
        time.sleep(10)

        result_payload = {
            "answer": 42
        }

        #upsert(update and insert) result (idempotent)

        existing_result = (
            db.query(JobResult)
            .filter(JobResult.job_id == job.id)
            .first()
        )
        if existing_result:
            existing_result.result_data = result_payload
            existing_result.error_message = None
        else:
            db.add(JobResult(
                job_id=job.id,
                result_data=result_payload
            ))

        # if SUCCESS

        job.status = JobStatus.SUCCESS.value
        job.finished_at = datetime.now(timezone.utc)
        db.commit()

         # FAILED
    except Exception as e:

        #rollback failed transaction
        db.rollback()

        #upsert error result
        existing_result = (
            db.query(JobResult)
            .filter(JobResult.job_id == job.id)
            .first()
        )

        if existing_result:
            existing_result.error_message = str(e)
        else:
            db.add(JobResult(
                job_id=job.id,
                error_message=str(e)
            ))

        job.status = JobStatus.FAILED.value
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
    
        raise


    finally:
        #always release lock
        release_job_lock(job_id)
        db.close()