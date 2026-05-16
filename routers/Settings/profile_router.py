from fastapi import APIRouter, Body, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from core.dependencies import get_current_user
from core.database import get_db

from models.Auth.user_session import UserSession
from models.Auth.user import User

from models.Settings.user_settings import DeleteAccountRequest
from schemas.Settings.common_response import CommonResponse

# ✅ FIXED IMPORT (important)
from schemas.Settings.profile_schema import ProfileUpdate, TempAddressUpdate

from services.Settings.cloudinary_service import upload_image
from services.Settings.profile_service import (
    update_user_profile,
    delete_user_account,
    send_otp_to_old_email,
    verify_otp_and_update_email
)

router = APIRouter(
    prefix="/user/profile",
    tags=["Profile"]
)

# ===============================
# 🔐 EMAIL SCHEMA
# ===============================
class UpdateEmail(BaseModel):
    new_email: EmailStr
    otp: str


# ===============================
# PROFILE APIs
# ===============================

@router.get("/")
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/", response_model=CommonResponse)
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = update_user_profile(
        db,
        current_user,
        data.dict(exclude_unset=True)
    )

    return CommonResponse(
        success=True,
        message="Profile updated successfully",
        data=user
    )


# ===============================
# ✅ TEMP ADDRESS UPDATE (NEW)
# ===============================

@router.put("/temp-address")
def update_temp_address(
    data: TempAddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.temporary_address = data.temporary_address

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Temporary address updated successfully",
        "temporary_address": current_user.temporary_address
    }


# ===============================
# 🔐 EMAIL OTP APIs
# ===============================

@router.post("/send-email-otp", response_model=CommonResponse)
def send_email_otp(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    send_otp_to_old_email(db, current_user)

    return CommonResponse(
        success=True,
        message="OTP sent to registered email",
        data=None
    )


@router.put("/update-email", response_model=CommonResponse)
def update_email(
    payload: UpdateEmail,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_otp_and_update_email(
        db,
        current_user,
        payload.new_email,
        payload.otp
    )

    return CommonResponse(
        success=True,
        message="Email updated successfully",
        data=None
    )


# ===============================
# SESSIONS
# ===============================

@router.get("/active-sessions")
def active_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).all()


@router.post("/logout-all")
def logout_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).update({"is_active": False})

    db.commit()

    return {"message": "Logged out from all devices"}


# ===============================
# PROFILE IMAGE
# ===============================

@router.post("/upload-dp")
async def upload_dp(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    result = upload_image(file.file)

    current_user.profile_image_url = result["secure_url"]

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile image uploaded successfully",
        "url": current_user.profile_image_url
    }


@router.delete("/delete-dp")
async def delete_dp(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.profile_image_url:
        raise HTTPException(status_code=400, detail="No image found")

    current_user.profile_image_url = None
    db.commit()

    return {"message": "Profile image deleted successfully"}


# ===============================
# DELETE ACCOUNT
# ===============================

@router.post("/request-delete-account", response_model=CommonResponse)
def request_delete_account(
    reason: str = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(DeleteAccountRequest).filter(
        DeleteAccountRequest.user_id == current_user.id,
        DeleteAccountRequest.status == "pending"
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Request already pending")

    request = DeleteAccountRequest(
        user_id=current_user.id,
        reason=reason
    )

    db.add(request)
    db.commit()

    return CommonResponse(
        success=True,
        message="Delete request sent to admin",
        data=None
    )