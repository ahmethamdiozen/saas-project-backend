import redis
from rq import Queue

redis_conn = redis.Redis(host="localhost", port=6379, db=0)

job_queue = Queue("default", connection=redis_conn)