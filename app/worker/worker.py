import os
import redis
from rq import Worker, Queue, SimpleWorker
from app.worker.cancel_listener import start_cancel_listener
from app.core.config import settings
from app.db import models # Load models

# --- macOS FORK SAFETY ---
# This environment variable helps with some C-library crashes on macOS
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

start_cancel_listener()

listen = ["default"]
redis_conn = redis.from_url(settings.REDIS_URL)

if __name__ == "__main__":
    # On macOS ARM, os.fork() is highly unstable with C-extensions like fitz/pinecone.
    # We use SimpleWorker which processes jobs sequentially in the same process.
    print("🚀 Starting Production-Ready Worker (SimpleWorker Mode for macOS Stability)")
    
    worker = SimpleWorker(
        [Queue(name, connection=redis_conn) for name in listen], 
        connection=redis_conn
    )
    worker.work()
