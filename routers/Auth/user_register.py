from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from core.database import SessionLocal
from models.Auth.user import User
from datetime import datetime, timedelta
from core.config import settings

from models.Auth.user_session import UserSession
from schemas.Auth.RegisterSchema import RegisterSchema
from schemas.Auth.SendOTPSchema import SendOTPSchema, VerifyOTPSchema

import random
from core.security import (
    hash_password,
    create_access_token,
    create_refresh_token,
    validate_mobile,
    validate_password_length,
)

from services.Auth.verify_otp_services import (
    send_otp,
    resend_otp,
    verify_otp,
    remaining_attempts,
)
router = APIRouter(
    prefix="/auth",
    tags=["User Registration process"]
)


# ======================================================
# DB Dependency
# ======================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ======================================================
# REGISTER (SAVE TEMP DATA IN OTP TABLE)
# ======================================================
@router.post("/register")
def register_user(data: RegisterSchema, db: Session = Depends(get_db)):

    validate_mobile(data.mobile_number)
    validate_password_length(data.password)

    existing_user = db.query(User).filter(
        User.mobile_number == data.mobile_number
    ).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    # 🔥 Send OTP (Cloud Redis)
    success, message = send_otp(data.mobile_number)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "step": "OTP_SENT",
        "message": message
    }
# ======================================================
# VERIFY OTP + CREATE USER
# ======================================================
@router.post("/verify-otp")
def verify_otp_api(data: VerifyOTPSchema, db: Session = Depends(get_db)):

    # 1️⃣ Verify OTP from Cloud Redis
    if not verify_otp(data.mobile_number, data.otp):

        attempts_left = remaining_attempts(data.mobile_number)

        if attempts_left == 0:
            raise HTTPException(
                status_code=403,
                detail="Blocked for 24 hours"
            )

        raise HTTPException(
            status_code=400,
            detail=f"Invalid OTP. Attempts left: {attempts_left}"
        )

    # 2️⃣ Check if user already exists
    user = db.query(User).filter(
        User.mobile_number == data.mobile_number
    ).first()

    # 3️⃣ If NOT exist → create new user (registration flow)
    if not user:
        user = User(
            mobile_number=data.mobile_number,
            username=data.username,  # Default username = mobile number
            password_hash=hash_password(data.password),
            device_id=data.device_id,
            role="USER"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4️⃣ Generate Tokens
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    expires_at = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    session = UserSession(
        user_id=user.id,
        session_token=access_token,
        refresh_token=refresh_token,
        is_active=True,
        expires_at=expires_at,
        device_id=data.device_id,
        user_agent="User Registration"

    )

    db.add(session)
    db.commit()
    # 6️⃣ Return tokens
    
    return {
        "message": "OTP verified successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
# ======================================================
# RESEND OTP    
# ======================================================

@router.post("/resend-otp")
def resend_otp_api(data: SendOTPSchema):

    validate_mobile(data.mobile_number)

    result = resend_otp(data.mobile_number)

    return {
        "step": "OTP_RESENT",
        "message": result["message"],
        "resend_attempts_left":
            result["remaining_resend_attempts"]
    }

