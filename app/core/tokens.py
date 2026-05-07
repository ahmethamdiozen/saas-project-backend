import secrets
from app.worker.redis_client import redis_client

PASSWORD_RESET_TTL = 3600    # 1 hour
EMAIL_VERIFY_TTL = 86400     # 24 hours


def _generate(prefix: str, user_id: str, ttl: int) -> str:
    token = secrets.token_urlsafe(32)
    redis_client.setex(f"{prefix}:{token}", ttl, user_id)
    return token


def _consume(prefix: str, token: str) -> str | None:
    key = f"{prefix}:{token}"
    user_id = redis_client.get(key)
    if user_id:
        redis_client.delete(key)
    return user_id


def create_password_reset_token(user_id: str) -> str:
    return _generate("pwd_reset", user_id, PASSWORD_RESET_TTL)


def consume_password_reset_token(token: str) -> str | None:
    return _consume("pwd_reset", token)


def create_email_verification_token(user_id: str) -> str:
    return _generate("email_verify", user_id, EMAIL_VERIFY_TTL)


def consume_email_verification_token(token: str) -> str | None:
    return _consume("email_verify", token)
