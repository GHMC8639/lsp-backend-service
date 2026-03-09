from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.Loan_application.loan_application_references import LoanApplicationReference
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker
from models.Loan_application.loan_application import LoanApplication
from core.enums import LoanApplicationStatus, LoanApplicationStep, enum_value


def validate_final_submission(
    db: Session,
    application: LoanApplication,
    tracker: LoanApplicationStepTracker):

    if application.application_status != enum_value(LoanApplicationStatus.DRAFT):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application already submitted")

    if not tracker.loan_details_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "pending_step": enum_value(LoanApplicationStep.LOAN_DETAILS),
                "message": "Loan details not completed"
            })

    if not tracker.purpose_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "pending_step": enum_value(LoanApplicationStep.PURPOSE),
                "message": "Loan purpose not completed"
            })

    if not tracker.references_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "pending_step": enum_value(LoanApplicationStep.REFERENCES),
                "message": "References not completed"
            })

    if not tracker.declaration_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "pending_step": enum_value(LoanApplicationStep.DECLARATION),
                "message": "Declaration not completed"
            })

    # check declaration record exists and locked
    if not application.declaration or not application.declaration.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "pending_step": enum_value(LoanApplicationStep.DECLARATION),
                "message": "Declaration confirmation pending"
            })

    references = (
        db.query(LoanApplicationReference)
        .filter(LoanApplicationReference.application_id == application.id)
        .all())

    if len(references) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly 2 references are required")

    if not all(ref.is_verified for ref in references):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All references must be OTP verified")

    return True
