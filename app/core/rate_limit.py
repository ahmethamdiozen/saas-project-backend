import time
from fastapi import HTTPException, status, Depends
from starlette.requests import HTTPConnection
from sqlalchemy.orm import Session
from app.worker.redis_client import redis_client
from app.core.logging import logger
from app.db.session import get_db
from app.modules.subscriptions.service import get_user_active_subscription
from app.core.security import decode_token

# Default rate limits for unauthenticated users (per IP) - INCREASED FOR DEV
DEFAULT_ANONYMOUS_LIMIT = 500

async def rate_limiter(
    request: HTTPConnection,
    db: Session = Depends(get_db)
):
    # Identifiers
    user_id = None
    limit = DEFAULT_ANONYMOUS_LIMIT
    identifier = f"rate_limit:ip:{request.client.host if request.client else 'unknown'}"

    try:
        # 1. Try to get user from cookie first, then Authorization header
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
        # If anything fails during identification, we fallback to IP-based limit
        logger.debug(f"Rate limiter identification fallback: {e}")
        pass

    # 2. Redis-based Counter
    current_minute = int(time.time() / 60)
    key = f"{identifier}:{current_minute}"

    try:
        # Atomic increment
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
        # If Redis is down, we allow the request to pass
        logger.error(f"Redis rate limiter technical error: {e}")
        pass

    return True
