from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.session import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from schemas.Loan_application.loan_application_purpose import (
    LoanApplicationPurposeCreate,
    LoanApplicationPurposeResponse,
)

from services.Loan_application.loan_application_purpose_service import (
    LoanApplicationPurposeService,
)

router = APIRouter(
    prefix="/loan/application",
    tags=["Loan Application Purpose"],
)


# -----------------------------------------------------
# Save Purpose (USER ONLY - Latest Draft Auto Detect)
# -----------------------------------------------------
@router.put(
    "/purpose",
    response_model=LoanApplicationPurposeResponse,
)
def save_loan_purpose(
    data: LoanApplicationPurposeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    result = LoanApplicationPurposeService.save_purpose(
        db=db,
        user_id=current_user.id,
        purpose_code=data.purpose_code,
        purpose_description=data.purpose_description,
    )

    return LoanApplicationPurposeResponse(
        application_id=result["application_id"],
        purpose_code=result["purpose_code"],
        purpose_description=result["purpose_description"],
        message=result["message"],
    )


# -----------------------------------------------------
# Get Purpose (USER ONLY - Latest Draft Auto Detect)
# -----------------------------------------------------
@router.get(
    "/purpose",
    response_model=LoanApplicationPurposeResponse,
)
def get_loan_purpose(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    result = LoanApplicationPurposeService.get_purpose(
        db=db,
        user_id=current_user.id,
    )

    return LoanApplicationPurposeResponse(
        application_id=result.application_id,
        purpose_code=result.purpose_code,
        purpose_description=result.purpose_description,
        message="Purpose fetched successfully",
    )