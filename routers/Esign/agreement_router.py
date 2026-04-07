from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from core.database import get_db

from services.Esign.agreement_service import AgreementService
from services.Esign.pdf_generator import PDFGenerator
from services.Esign.loan_client import LoanClient

from schemas.Esign.agreement_schema import AgreementResponse

# ✅ ADD THIS
from core.permissions import user_required


router = APIRouter(
    prefix="/loan/agreement",
    tags=["Agreement"]
)


# Dependency Injection
def get_agreement_service() -> AgreementService:
    pdf = PDFGenerator()
    loan_client = LoanClient()
    return AgreementService(pdf=pdf, loan_client=loan_client)


# ------------------------------------------------
# GET AGREEMENT (USER + ADMIN)
# ------------------------------------------------
@router.get("/{loan_id}", response_model=AgreementResponse)
def get_agreement(
    loan_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),

    # ✅ ROLE CHECK
    current_user=Depends(user_required)
):
    return service.fetch_agreement(loan_id, db)


# ------------------------------------------------
# VIEW AGREEMENT PDF (USER + ADMIN)
# ------------------------------------------------
@router.get("/{loan_id}/view")
def view_agreement(
    loan_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),

    # ✅ ROLE CHECK
    current_user=Depends(user_required)
):
    return service.get_agreement_view(loan_id, db)


# ------------------------------------------------
# VERIFY HASH (ADMIN ONLY)
# ------------------------------------------------
@router.get("/{loan_id}/hash")
def verify_hash(
    loan_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),

    # ✅ RESTRICTED ACCESS
    current_user=Depends(user_required)
):
    return service.verify_hash(loan_id, db)