import uuid
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.users.repository import get_user_by_email
from app.modules.users.schemas import UserRead, ChangePasswordRequest, UpdateProfileRequest, DeleteAccountRequest
from app.modules.auth.repository import revoke_all_user_tokens
from app.core.security import verify_password, hash_password
from app.core.tokens import create_email_verification_token
from app.core.email import send_verification_email
from app.core.config import settings

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserRead)
def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    new_email = payload.email.lower()
    if new_email != current_user.email:
        if get_user_by_email(db, new_email):
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = new_email
        current_user.is_verified = False
        token = create_email_verification_token(str(current_user.id))
        send_verification_email(new_email, token)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.delete("/me")
def delete_account(
    payload: DeleteAccountRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Anonymize PII and deactivate — keeps relational integrity intact
    current_user.email = f"deleted_{current_user.id}@deleted.invalid"
    current_user.password_hash = ""
    current_user.is_active = False
    current_user.stripe_customer_id = None

    revoke_all_user_tokens(db, current_user.id)
    db.commit()

    is_secure = settings.ENVIRONMENT == "production"
    response.delete_cookie("access_token", httponly=True, samesite="lax", secure=is_secure)
    response.delete_cookie("refresh_token", httponly=True, samesite="lax", secure=is_secure)

    return {"message": "Account deleted successfully"}
