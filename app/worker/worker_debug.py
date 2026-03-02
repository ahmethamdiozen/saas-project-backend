import redis
from rq import SimpleWorker, Queue
from app.core.config import settings
from app.worker.tasks import process_job
from app.db import models

# Use SimpleWorker to avoid os.fork() issues on macOS
def run_simple_worker():
    redis_conn = redis.from_url(settings.REDIS_URL)
    queue = Queue("default", connection=redis_conn)
    
    print("--- Starting SimpleWorker (No Fork Mode) ---")
    worker = SimpleWorker([queue], connection=redis_conn)
    worker.work()

if __name__ == "__main__":
    run_simple_worker()
