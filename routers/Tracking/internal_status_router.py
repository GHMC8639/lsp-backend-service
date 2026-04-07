from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from services.Tracking.status_update_service import StatusUpdateService

from schemas.Tracking.internal_status_schema import (
    InternalStatusUpdateRequest,
    InternalStatusUpdateResponse
)

# ✅ ADD THIS
from core.permissions import user_required
from models.Auth.user import User


router = APIRouter(
    prefix="/internal",
    tags=["Internal Module APIs"]
)


@router.post(
    "/status/update",
    response_model=InternalStatusUpdateResponse
)
def update_internal_status(
    payload: InternalStatusUpdateRequest,
    db: Session = Depends(get_db),

    # ✅ ONLY ADMIN ACCESS
    current_user: User = Depends(user_required)
):
    try:
        StatusUpdateService.update_status(
            db=db,
            application_id=payload.application_id,

            # ✅ FIXED (no user_id from payload)
            user_id=current_user.id,

            new_status=payload.status,
            source=f"{current_user.role}(MODULE-7)",  # dynamic source
            comment=payload.comment
        )

        return {
            "success": True,
            "message": "Status updated successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )