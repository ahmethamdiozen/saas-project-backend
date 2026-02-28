import redis
import json

redis_client = redis.Redis(host="localhost", port=6379, db=0)

CANCEL_CHANNEL = "job_cancellations"

def publish_job_cancel(job_id: str):
    message = json.dumps({"job_id": job_id})
    redis_client.publish(CANCEL_CHANNEL, message)

