from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db
from models.Auth.user import User
from services.Auth.superadminservices import super_admin_required
from core.security import validate_mobile
from models.Auth.user_session import UserSession
from schemas.Auth.SendOTPSchema import  UpdateUserSchema
router = APIRouter(
    prefix="/auth",
    tags=["SuperAdmin Access"]
)
# ======================================================
# ADMIN — GET USERS
# ======================================================

@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(super_admin_required),
):
    users = db.query(User).filter(User.role == "USER").all()

    return {
        "count": len(users),
        "users": [
            {
                "id": u.id,
                "mobile_number": u.mobile_number,
                "username": u.username,
                "role": u.role,
                "device_id": u.device_id,
            }
            for u in users
        ],
    }


@router.get("/users/by-mobile/{mobile_number}")
def get_user_by_mobile(
    mobile_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(super_admin_required),
):  
    validate_mobile(mobile_number)

    user = db.query(User).filter(
        User.mobile_number == mobile_number,
        User.role == "USER"
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "id": user.id,
        "mobile_number": user.mobile_number,
        "username": user.username,
        "role": user.role,
        "device_id": user.device_id,
    }

# ======================================================
#ADMIN-UPDATE USERNAME BY MOBILE NUMBER
# ======================================================
@router.put("/users/by-mobile/{mobile_number}",
    status_code=status.HTTP_200_OK
)
def update_user_by_mobile(
    mobile_number: str,
    payload: UpdateUserSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(super_admin_required),
):
    # Validate mobile number
    validate_mobile(mobile_number)
 
    
    user = db.query(User).filter(
        User.mobile_number == mobile_number,
        User.role == "USER"
    ).first()
 
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    update_data = payload.dict(exclude_unset=True)
 
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update"
        )
 

    for field, value in update_data.items():
        setattr(user, field, value)
 
    db.commit()
    db.refresh(user)
 
 
 
    return {
        "message": "User updated successfully",
        "user": {
            "id": user.id,
            "mobile_number": user.mobile_number,
            "username": user.username,
            "role": user.role,
            "device_id": user.device_id,
            "is_active": user.is_active,
        }
    }
 
 
# ======================================================
# ADMIN — DELETE USER BY MOBILE NUMBER
# ======================================================

@router.delete("/users/by-mobile/{mobile_number}")
def delete_user_by_mobile(
    mobile_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(super_admin_required),
):

    validate_mobile(mobile_number)

    user = db.query(User).filter(
        User.mobile_number == mobile_number,
        User.role == "USER"
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    # delete sessions first
    db.query(UserSession).filter(
        UserSession.user_id == user.id
    ).delete()

    # delete user
    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}
