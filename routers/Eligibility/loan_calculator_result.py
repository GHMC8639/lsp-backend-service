from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from services.Eligibility.loan_service import LoanCalculationService

router = APIRouter(
    prefix="/loan",
    tags=["Loan Calculator"]
)


# =====================================================
# GET LOAN CALCULATION (LOGGED-IN USER ONLY)
# =====================================================
@router.get("/result/me")
def get_loan_calculation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    """
    Fetches the most recent EMI calculation
    for the logged-in USER only.
    """

    record = LoanCalculationService.get_calculation(
        db=db,
        user_id=current_user.id
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail=(
                "No EMI calculation found. "
                "Please use POST /loan/calculate first."
            ),
        )

    return {
        "status": "success",
        "data": {
            "id": record.id,
            "requested_amount": record.requested_amount,
            "eligible_amount": record.eligible_amount,
            "tenure_months": record.tenure_months,
            "interest_rate_pa": record.interest_rate_pa,
            "monthly_emi": record.monthly_emi,
            "total_repayment": record.total_repayment,
            "total_interest": record.total_interest,
            "status": record.status,
        },
    }