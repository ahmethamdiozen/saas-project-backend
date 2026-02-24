from app.worker.redis_client import redis_client

LOCK_EXPIRE_SECONDS = 600 

def acquire_job_lock(job_id: str) -> bool:
    """
    True -> Worker takes this job.
    False -> Other worker already running this job.
    """

    lock_key = f"job-lock:{job_id}"

    return redis_client.set(
        lock_key,
        "locked",
        nx=True,        # set if not exists
        ex=LOCK_EXPIRE_SECONDS
    )

def release_job_lock(job_id: str):

    lock_key = f"job-lock:{job_id}"
    redis_client.delete(lock_key)