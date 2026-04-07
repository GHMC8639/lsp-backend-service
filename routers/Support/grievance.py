from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from models.Support.grievance import Grievance
from schemas.Support.grievance_schema import GrievanceCreate

# ✅ ADD THESE
from core.permissions import user_required
from core.dependencies import get_current_user
from models.Auth.user import User


router = APIRouter(
    prefix="/support/grievance",
    tags=["Grievance Officer"]
)


# ------------------------------------------------
# CREATE GRIEVANCE (USER ONLY)
# ------------------------------------------------
@router.post("/", status_code=201)
def create_grievance(
    data: GrievanceCreate,
    db: Session = Depends(get_db),

    # ✅ Only users can raise grievance
    current_user: User = Depends(user_required)
):
    grievance = Grievance(
        **data.dict(),
        user_id=current_user.id  # ✅ attach user
    )

    db.add(grievance)
    db.commit()
    db.refresh(grievance)

    return grievance


# ------------------------------------------------
# LIST GRIEVANCES
# ------------------------------------------------
@router.get("/")
def list_grievances(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    
    # ✅ ADMIN → see all
    if current_user.role in ["ADMIN", "SUPER_ADMIN"]:
        return db.query(Grievance).all()

    # ✅ USER → see only their grievances
    return db.query(Grievance).filter(
        Grievance.user_id == current_user.id
    ).all()