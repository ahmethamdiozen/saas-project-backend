import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr | str
    password: str

class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr | str
    is_verified: bool
    created_at: datetime

class LoginRequest(BaseModel):
    email: EmailStr | str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

