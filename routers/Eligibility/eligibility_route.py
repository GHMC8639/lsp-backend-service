from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles

from models.Auth.user import User
from services.Eligibility.eligibility_service import (
    EligibilityService,
    CREDIT_SCORE_TIERS,
    get_apr
)

router = APIRouter(
    prefix="/eligibility",
    tags=["Loan Eligibility"]
)


# =====================================================
# CHECK ELIGIBILITY FOR LOGGED-IN USER
# =====================================================
@router.post("/check")
def check_loan_eligibility(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    """
    Checks loan eligibility automatically for the logged-in user.

    Credit Score → Approved Amount:
        >= 800  → ₹20,000
        >= 750  → ₹15,000
        >= 700  → ₹10,000
        >= 650  → ₹5,000
        < 650   → REJECTED
    """

    try:
        eligibility = EligibilityService.check_eligibility(
            db=db,
            user=current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    status = eligibility.eligibility_status

    # =====================================
    # REJECTED CASE
    # =====================================
    if status == "REJECTED":
        return {
            "user_id": current_user.id,
            "eligibility_status": status,
            "failure_reason": eligibility.failure_reason,
            "credit_summary": {
                "current_score": eligibility.credit_score_used,
                "bureau": eligibility.bureau_name,
            },
            "credit_score_tiers": [
                {
                    "min_score": score,
                    "max_loan_amount": amount
                }
                for score, amount in CREDIT_SCORE_TIERS
            ],
            "message": "You are not eligible for a loan based on your current credit score."
        }

    # =====================================
    # APPROVED CASE
    # =====================================
    approved_amount = float(eligibility.max_eligible_amount or 0)

    return {
        "user_id": current_user.id,
        "eligibility_status": status,
        "loan_offer": {
            "approved_amount": approved_amount,
            "annual_interest_rate": get_apr(),
        },
        "credit_summary": {
            "current_score": eligibility.credit_score_used,
            "bureau": eligibility.bureau_name,
        },
        "message": "You are eligible for a loan. Proceed to EMI calculation."
    }