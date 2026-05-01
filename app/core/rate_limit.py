import time
import threading
from collections import defaultdict
from fastapi import HTTPException, status, Depends
from starlette.requests import HTTPConnection
from sqlalchemy.orm import Session
from app.worker.redis_client import redis_client
from app.core.logging import logger
from app.db.session import get_db
from app.modules.subscriptions.service import get_user_active_subscription
from app.core.security import decode_token

DEFAULT_ANONYMOUS_LIMIT = 500
FALLBACK_LIMIT = 20  # conservative per-worker limit when Redis is unavailable

_mem_counts: dict = defaultdict(lambda: {"count": 0, "minute": 0})
_mem_lock = threading.Lock()


def _check_memory_fallback(identifier: str, current_minute: int) -> bool:
    with _mem_lock:
        entry = _mem_counts[identifier]
        if entry["minute"] != current_minute:
            entry["count"] = 0
            entry["minute"] = current_minute
        entry["count"] += 1
        return entry["count"] <= FALLBACK_LIMIT


async def rate_limiter(
    request: HTTPConnection,
    db: Session = Depends(get_db)
):
    user_id = None
    limit = DEFAULT_ANONYMOUS_LIMIT
    identifier = f"rate_limit:ip:{request.client.host if request.client else 'unknown'}"

    try:
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if token:
            payload = decode_token(token)
            user_id = payload.get("sub")

            if user_id:
                identifier = f"rate_limit:user:{user_id}"
                active_sub = get_user_active_subscription(db, user_id)
                if active_sub and hasattr(active_sub, 'subscription') and active_sub.subscription:
                    limit = active_sub.subscription.rate_limit_per_minute

    except Exception as e:
        logger.debug(f"Rate limiter identification fallback: {e}")

    current_minute = int(time.time() / 60)
    key = f"{identifier}:{current_minute}"

    try:
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, 60)

        if count > limit:
            logger.warning(f"Rate limit exceeded for {identifier}: {count}/{limit}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Limit: {limit}/min. Please slow down."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Redis unavailable, applying in-memory fallback rate limit: {e}")
        if not _check_memory_fallback(identifier, current_minute):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down."
            )

    return True
