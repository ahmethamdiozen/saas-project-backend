from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.modules.auth.schemas import UserCreate, UserRead, LoginRequest, TokenResponse
from app.modules.auth.service import register_user, login_user, refresh_access_token
from app.db.session import SessionLocal
from app.modules.auth.dependencies import get_refresh_token_from_cookie

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserRead)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db)
):
    try:
        user = register_user(
        db=db,
        email=payload.email,
        password=payload.password
    )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    try:
        access_token, refresh_token = login_user(
            db=db,
            email=payload.email,
            password=payload.password
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30
        ) 
        return {"access_token": access_token}
    
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@router.post("refresh", response_model=TokenResponse)
def refresh(
    refresh_token: str = Depends(get_refresh_token_from_cookie),
    db: Session = Depends(get_db)
):
    try:
        new_access_token = refresh_access_token(
            db,
            raw_refresh_token=refresh_token
        )
        return {"access_token": new_access_token}
    
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )