
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings
import secrets
import hashlib
import hmac

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    # bcrypt has a 72-byte limit. We truncate to 72 bytes.
    return pwd_context.hash(password.encode("utf-8")[:72])

def verify_password(plain: str, hashed: str) -> bool:
    # bcrypt has a 72-byte limit. We truncate plain password to 72 bytes for verification.
    return pwd_context.verify(plain.encode("utf-8")[:72], hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt

def decode_token(token:str) -> dict:
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)

def hash_refresh_token(token: str) -> str:
    return hmac.new(
        key=SECRET_KEY.encode(),
        msg=token.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()