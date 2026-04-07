from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db

from services.Tracking.reupload_service import ReuploadService
from schemas.Tracking.reupload_schema import DocumentReuploadRequest

# ✅ USE RBAC
from core.permissions import user_required
from models.Auth.user import User

# ✅ OPTIONAL (if you want ownership check here)
from models.Loan_application.loan_application import LoanApplication


router = APIRouter(
    prefix="/loan",
    tags=["Document Reupload"]
)


@router.post("/application/{application_id}/reupload")
def reupload_document(
    application_id: int,
    payload: DocumentReuploadRequest,
    db: Session = Depends(get_db),

    # ✅ RBAC
    current_user: User = Depends(user_required)
):
    """
    Allows user to reupload rejected document
    """

    # ------------------------------------------------
    # 🔐 OWNERSHIP CHECK (VERY IMPORTANT)
    # ------------------------------------------------
    application = db.query(LoanApplication).filter(
        LoanApplication.id == application_id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # ✅ USER → only own application
    if current_user.role == "USER" and application.user_profile_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # ------------------------------------------------
    # PROCESS REUPLOAD
    # ------------------------------------------------
    return ReuploadService.submit_reupload(
        db=db,
        application_id=application_id,
        user_id=current_user.id,
        document_type=payload.document_type,
        new_document_url=payload.new_document_url,
        rejection_reason=payload.rejection_reason
    )