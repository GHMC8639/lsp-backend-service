from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import SessionLocal
from schemas.Tracking.reupload_schema import DocumentReuploadRequest
from services.Tracking.reupload_service import ReuploadService

router = APIRouter(prefix="/api/v1/loan", tags=["Document Reupload"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/application/{application_id}/reupload")
def reupload(application_id: str, payload: DocumentReuploadRequest, db: Session = Depends(get_db)):
    return ReuploadService.reupload_document(
        db=db,
        application_id=application_id,
        document_type=payload.document_type,
        reason=payload.reason,
        comments=payload.comments
    )
