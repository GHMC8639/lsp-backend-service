from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.session import get_db

from services.Loan_application.loan_disbursement_service import LoanDisbursementService
from services.Loan_application.pre_disbursement_service import PreDisbursementService

from schemas.Loan_application.loan_disbursement_schema import (
    DisbursementResponseSchema,
    DisbursementRequestSchema
)
from schemas.Loan_application.loan_predisbursement_schema import (
    PreDisbursementResponseSchema
)

# ✅ ADD THIS
from core.permissions import user_required
from models.Auth.user import User

router = APIRouter(
    prefix="/admin/disbursement",
    tags=["Loan Disbursement"]
)


# ------------------------------------------------
# PREVIEW DISBURSEMENT (ADMIN ONLY)
# ------------------------------------------------
@router.get(
    "/{application_id}",
    response_model=PreDisbursementResponseSchema
)
def preview_charges(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    return PreDisbursementService.get_preview(db, application_id)


# ------------------------------------------------
# DISBURSE LOAN (ADMIN ONLY)
# ------------------------------------------------
@router.post(
    "/{application_id}",
    response_model=DisbursementResponseSchema
)
def disburse_loan(
    application_id: int,
    request: DisbursementRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    return LoanDisbursementService.disburse_loan(
        db=db,
        application_id=application_id,
        payment_mode=request.payment_mode,
        # ✅ optional audit
        processed_by=current_user.id
    )