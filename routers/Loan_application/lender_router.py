from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from services.Loan_application.lender_service import LenderService
from schemas.Loan_application.lender import LenderApplicationListResponse


router = APIRouter(
    prefix="/lender",
    tags=["Lender Dashboard"]
)


# ==============================
# Serializer
# ==============================
def serialize_application(app):
    return {
        "application_id": app.id,
        "reference_number": app.reference_number,
        "approved_amount": float(app.approved_amount),
        "tenure_months": app.requested_tenure_months,
        "application_status": app.application_status.value,
        "submitted_at": app.submitted_at,
    }


# =====================================================
# VIEW ALL SUBMITTED APPLICATIONS (LENDER ONLY)
# =====================================================
@router.get("/applications", response_model=List[LenderApplicationListResponse])
def view_submitted_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    applications = LenderService.get_submitted_applications(db)
    return [serialize_application(app) for app in applications]


# =====================================================
# VIEW MY APPLICATIONS (LENDER ONLY)
# =====================================================
@router.get("/my-applications", response_model=List[LenderApplicationListResponse])
def view_lender_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    applications = LenderService.get_lender_applications(db, current_user.id)
    return [serialize_application(app) for app in applications]


# =====================================================
# PICK APPLICATION (LENDER ONLY)
# =====================================================
@router.post("/pick/{application_id}")
def pick_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    return LenderService.pick_application(
        db,
        application_id,
        current_user.id
    )


# =====================================================
# APPROVE APPLICATION (LENDER ONLY)
# =====================================================
@router.post("/approve/{application_id}")
def approve_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    return LenderService.approve_application(
        db,
        application_id,
        current_user.id
    )


# =====================================================
# REJECT APPLICATION (LENDER ONLY)
# =====================================================
@router.post("/reject/{application_id}")
def reject_application(
    application_id: int,
    rejection_reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    return LenderService.reject_application(
        db,
        application_id,
        current_user.id,
        rejection_reason
    )