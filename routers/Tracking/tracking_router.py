from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from models.Auth.user import User

from services.Tracking.tracking_service import TrackingService
from schemas.Tracking.tracking_schema import CreateTrackingRequest              

router = APIRouter(prefix="/loan", tags=["Loan Tracking"])


@router.get("/applications")
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TrackingService.list_applications(db, current_user.id)


@router.get("/application/{application_id}/status")
def get_status(
    application_id: str,
    db: Session = Depends(get_db),
):
    return TrackingService.get_current_status(db, application_id)


@router.get("/application/{application_id}/timeline")
def get_timeline(
    application_id: str,
    db: Session = Depends(get_db),
):
    return TrackingService.get_timeline(db, application_id)


@router.post("/application")
def create_tracking(
    request: CreateTrackingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return TrackingService.create_tracking_entry(
        db=db,
        user_id=current_user.id,  # from JWT token
        loan_origination_id=request.loan_origination_id,
        loan_amount=request.loan_amount,
        tenure=request.tenure_months,
    )