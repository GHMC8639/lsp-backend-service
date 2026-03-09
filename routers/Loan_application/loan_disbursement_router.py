from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.session import get_db
from services.Loan_application.loan_disbursement_service import LoanDisbursementService
from schemas.Loan_application.loan_disbursement_schema import (
    DisbursementResponseSchema,
    DisbursementRequestSchema)
from services.Loan_application.pre_disbursement_service import PreDisbursementService
from schemas.Loan_application.loan_predisbursement_schema import (
    PreDisbursementResponseSchema)

router = APIRouter(
    prefix="/admin/disbursement",
    tags=["Loan Disbursement"])


@router.get(
    "/{application_id}",
    response_model=PreDisbursementResponseSchema)

def preview_charges(
    application_id: int,
    db: Session = Depends(get_db)
):
    return PreDisbursementService.get_preview(db, application_id)

@router.post(
    "/{application_id}",
    response_model=DisbursementResponseSchema)

def disburse_loan(
    application_id: int,
    request: DisbursementRequestSchema,  
    db: Session = Depends(get_db)):
    
    return LoanDisbursementService.disburse_loan(
        db=db,
        application_id=application_id,
        payment_mode=request.payment_mode )