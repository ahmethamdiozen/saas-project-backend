from app.worker.redis_queue import job_queue
from app.worker.tasks import process_job

def enqueue_job(job_id: str):
    job_queue.enqueue(process_job, job_id)

