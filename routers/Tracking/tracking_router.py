from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from services.Tracking.tracking_service import TrackingService

from schemas.Tracking.loan_status_schema import LoanStatusResponse
from schemas.Tracking.loan_timeline_schema import LoanStatusHistoryItem
from schemas.Loan_application.loan_application import LoanApplicationBase

# ✅ USE RBAC
from core.permissions import user_required
from models.Auth.user import User

# ✅ For ownership check
from models.Loan_application.loan_application import LoanApplication


router = APIRouter(
    prefix="/loan",
    tags=["Loan Tracking"]
)


# ------------------------------------------------
# GET USER APPLICATIONS
# ------------------------------------------------
@router.get("/applications", response_model=list[LoanApplicationBase])
def get_user_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    # ✅ ADMIN → see all
    if current_user.role in ["ADMIN", "SUPER_ADMIN"]:
        return TrackingService.get_all_applications(db)

    # ✅ USER → only own
    return TrackingService.get_user_applications(
        db=db,
        user_id=current_user.id
    )


# ------------------------------------------------
# GET APPLICATION STATUS
# ------------------------------------------------
@router.get("/application/{application_id}/status", response_model=LoanStatusResponse)
def get_application_status(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    application = db.query(LoanApplication).filter(
        LoanApplication.id == application_id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # ✅ USER → only own application
    if current_user.role == "USER" and application.user_profile_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return TrackingService.get_application_status(
        db=db,
        application_id=application_id,
        user_id=current_user.id
    )


# ------------------------------------------------
# GET APPLICATION TIMELINE
# ------------------------------------------------
@router.get("/application/{application_id}/timeline", response_model=list[LoanStatusHistoryItem])
def get_application_timeline(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    application = db.query(LoanApplication).filter(
        LoanApplication.id == application_id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # ✅ USER → only own
    if current_user.role == "USER" and application.user_profile_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return TrackingService.get_application_timeline(
        db=db,
        application_id=application_id,
        user_id=current_user.id
    )