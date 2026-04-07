from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.session import get_db
from schemas.Eligibility.eligibility import (
    EligibilityDecisionCreate,
    EligibilityDecisionResponse
)
from services.Eligibility.eligibility_service import EligibilityService


router = APIRouter(
    prefix="/loan/eligibility",
    tags=["Loan_Eligibility"])

@router.post("/check/{user_profile_id}",
    response_model=EligibilityDecisionResponse)

def check_eligibility(
    payload: EligibilityDecisionCreate,
    db: Session = Depends(get_db)
):
    return LoanEligibilityService.check_eligibility(
        db=db,
        payload=payload)


@router.get(
    "/{eligibility_id}",
    response_model=EligibilityDecisionResponse
)
def get_eligibility(
    eligibility_id: int,
    db: Session = Depends(get_db)
):
    eligibility = LoanEligibilityService.get_by_id(
        db=db,
        eligibility_id=eligibility_id
    )

    if not eligibility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eligibility not found"
        )

    return eligibility
