from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from core.database import get_db
from services.Esign.disbursement_service import DisbursementService

from schemas.Esign.disbursement_schema import (
    DisbursementConfirmRequest,
    DisbursementConfirmResponse,
    DisbursementStatusResponse
)


router = APIRouter(
    prefix="/api/v1/loan/disbursement",
    tags=["Disbursement"]
)


# ------------------------------------------------
# Dependency Injection
# ------------------------------------------------
def get_disbursement_service() -> DisbursementService:
    return DisbursementService()


# ------------------------------------------------
# GET DISBURSEMENT STATUS
# ------------------------------------------------
@router.get("/{loan_id}/status", response_model=DisbursementStatusResponse)
def get_disbursement_status(
    loan_id: int = Path(..., gt=0, description="Loan ID"),
    db: Session = Depends(get_db),
    service: DisbursementService = Depends(get_disbursement_service),
):
    return service.get_status(loan_id, db)


# ------------------------------------------------
# CONFIRM DISBURSEMENT
# ------------------------------------------------
@router.post("/confirm", response_model=DisbursementConfirmResponse)
def confirm_disbursement(
    payload: DisbursementConfirmRequest,
    db: Session = Depends(get_db),
    service: DisbursementService = Depends(get_disbursement_service),
):
    
    # NOTE:
    # Admin/manual trigger only.
    # Primary flow is automatic via e-sign callback.

    return service.confirm(payload.loan_id, db)