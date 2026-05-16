from sqlalchemy.orm import Session
from models.Auth.user import User
from fastapi import HTTPException
import random
from datetime import datetime, timedelta

from core.email_service import sendmail

OTP_EXPIRY_MINUTES = 5


def update_user_profile(db: Session, user: User, data: dict):

    if "mail" in data:
        raise HTTPException(
            status_code=400,
            detail="Use OTP verification API to update email"
        )

    for key, value in data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user


def delete_user_account(db: Session, user: User):
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


def send_otp_to_old_email(db: Session, user: User):

    if user.otp_expiry and datetime.utcnow() < (
        user.otp_expiry - timedelta(minutes=4, seconds=30)
    ):
        raise HTTPException(
            status_code=400,
            detail="Please wait before requesting OTP again"
        )

    otp = str(random.randint(100000, 999999))

    user.email_otp = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    db.commit()

    email_sent = sendmail(
        to=user.mail,
        subject="OTP Verification",
        body=f"Your OTP is {otp}. It is valid for 5 minutes."
    )

    if not email_sent:
        raise HTTPException(
            status_code=500,
            detail="Failed to send OTP email"
        )

    return {
        "status": "success",
        "message": "OTP sent to registered email"
    }


def verify_otp_and_update_email(
    db: Session,
    user: User,
    new_email: str,
    otp: str
):

    if not user.email_otp or not user.otp_expiry:
        raise HTTPException(status_code=400, detail="OTP not generated")

    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired")

    if user.email_otp != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if user.mail == new_email:
        raise HTTPException(
            status_code=400,
            detail="New email must be different"
        )

    existing = db.query(User).filter(User.mail == new_email).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    user.mail = new_email
    user.email_otp = None
    user.otp_expiry = None
    user.email_verified = True

    db.commit()
    db.refresh(user)

    return {
        "status": "success",
        "message": "Email updated successfully",
        "email": user.mail
    }