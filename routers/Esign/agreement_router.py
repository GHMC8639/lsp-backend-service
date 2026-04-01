from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from core.database import get_db

from services.Esign.agreement_service import AgreementService
from services.Esign.pdf_generator import PDFGenerator
from services.Esign.loan_client import LoanClient

from schemas.Esign.agreement_schema import AgreementResponse


router = APIRouter(
    prefix="/api/v1/loan/agreement",
    tags=["Agreement"]
)


# Dependency Injection
def get_agreement_service() -> AgreementService:
    pdf = PDFGenerator()
    loan_client = LoanClient()
    return AgreementService(pdf=pdf, loan_client=loan_client)


# Get agreement (generate if not exists)
@router.get("/{loan_id}", response_model=AgreementResponse)
def get_agreement(
    loan_id: int = Path(..., gt=0, description="Loan ID"),
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),
):
    return service.fetch_agreement(loan_id, db)

# ------------------------------------------------
# PDF VIEWER (NEW)
# ------------------------------------------------
@router.get("/{loan_id}/view")
def view_agreement(
    loan_id: int = Path(..., gt=0, description="Loan ID"),
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),
):
    return service.get_agreement_view(loan_id, db)


# Verify agreement hash
@router.get("/{loan_id}/hash")
def verify_hash(
    loan_id: int = Path(..., gt=0, description="Loan ID"),
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),
):
    return service.verify_hash(loan_id, db)