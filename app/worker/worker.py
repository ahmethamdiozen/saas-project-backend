import os
import platform
import redis
from rq import Worker, Queue, SimpleWorker
from app.worker.cancel_listener import start_cancel_listener
from app.core.config import settings
from app.db import models  # noqa: F401 — load models so ORM is aware of them

os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

start_cancel_listener()

listen = ["default"]
redis_conn = redis.from_url(settings.REDIS_URL)

if __name__ == "__main__":
    queues = [Queue(name, connection=redis_conn) for name in listen]

    if platform.system() == "Darwin":
        # os.fork() is unstable on macOS with C-extensions (fitz, pinecone, etc.)
        worker = SimpleWorker(queues, connection=redis_conn)
    else:
        worker = Worker(queues, connection=redis_conn)

    worker.work()
