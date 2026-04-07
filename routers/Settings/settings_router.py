from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.permissions import user_required

from models.Auth.user import User
from models.Settings.user_settings import UserSettings
from schemas.Settings.common_response import CommonResponse
from schemas.Settings.settings_schema import SettingsUpdate
from schemas.Settings.settings_response_schema import SettingsResponse
from services.Settings.settings_service import (
    get_user_settings,
    update_user_settings
)
router = APIRouter(
    prefix="/user/settings",
    tags=["Settings"]
)


@router.get("/", response_model=SettingsResponse)
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


@router.put("/")
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

    update_data = data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(settings, key, value)

    db.commit()
    db.refresh(settings)

    return {"message": "Settings updated successfully"}
@router.get("/", response_model=CommonResponse)
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(user_required)):
    settings = get_user_settings(db, current_user.id)

    return CommonResponse(
        success=True,
        message="Settings fetched successfully",
        data=settings
    )


@router.put("/", response_model=CommonResponse)
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    settings = update_user_settings(
        db,
        current_user.id,
        data.dict(exclude_unset=True)
    )

    return CommonResponse(
        success=True,
        message="Settings updated successfully",
        data=settings
    )