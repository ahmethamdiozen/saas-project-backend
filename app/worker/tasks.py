from datetime import datetime, timezone
import time

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.modules.jobs.models import Job, JobResult, JobStatus, JobExecution
from app.worker.locks import acquire_job_lock, release_job_lock

SLOW_EXECUTION_THRESHOLD = 5

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
        
        # define execution attempt
        attempt_number = len(job.executions) + 1

        execution = JobExecution(
            job_id = job.id,
            attempt_number=attempt_number,
            status=JobStatus.RUNNING.value
        )

        db.add(execution)
        db.commit()
        db.refresh(execution)

        #mark RUNNING
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        job.finished_at = None
        db.commit()

        # STEP 1
        execution.current_step = "loading_data"
        execution.progress = 20
        db.commit()
        time.sleep(2)

        # STEP 2
        execution.current_step = "processing_data"
        execution.progress = 50
        db.commit()
        time.sleep(2)

        # STEP 3
        execution.current_step = "finalizing"
        execution.progress = 80
        db.commit()
        time.sleep(2)

        # STEP 4
        execution.current_step = "completed"
        execution.progress = 100
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

        # execution success
        execution.status = JobStatus.SUCCESS.value
        execution.finished_at = datetime.now(timezone.utc)
        execution.duration_seconds = (
            execution.finished_at - execution.started_at
        ).total_seconds
        if execution.duration_seconds > SLOW_EXECUTION_THRESHOLD:
            print(f"SLOW EXECUTION: job{job.id} duration{execution.duration_seconds}")
        db.commit()

        # if SUCCESS

        job.status = JobStatus.SUCCESS.value
        job.finished_at = datetime.now(timezone.utc)
        db.commit()

         # FAILED
    except Exception as e:

        execution.status = JobStatus.FAILED.value
        execution.error_message = str(e)
        execution.finished_at = datetime.now(timezone.utc)
        execution.duration_seconds = (
            execution.finished_at - execution.started_at
        ).total_seconds
        if execution.duration_seconds > SLOW_EXECUTION_THRESHOLD:
            print(f"SLOW EXECUTION: job={job.id} duration={execution.duration_seconds}")
        db.commit()

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