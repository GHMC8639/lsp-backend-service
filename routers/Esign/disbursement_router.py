from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from core.database import get_db
from services.Esign.disbursement_service import DisbursementService

from schemas.Esign.disbursement_schema import (
    DisbursementConfirmRequest,
    DisbursementConfirmResponse,
    DisbursementStatusResponse
)

# ✅ ADD THIS
from core.permissions import user_required

router = APIRouter(
    prefix="/api/v1/loan/disbursement",
    tags=["Disbursement"]
)


def get_disbursement_service() -> DisbursementService:
    return DisbursementService()


# ------------------------------------------------
# GET DISBURSEMENT STATUS (USER + ADMIN)
# ------------------------------------------------
@router.get(
    "/{loan_id}/status",
    response_model=DisbursementStatusResponse
)
def get_disbursement_status(
    loan_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    service: DisbursementService = Depends(get_disbursement_service),

    # ✅ allow all logged-in users
    current_user=Depends(user_required)
):
    return service.get_status(loan_id, db)


# ------------------------------------------------
# CONFIRM DISBURSEMENT (ADMIN ONLY)
# ------------------------------------------------
@router.post(
    "/confirm",
    response_model=DisbursementConfirmResponse
)
def confirm_disbursement(
    payload: DisbursementConfirmRequest,
    db: Session = Depends(get_db),
    service: DisbursementService = Depends(get_disbursement_service),

    # ✅ restrict access
    current_user=Depends(user_required)
):
    return service.confirm(payload.loan_id, db)