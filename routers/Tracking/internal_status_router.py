from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import logger
from core.dependencies import require_roles

from services.Tracking.status_update_service import StatusUpdateService

from schemas.Tracking.internal_status_schema import (
    InternalStatusUpdateRequest,
    InternalStatusUpdateResponse
)

from models.Auth.user import User


router = APIRouter(
    prefix="/internal",
    tags=["Internal Module APIs"]
)


@router.post(
    "/status/update",
    response_model=InternalStatusUpdateResponse,
    operation_id="internal_status_update"
)
def update_internal_status(
    request: InternalStatusUpdateRequest,
    http_request: Request,
    db: Session = Depends(get_db),

    # 🔐 STRICT ACCESS CONTROL
    current_user: User = Depends(require_roles("ADMIN", "SUPER_ADMIN")),
):
    try:
        logger.info(
            f"[STATUS UPDATE REQUEST] user={current_user.id}, "
            f"app={request.application_id}, status={request.status}"
        )

        authorization = http_request.headers.get("Authorization")

        updated_app = StatusUpdateService.update_status(
            db=db,
            application_id=request.application_id,
            user_id=current_user.id,
            new_status=request.status,
            source=current_user.role,
            comment=request.comment,
            token=authorization
        )

        return {
            "success": True,
            "application_id": updated_app.id,
            "new_status": (
                updated_app.application_status.value
                if updated_app.application_status else None
            ),
            "message": "Status updated successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[STATUS UPDATE ERROR] {str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Failed to update status"
        )