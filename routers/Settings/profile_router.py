from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.permissions import user_required
from schemas.Settings.common_response import CommonResponse
from models.Auth.user import User
from schemas.Settings.profile_schema import ProfileUpdate
from services.Settings.profile_service import update_user_profile
from services.Settings.profile_service import delete_user_account

router = APIRouter(
    prefix="/user/profile",
    tags=["Profile"]
)


@router.get("/")
def get_profile(current_user: User = Depends(user_required)):
    return current_user


@router.put("/")
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    update_data = data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)

    return {"message": "Profile updated successfully"}
@router.put("/", response_model=CommonResponse)
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
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
@router.delete("/delete-account", response_model=CommonResponse)
def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    delete_user_account(db, current_user)

    return CommonResponse(
        success=True,
        message="Account deleted successfully",
        data=None
    )