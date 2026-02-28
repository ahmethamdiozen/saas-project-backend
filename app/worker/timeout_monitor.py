from datetime import datetime, timezone, timedelta
import time

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.modules.jobs.models import Job, JobStatus
from app.worker.cancel_pubsub import publish_job_cancel


CHECK_INTERVAL = 10  # saniye


def check_timeouts():
    db: Session = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        running_jobs = (
            db.query(Job)
            .filter(Job.status == JobStatus.RUNNING.value)
            .all()
        )

        for job in running_jobs:

            if not job.started_at:
                continue

            deadline = job.started_at + timedelta(
                seconds=job.max_execution_seconds
            )

            if now >= deadline:
                print(f"[TIMEOUT] Job {job.id}")

                job.status = JobStatus.TIMEOUT.value
                job.finished_at = now
                db.commit()

                publish_job_cancel(str(job.id))

    finally:
        db.close()


if __name__ == "__main__":
    print("Timeout monitor started")

    while True:
        check_timeouts()
        time.sleep(CHECK_INTERVAL)