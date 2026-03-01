import redis
from app.core.config import settings

# Unified Redis client using settings
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)
