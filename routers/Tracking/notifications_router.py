from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import SessionLocal
from services.Tracking.notification_service import NotificationService

router = APIRouter(prefix="/api/v1", tags=["Notifications"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/notifications")
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    return NotificationService.get_notifications(db, user_id)
