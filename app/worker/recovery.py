from datetime import datetime, timezone, timedelta
import time

from sqlalchemy.orm import Session

import app.db.models
from app.db.session import SessionLocal
from app.modules.jobs.models import Job, JobStatus
from app.worker.redis_queue import job_queue
from app.worker.tasks import process_job

STUCK_THRESHOLD_SECONDS = 360
MAX_RECOVERY_ATTEMPTS = 3

def recover_stuck_jobs():
    db: Session = SessionLocal()

    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            seconds=STUCK_THRESHOLD_SECONDS
        )
        
        stuck_jobs = (
            db.query(Job)
            .filter(Job.status == JobStatus.RUNNING.value)
            .filter(Job.started_at < cutoff_time)
            .all()
        )

        for job in stuck_jobs:

            print(f"Recovering stuck job {job.id}")

            #recovery limit guard
            if job.recovery_attempts >= MAX_RECOVERY_ATTEMPTS:
                print(f"Job {job.id} exceeded max recovery attempts")
                continue

            #mark FAILED
            job.status = JobStatus.FAILED.value
            job.finished_at = datetime.now(timezone.utc)
            job.recovery_attempts += 1
            db.commit()
            
            #requeue new execution
            job_queue.enqueue(process_job, str(job.id))
    
    finally:
        db.close()

if __name__ == "__main__":
    print("Recovery worker started...")

    while True:
        print("Recovery worker still working")
        recover_stuck_jobs()
        time.sleep(30)