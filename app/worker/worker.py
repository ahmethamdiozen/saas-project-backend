import redis
from rq import Worker, Queue
from app.worker.cancel_listener import start_cancel_listener
from app.core.config import settings
from app.modules.users.models import User
from app.modules.auth.models import RefreshToken
from app.modules.subscriptions.models import Subscription, UserSubscription
from app.modules.jobs.models import Job, JobResult, JobExecution
from app.db import models  # to load models


start_cancel_listener()

listen = ["default"]

# Use settings.REDIS_URL instead of hardcoded localhost
redis_conn = redis.from_url(settings.REDIS_URL)

if __name__ == "__main__":
    worker = Worker(
        [Queue(name, connection=redis_conn) for name in listen]
    )
    worker.work()