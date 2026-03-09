from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from services.Eligibility.loan_service import (
    LoanCalculationService,
    ALLOWED_TENURES
)

router = APIRouter(
    prefix="/loan",
    tags=["Loan Calculator"]
)


# =====================================================
# REQUEST MODEL (NO user_id HERE)
# =====================================================
class LoanCalculateRequest(BaseModel):
    """
    EMI is always calculated on the full eligible amount.
    User ID is derived from the JWT token.
    """
    tenure_months: int = Field(
        ...,
        description=f"Tenure in months. Allowed: {ALLOWED_TENURES}",
    )


# =====================================================
# CALCULATE EMI (LOGGED-IN USER ONLY)
# =====================================================
@router.post("/calculate")
def calculate_emi(
    payload: LoanCalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    """
    Calculates EMI for the logged-in USER only.
    """

    if payload.tenure_months not in ALLOWED_TENURES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tenure. Allowed values: {ALLOWED_TENURES}"
        )

    try:
        result = LoanCalculationService.calculate_and_save(
            db=db,
            user_id=current_user.id,
            tenure_months=payload.tenure_months,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    record = result["record"]

    return {
        "status": "success",
        "message": "EMI calculated and saved successfully.",
        "data": {
            "id": record.id,
            "eligible_amount": record.eligible_amount,
            "requested_amount": record.requested_amount,
            "tenure_months": record.tenure_months,
            "interest_rate_pa": record.interest_rate_pa,
            "monthly_emi": record.monthly_emi,
            "total_repayment": record.total_repayment,
            "total_interest": record.total_interest,
            "status": record.status,
            "amortization_schedule": result["amortization_schedule"],
        },
    }