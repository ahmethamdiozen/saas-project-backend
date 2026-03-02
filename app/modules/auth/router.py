from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.modules.auth.schemas import UserCreate, UserRead, LoginRequest, TokenResponse
from app.modules.auth.service import register_user, login_user, refresh_access_token, logout_user
from app.db.session import get_db
from app.modules.auth.dependencies import get_refresh_token_from_cookie
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
    
@router.post("/refresh")
def refresh(response: Response, refresh_token: str = Depends(get_refresh_token_from_cookie), db: Session = Depends(get_db)):
    try:
        new_access_token = refresh_access_token(db, raw_refresh_token=refresh_token)
        set_auth_cookies(response, new_access_token) # Refresh ONLY access token
        return {"message": "Token refreshed"}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
