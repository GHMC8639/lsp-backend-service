from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db

from services.Tracking.notification_service import NotificationService
from schemas.Tracking.notification_schemas import NotificationResponse

# ✅ USE THIS INSTEAD
from core.dependencies import require_roles
from models.Auth.user import User


router = APIRouter(
    prefix="/loan",   # 🔥 fixed (lowercase best practice)
    tags=["Notifications"]
)


@router.get("/notifications", response_model=list[NotificationResponse])
def get_user_notifications(
    db: Session = Depends(get_db),

    # ✅ RBAC added
    current_user: User = Depends(require_roles("USER", "ADMIN", "SUPER_ADMIN"))
):
    return NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id   # ✅ secure
    )