import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr | str
    password: str

class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr | str
    created_at: datetime

class LoginRequest(BaseModel):
    email: EmailStr | str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr | str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

