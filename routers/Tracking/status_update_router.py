from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import SessionLocal
from schemas.Tracking.status_update_schema import StatusUpdateRequest
from services.Tracking.status_update_service import StatusUpdateService
from schemas.Tracking.status_update_schema import StatusUpdateResponse


router = APIRouter(prefix="/api/v1/status", tags=["Status Update"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/update",
    response_model=StatusUpdateResponse,
    summary="Update loan application status",
    description="Updates the status of a loan application and logs history. Includes KYC checks.",
)
def update_status_endpoint(payload: StatusUpdateRequest, db: Session = Depends(get_db)):
    updated = StatusUpdateService.update_status(
        db=db,
        application_id=payload.application_id,
        new_status=payload.new_status,
        source=payload.source,
        metadata=payload.metadata,
    )

    return StatusUpdateResponse(
        application_id=str(updated.id),
        new_status=updated.current_status,
        message="Status updated successfully"
    )
