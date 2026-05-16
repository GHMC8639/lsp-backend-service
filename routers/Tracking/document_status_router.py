# routers/document_status_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db

from repositories.Tracking.loan_application_repo import LoanApplicationRepository
from services.Tracking.document_status_service import DocumentStatusService

router = APIRouter(
    prefix="/applications",
    tags=["Application Tracking"]
)


@router.get("/{application_id}/document-status")
def get_document_status(application_id: int, db: Session = Depends(get_db)):
    """
    Get document status + rejection reasons for UI
    """

    # 🔍 Fetch application
    application = LoanApplicationRepository.get_by_id(db, application_id)

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # 🔥 Get document status response
    result = DocumentStatusService.get_document_status(db, application)

    return result