from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user

from models.Auth.user import User
from models.Eligibility.credit_profile import CreditProfile

from repositories.Eligibility.credit_repository import CreditRepository


router = APIRouter(
    prefix="/credit",
    tags=["Credit Profile"]
)


# -------------------------------------------------------
# Generate Credit Profile
# -------------------------------------------------------
@router.post("/generate")
def generate_credit_profile(
    force_refresh: bool = Query(
        default=False,
        description="Generate new credit profile even if one already exists"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id

    existing_profile = CreditRepository.get_latest_credit_profile(db, user_id)

    # If profile exists and refresh not requested
    if existing_profile and not force_refresh:
        return {
            "message": "Credit profile already exists. Use ?force_refresh=true to regenerate.",
            "credit_profile_id": existing_profile.id,
            "credit_score": existing_profile.credit_score,
            "bureau_name": existing_profile.bureau_name,
            "total_active_loans": existing_profile.total_active_loans,
            "total_existing_emi": float(existing_profile.total_existing_emi or 0),
        }

    # Create new dummy profile
    profile: CreditProfile = CreditRepository.create_dummy_credit_profile(
        db=db,
        user_id=user_id
    )

    return {
        "message": "Credit profile created successfully",
        "credit_profile_id": profile.id,
        "credit_score": profile.credit_score,
        "bureau_name": profile.bureau_name,
        "total_active_loans": profile.total_active_loans,
        "total_existing_emi": float(profile.total_existing_emi or 0),
    }


# -------------------------------------------------------
# Get Current User Credit Profile
# -------------------------------------------------------
@router.get("/me")
def get_credit_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id

    profile = CreditRepository.get_latest_credit_profile(db, user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit profile not found. Generate one first."
        )

    return {
        "credit_profile_id": profile.id,
        "credit_score": profile.credit_score,
        "bureau_name": profile.bureau_name,
        "total_active_loans": profile.total_active_loans,
        "total_existing_emi": float(profile.total_existing_emi or 0),
        "pulled_at": profile.pulled_at
    }