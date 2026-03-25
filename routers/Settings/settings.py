from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from  core.database import get_db
from  core.permissions import user_required
from  core.auth import oauth2_scheme

from  models.Auth.user import User
from  models.Settings.user_settings import UserSettings
from  models.Settings.user_session import UserSession

from  schemas.Settings.user_settings import SettingsUpdate

router = APIRouter(
    prefix="/api/v1/user",
    tags=["Settings"],
    dependencies=[Depends(oauth2_scheme)]
)


@router.get("/settings")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()

    if not settings:
        
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings



@router.put("/settings")
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()

    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)

    settings.biometric_enabled = data.biometric_enabled
    settings.pin_enabled = data.pin_enabled
    settings.language = data.language
    settings.push_notification = data.push_notification
    settings.sms_notification = data.sms_notification
    settings.email_notification = data.email_notification

    db.commit()
    db.refresh(settings)

    return {"message": "Settings updated successfully"}



@router.get("/consent-download")
def download_consent_record(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()

    return {
        "user_id": current_user.id,
        "consent_status": "Accepted",
        "language": settings.language if settings else "en"
    }



@router.get("/active-sessions")
def active_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).all()

    return sessions



@router.post("/logout-all")
def logout_all_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id
    ).update({"is_active": False})

    db.commit()

    return {"message": "Logged out from all devices"}