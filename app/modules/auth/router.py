from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.modules.auth.schemas import UserCreate, UserRead, LoginRequest, TokenResponse
from app.modules.auth.service import register_user, login_user
from app.db.session import SessionLocal

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