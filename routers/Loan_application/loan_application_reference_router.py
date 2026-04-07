from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from core.session import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from core.enums import ReferenceRelation

from services.Loan_application.loan_application_reference_service import (
    LoanApplicationReferenceService,
)

from schemas.Loan_application.loan_application_references import (
    LoanApplicationReferenceResponse,
)

router = APIRouter(
    prefix="/loan/application",
    tags=["Loan Application References"],
)


# -----------------------------------------------------
# Save References (USER ONLY - Auto Draft Detection)
# -----------------------------------------------------
@router.put(
    "/references",
    response_model=list[LoanApplicationReferenceResponse],
)
def save_references(
    # Reference 1
    ref1_name: str = Form(...),
    ref1_mobile_number: str = Form(...),
    ref1_relation_type: ReferenceRelation = Form(...),
    ref1_is_emergency_contact: bool = Form(...),

    # Reference 2
    ref2_name: str = Form(...),
    ref2_mobile_number: str = Form(...),
    ref2_relation_type: ReferenceRelation = Form(...),
    ref2_is_emergency_contact: bool = Form(...),

    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    return LoanApplicationReferenceService.save_references_form(
        db=db,
        user_id=current_user.id,
        ref1_name=ref1_name,
        ref1_mobile_number=ref1_mobile_number,
        ref1_relation_type=ref1_relation_type,
        ref1_is_emergency_contact=ref1_is_emergency_contact,
        ref2_name=ref2_name,
        ref2_mobile_number=ref2_mobile_number,
        ref2_relation_type=ref2_relation_type,
        ref2_is_emergency_contact=ref2_is_emergency_contact,
    )


# -----------------------------------------------------
# Get References (USER ONLY - Auto Draft Detection)
# -----------------------------------------------------
@router.get(
    "/references",
    response_model=list[LoanApplicationReferenceResponse],
)
def get_references(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    return LoanApplicationReferenceService.get_references(
        db=db,
        user_id=current_user.id,
    )