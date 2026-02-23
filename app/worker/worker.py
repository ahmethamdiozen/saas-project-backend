import redis
from rq import Worker, Queue
from app.modules.users.models import User
from app.modules.auth.models import RefreshToken
from app.modules.subscriptions.models import Subscription, UserSubscription
from app.modules.jobs.models import Job, JobResult
from app.db import models  # to load models

listen = ["default"]

redis_conn = redis.Redis(host="localhost", port=6379, db=0)

if __name__ == "__main__":
    worker = Worker(
        [Queue(name, connection=redis_conn) for name in listen]
    )
    worker.work()