from sqlalchemy.orm import Session
from app.modules.users.repository import get_user_by_email, create_user
from app.core.security import hash_password

def register_user(db: Session, *, email: str, password: str):
    existing_user = get_user_by_email(db, email)

    if existing_user:
        raise ValueError("Email already registered")
    
    password_hash = hash_password(password)

    user = create_user(
        db,
        email=email,
        password_hash=password_hash
    )

    return user
    