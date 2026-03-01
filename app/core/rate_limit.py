import time
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.worker.redis_client import redis_client
from app.core.logging import logger
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.subscriptions.service import get_user_active_subscription
from app.modules.users.models import User

# Default rate limits for unauthenticated users (per IP)
DEFAULT_ANONYMOUS_LIMIT = 20 # 20 requests per minute

async def rate_limiter(
    request: Request,
    db: Session = Depends(get_db)
):
    # Try to identify user by token (if present)
    user: User | None = None
    try:
        # We manually call this to not raise error if token is missing
        # but capture user if it exists
        from app.modules.auth.dependencies import oauth2_scheme
        from app.core.security import decode_token
        from app.modules.users.repository import get_user_by_id
        
        token = await request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]
            payload = decode_token(token)
            user_id = payload.get("sub")
            if user_id:
                user = get_user_by_id(db, user_id)
    except Exception:
        # If token is invalid or missing, treat as anonymous
        user = None

    if user:
        # Identify by User ID
        identifier = f"rate_limit:user:{user.id}"
        # Get limit from subscription
        active_sub = get_user_active_subscription(db, user.id)
        limit = active_sub.subscription.rate_limit_per_minute if active_sub else 5
    else:
        # Identify by IP
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"rate_limit:ip:{client_ip}"
        limit = DEFAULT_ANONYMOUS_LIMIT

    # Redis-based Fixed Window Counter
    current_minute = int(time.time() / 60)
    key = f"{identifier}:{current_minute}"

    try:
        # Atomic increment
        count = redis_client.incr(key)
        if count == 1:
            # Set TTL for the key to expire after the minute passes
            redis_client.expire(key, 60)
            
        if count > limit:
            logger.warning(f"Rate limit exceeded for {identifier}: {count}/{limit}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Your limit is {limit} per minute."
            )
            
        # Add rate limit info to headers (optional but professional)
        # request.state.rate_limit_info = {"limit": limit, "remaining": limit - count}
        
    except redis.RedisError as e:
        # If Redis is down, we allow the request to pass to ensure availability
        logger.error(f"Redis rate limiter error: {e}")
        pass

    return True
