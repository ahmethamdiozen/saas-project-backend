from sqlalchemy.orm import Session
from app.modules.users.repository import (
    get_user_by_email,
    create_user
)
from app.core.security import ( 
    hash_password, 
    verify_password, 
    create_access_token, 
    hash_refresh_token, 
    generate_refresh_token
)
from app.modules.auth.repository import (
    create_refresh_token,
    get_valid_refresh_token
)

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

def login_user(db: Session, *, email: str, password: str):
    user = get_user_by_email(db, email)

    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    raw_refresh_token = generate_refresh_token()
    hashed_refresh_token = hash_refresh_token(raw_refresh_token)

    create_refresh_token(db, user_id=user.id, token_hash=hashed_refresh_token)


    return access_token, raw_refresh_token

def refresh_access_token(db, *, raw_refresh_token: str) -> str:
    token_hash = hash_refresh_token(raw_refresh_token)

    stored_token = get_valid_refresh_token(db, token_hash)

    if not stored_token:
        raise ValueError("Invalid refresh token")
    
    user_id = stored_token.user_id

    new_access_token = create_access_token(
        data={"sub": str(user_id)}
    )

    return new_access_token