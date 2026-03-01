import json
from typing import Any, Optional
from datetime import timedelta
from app.worker.redis_client import redis_client
from app.core.logging import logger

class Cache:
    @staticmethod
    def get(key: str) -> Optional[Any]:
        try:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    @staticmethod
    def set(key: str, value: Any, expire: int = 300) -> bool:
        """
        Store value in cache with expiration in seconds (default 5 minutes)
        """
        try:
            serialized_value = json.dumps(value)
            return redis_client.setex(key, expire, serialized_value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    @staticmethod
    def delete(key: str) -> bool:
        try:
            return redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    @staticmethod
    def clear_user_cache(user_id: Any):
        """Helper to clear common user-related cache keys"""
        Cache.delete(f"user:{user_id}")
        Cache.delete(f"user_sub:{user_id}")

cache = Cache()
