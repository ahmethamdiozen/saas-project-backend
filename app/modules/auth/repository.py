from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.modules.auth.models import RefreshToken

REFRESH_TOKEN_EXPIRE_DAYS=30

def create_refresh_token(
        db: Session,
        *,
        user_id,
        token_hash: str,
) -> RefreshToken:
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) 
        + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)

    return refresh_token