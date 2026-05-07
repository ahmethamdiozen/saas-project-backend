from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.modules.auth.schemas import UserCreate, UserRead, LoginRequest, TokenResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.modules.auth.service import register_user, login_user, refresh_access_token, logout_user
from app.db.session import get_db
from app.modules.auth.dependencies import get_refresh_token_from_cookie, get_current_user
from app.modules.users.repository import get_user_by_email, get_user_by_id
from app.core.security import hash_password
from app.core.tokens import create_password_reset_token, consume_password_reset_token
from app.core.email import send_password_reset_email
from app.core.config import settings

router = APIRouter()

def set_auth_cookies(response: Response, access_token: str, refresh_token: str = None):
    is_secure = settings.ENVIRONMENT == "production"
    
    # Set Access Token Cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    # Set Refresh Token Cookie (if provided)
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=60 * 60 * 24 * 30 # 30 days
        )

@router.post("/register", response_model=UserRead)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        return register_user(db=db, email=payload.email, password=payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        access_token, refresh_token = login_user(
            db=db,
            email=payload.email,
            password=payload.password
        )
        set_auth_cookies(response, access_token, refresh_token)
        return {"message": "Login successful"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        logout_user(db, raw_refresh_token=refresh_token)
    
    response.delete_cookie(key="access_token", httponly=True, samesite="lax", secure=settings.ENVIRONMENT == "production")
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax", secure=settings.ENVIRONMENT == "production")
    return {"message": "Logged out successfully"}
    
@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if user and user.is_active:
        token = create_password_reset_token(str(user.id))
        send_password_reset_email(user.email, token)
    # Always return the same message to avoid email enumeration
    return {"message": "If that email is registered, you'll receive a reset link shortly"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user_id = consume_password_reset_token(payload.token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password reset successfully"}


@router.post("/refresh")
def refresh(response: Response, refresh_token: str = Depends(get_refresh_token_from_cookie), db: Session = Depends(get_db)):
    try:
        new_access_token = refresh_access_token(db, raw_refresh_token=refresh_token)
        set_auth_cookies(response, new_access_token) # Refresh ONLY access token
        return {"message": "Token refreshed"}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
