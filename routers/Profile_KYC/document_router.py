from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from sqlalchemy.orm import Session
from core.database import get_db
from core.config import settings
from schemas.Profile_KYC.document_schema import (
    AllDocumentsResponse,
    DocumentListItem,
    BulkDocumentUploadResponse,
    BulkDocumentUploadResult,
)
from services.Profile_KYC.document_upload_service import DocumentUploadService
import logging
 
logger = logging.getLogger(__name__)
 
router = APIRouter(prefix="/api/v1/documents", tags=["Document Upload & Verification"])
 
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
VALID_TYPES = ["PAN_CARD", "AADHAAR_FRONT", "AADHAAR_BACK", "SALARY_SLIP", "BANK_STATEMENT"]
 
 
@router.post("/upload/bulk", response_model=BulkDocumentUploadResponse)
async def bulk_upload_documents(
    background_tasks: BackgroundTasks,
    user_id: int = Form(..., description="User ID"),
    document_types: List[str] = Form(
        ...,
        description="List of document types (up to 4): PAN_CARD, AADHAAR_FRONT, AADHAAR_BACK, SALARY_SLIP, BANK_STATEMENT",
    ),
    files: List[UploadFile] = File(..., description="Up to 4 files. JPG/PNG for ID docs, PDF for financial docs. Max 2MB each."),
    db: Session = Depends(get_db),
):
    try:
        normalized: List[str] = []
        for item in document_types:
            for part in item.split(","):
                part = part.strip()
                if part:
                    normalized.append(part)
        document_types = normalized
 
        if len(files) > 4:
            raise HTTPException(400, "Maximum 4 documents can be uploaded at once")
 
        if len(files) != len(document_types):
            raise HTTPException(
                400,
                f"Mismatch: {len(files)} file(s) but {len(document_types)} document_type(s) provided",
            )
 
        for dt in document_types:
            if dt not in VALID_TYPES:
                raise HTTPException(
                    400,
                    {"error": f"Invalid document type: {dt}", "valid_types": VALID_TYPES},
                )
 
        for file in files:
            if not file or not file.filename:
                raise HTTPException(400, "One or more files are missing or have no filename")
            contents = await file.read()
            if len(contents) > MAX_FILE_SIZE:
                raise HTTPException(
                    400,
                    f"File '{file.filename}' is too large. Max 2MB. Got {round(len(contents)/1024/1024, 2)}MB",
                )
            await file.seek(0)
 
        result = DocumentUploadService.bulk_upload_documents(
            db=db,
            user_id=user_id,
            document_types=document_types,
            files=files,
        )
 
        if settings.VERIFICATION_MODE == "api":
            for r in result["results"]:
                if r["success"] and r.get("id"):
                    background_tasks.add_task(
                        DocumentUploadService.verify_document_background,
                        r["id"],
                    )
 
        return BulkDocumentUploadResponse(
            total_submitted=result["total_submitted"],
            total_success=result["total_success"],
            total_failed=result["total_failed"],
            results=[BulkDocumentUploadResult(**r) for r in result["results"]],
        )
 
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk upload error: {e}", exc_info=True)
        raise HTTPException(500, f"Bulk upload failed: {str(e)}")
 
 
@router.get("/list", response_model=AllDocumentsResponse)
def list_documents(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    try:
        result = DocumentUploadService.list_documents(db=db, user_id=user_id)
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
    except Exception as e:
        logger.error(f"List error: {e}", exc_info=True)
        raise HTTPException(500, "Failed to retrieve documents")
 
 
@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    user_id: int = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db),
):
    try:
        return DocumentUploadService.delete_document(db=db, document_id=document_id, user_id=user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}", exc_info=True)
        raise HTTPException(500, "Failed to delete document")
 