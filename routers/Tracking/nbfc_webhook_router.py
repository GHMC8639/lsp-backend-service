from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import SessionLocal
from schemas.Tracking.status_update_schema import StatusUpdateRequest
from services.Tracking.nbfc_service import NBFCService

router = APIRouter(prefix="/api/v1/nbfc", tags=["NBFC"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/manual-update")
def nbfc_manual_update(payload: StatusUpdateRequest, db: Session = Depends(get_db)):
    return NBFCService.manual_update(
        db=db,
        application_id=payload.application_id,
        new_status=payload.new_status,
        metadata=payload.metadata
    )

@router.post("/update-status")
def nbfc_webhook(payload: StatusUpdateRequest, db: Session = Depends(get_db)):
    return {"received": True}
