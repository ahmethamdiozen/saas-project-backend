import redis
from rq import Queue
from app.core.config import settings

# CRITICAL FIX: Use the unified cloud Redis URL instead of hardcoded localhost
redis_conn = redis.from_url(settings.REDIS_URL)

job_queue = Queue("default", connection=redis_conn)
