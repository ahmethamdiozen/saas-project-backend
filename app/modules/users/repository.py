import uuid
import json
from sqlalchemy.orm import Session
from app.modules.users.models import User
from app.worker.redis_client import redis_client
from app.core.logging import logger

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: str):
    # 1. Try Cache First
    cache_key = f"user_data:{user_id}"
    cached_user = redis_client.get(cache_key)
    if cached_user:
        try:
            user_dict = json.loads(cached_user)
            # Create a mock user object or handle as dict
            # For SQLAlchemy compatibility, it's safer to just return DB object 
            # but we can skip this function if it's just for auth
            pass
        except: pass

    # 2. Fallback to DB (current simple way)
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, email: str, password_hash: str):
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
