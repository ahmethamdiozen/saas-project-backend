import redis
import json
import threading

from app.worker.cancellation import cancel_token
from app.worker.cancel_pubsub import redis_client, CANCEL_CHANNEL


def _listen():
    pubsub = redis_client.pubsub()
    pubsub.subscribe(CANCEL_CHANNEL)

    for message in pubsub.listen():
        if message["type"] != "message":
            continue

        data = json.loads(message["data"])
        job_id = data["job_id"]
        
        print(f"[CANCEL RECIEVED] {job_id}")
        cancel_token(job_id)

def start_cancel_listener():
    thread = threading.Thread(target=_listen, daemon=True)
    thread.start()


