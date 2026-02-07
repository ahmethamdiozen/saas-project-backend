from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.modules.auth.schemas import UserCreate, UserRead
from app.modules.auth.service import register_user
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