from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user

from models.Auth.user import User


# ✅ IMPORTANT: this must be named "router"
router = APIRouter(
    prefix="/settings",
    tags=["Settings"]
)


# ===============================
# BASIC SETTINGS API (TEST)
# ===============================
@router.get("/")
def get_settings(
    current_user: User = Depends(get_current_user)
):
    return {
        "message": "Settings API working",
        "user_id": current_user.id
    }


# ===============================
# CHANGE USER STATUS (EXAMPLE)
# ===============================
@router.put("/deactivate")
def deactivate_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.status = "inactive"

    db.commit()
    db.refresh(current_user)

    return {
        "message": "User deactivated successfully"
    }


# ===============================
# ACTIVATE USER (EXAMPLE)
# ===============================
@router.put("/activate")
def activate_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.status = "active"

    db.commit()
    db.refresh(current_user)

    return {
        "message": "User activated successfully"
    }


# ===============================
# DELETE ACCOUNT (SIMPLE)
# ===============================
@router.delete("/delete-account")
def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.delete(current_user)
    db.commit()

    return {
        "message": "Account deleted successfully"
    }