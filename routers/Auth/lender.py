from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from models.Auth.lender import Lender
from models.Auth.user import User
from schemas.Auth.lenderregisterschema import LenderCreate, LenderResponse, LenderUpdate
from services.Auth.superadminservices import super_admin_required, lender_required
from core.security import hash_password,validate_mobile,validate_password_length
from core.dependencies import get_current_user

router = APIRouter(tags=["SuperAdmin-Lenders createdits-deleted"], prefix="/lenders")


# ======================================================
# CREATE LENDER — SUPERADMIN ONLY
# ======================================================
@router.post("/create", response_model=LenderResponse, status_code=status.HTTP_201_CREATED)
def create_lender(
    lender_data: LenderCreate,
    db: Session = Depends(get_db),
    superadmin = Depends(super_admin_required),
):
    #  VALIDATIONS
    validate_mobile(lender_data.mobile_number)
    validate_password_length(lender_data.password)

    #  CHECK IF LOGIN USER EXISTS
    existing_user = db.query(User).filter(
        User.mobile_number == lender_data.mobile_number,User.role == "LENDER"
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    #  CREATE LOGIN USER
    user = User(
        mobile_number=lender_data.mobile_number,
        username=lender_data.company_name.lower(),
        password_hash=hash_password(lender_data.password),
        role="LENDER",
        device_id="lender-device",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    #  CREATE LENDER PROFILE (MATCHES MODEL)
    lender = Lender(
        user_id=user.id,
        company_name=lender_data.company_name,
        gst_number=lender_data.gst_number,
        address=lender_data.address,
        is_active=False,
        is_verified=False,
        is_blocked=False,
    )

    db.add(lender)
    db.commit()
    db.refresh(lender)

    return lender


# ======================================================
# UPDATE LENDER
# ======================================================
@router.put("/update/{company_name}", response_model=LenderResponse)
def update_lender(
    company_name: str,
    lender_data: LenderUpdate,
    db: Session = Depends(get_db),
    superadmin = Depends(super_admin_required),
):

    lender = db.query(Lender).join(User).filter(
        Lender.company_name == company_name,
        User.role == "LENDER"
    ).first()

    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")

    update_data = lender_data.dict(exclude_unset=True)

    # 🔹 Update Lender table
    for key, value in update_data.items():
        setattr(lender, key, value)

    # 🔹 If company_name updated → also update Users table
    if "company_name" in update_data:
        lender.user.username = update_data["company_name"]
        update_data = lender_data.dict(exclude_unset=True)

    for key, value in update_data.items():
        if key == "company_name":
            value = value.lower().strip()   # convert to small letters
            lender.user.username = value   # update users table also
        setattr(lender, key, value)
        
    

    db.commit()
    db.refresh(lender)

    return lender

# ======================================================
# DELETE LENDER
# ======================================================
@router.delete("/delete/{company_name}")
def delete_lender(
    company_name: str,
    db: Session = Depends(get_db),
    superadmin = Depends(super_admin_required),
):
    lender = db.query(Lender).join(User).filter(
    Lender.company_name == company_name,
    User.role == "LENDER").first()

    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")

    user_id = lender.user_id

    # 1️⃣ delete child first
    db.delete(lender)
    db.commit()

    # 2️⃣ then delete parent
    db.query(User).filter(User.id == user_id).delete()
    db.commit()

    return {
    
            "message": "Lender deleted successfully",
            "id": lender.id,
            "company_name": lender.company_name,
            }

    



# ==========================GET ALL LENDERS============================
@router.get(
    "/lenders",
    status_code=status.HTTP_200_OK
)
def get_all_lenders(
    db: Session = Depends(get_db),
    current_user = Depends(super_admin_required),
):
    lenders = db.query(Lender).join(User, Lender.user_id == User.id).filter(User.role == "LENDER").all()

    return {
        "count": len(lenders),
        "lenders": [
            {
                "id": lender.id,
                "company_name": lender.company_name,
                "gst_number": lender.gst_number,
                "address": lender.address,
                "created_at": lender.created_at,
            }
            for lender in lenders
        ]
    }
# ==========================GET LENDER BY COMPANY NAME============================
@router.get("/lenders/{company_name}", status_code=status.HTTP_200_OK)
def get_lender_by_company_name(
    company_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(super_admin_required),
):
    lender = db.query(Lender).join(User).filter(
    Lender.company_name == company_name,
    User.role == "LENDER").first()

    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")

    return {
        "id": lender.id,
        "company_name": lender.company_name,
        "gst_number": lender.gst_number,
        "address": lender.address,
        "created_at": lender.created_at,
    }

# ==========================GET LENDER BY USER MOBILE NUMBER============================

@router.get("/users/{mobile_number}")
def lender_get_user_details(
    mobile_number: str,   
    db: Session = Depends(get_db),
    current_user: User = Depends(lender_required),
):

    validate_mobile(mobile_number)

    
    user = db.query(User).filter(
        User.mobile_number == mobile_number,
        User.role == "USER"
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "device_id": user.device_id
    }
   
