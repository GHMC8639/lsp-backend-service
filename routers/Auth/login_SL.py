from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from core.database import get_db
from models.Auth.user import User


from core.security import (
    verify_password,
    create_access_token,
    validate_mobile
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    validate_mobile(form_data.username)

    user = db.query(User).filter(
        User.mobile_number == form_data.username
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({
        "sub": str(user.id),
        "role": user.role   # MUST be SUPER_ADMIN
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
    }
