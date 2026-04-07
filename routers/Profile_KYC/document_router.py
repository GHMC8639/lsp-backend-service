from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from schemas.Profile_KYC.document_schema import BulkDocumentUploadResponse, SingleDocumentResult, AllDocumentsResponse, DocumentListItem
from services.Profile_KYC.document_upload_service import DocumentUploadService

router = APIRouter(prefix="/kyc/documents", tags=["Document Upload"])


# =====================================================
# UPLOAD DOCUMENTS
# =====================================================
@router.post("/upload", response_model=BulkDocumentUploadResponse)
async def upload_documents(
    pan_card: Optional[UploadFile] = File(None),
    aadhaar_front: Optional[UploadFile] = File(None),
    aadhaar_back: Optional[UploadFile] = File(None),
    income_proof: Optional[UploadFile] = File(None),
    income_type: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),  
):
    profile = current_user.profile

    if not profile:
        raise HTTPException(404, "KYC profile not found")

    files_provided = [f for f in [pan_card, aadhaar_front, aadhaar_back, income_proof] if f and f.filename]
    if not files_provided:
        raise HTTPException(400, "No files provided")

    IMAGE_MAX = 2 * 1024 * 1024
    PDF_MAX   = 3 * 1024 * 1024

    for file, label, max_bytes in [
        (pan_card,      "PAN Card",      IMAGE_MAX),
        (aadhaar_front, "Aadhaar Front", IMAGE_MAX),
        (aadhaar_back,  "Aadhaar Back",  IMAGE_MAX),
        (income_proof,  "Income Proof",  PDF_MAX),
    ]:
        if file and file.filename:
            content = await file.read()
            if len(content) > max_bytes:
                raise HTTPException(400, f"{label} too large")
            await file.seek(0)

    try:
        result = DocumentUploadService.bulk_upload_documents(
            db=db,
            user_id=profile.user_id, 
            pan_card=pan_card,
            aadhaar_front=aadhaar_front,
            aadhaar_back=aadhaar_back,
            income_proof=income_proof,
            income_type=income_type,
        )

        uploaded = [SingleDocumentResult(**doc) for doc in result["uploaded_documents"]]

        return BulkDocumentUploadResponse(
            user_id=result["user_id"],
            email=result["email"],
            uploaded_documents=uploaded,
            total_uploaded=result["total_uploaded"],
            skipped_documents=result["skipped_documents"],
            missing_documents=result["missing_documents"],
            all_required_uploaded=result["all_required_uploaded"],
            message=result["message"],
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Document upload failed: {exc}")


# =====================================================
# LIST DOCUMENTS
# =====================================================
@router.get("/list", response_model=AllDocumentsResponse)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    profile = current_user.profile

    if not profile:
        raise HTTPException(404, "KYC profile not found")

    try:
        result = DocumentUploadService.list_documents(
            db=db,
            user_id=profile.user_id 
        )

        documents = [DocumentListItem(**doc) for doc in result["documents"]]

        return AllDocumentsResponse(
            user_id=result["user_id"],
            email=result["email"],
            documents=documents,
            total_documents=result["total_documents"],
            required_documents=result["required_documents"],
            missing_documents=result["missing_documents"],
            all_approved=result["all_approved"],
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(500, "Failed to retrieve documents")


# =====================================================
# DELETE DOCUMENT
# =====================================================
@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    profile = current_user.profile

    if not profile:
        raise HTTPException(404, "KYC profile not found")

    try:
        return DocumentUploadService.delete_document(
            db=db,
            document_id=document_id,
            user_id=profile.user_id 
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(500, "Failed to delete document")