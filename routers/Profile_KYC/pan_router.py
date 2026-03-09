from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from services.Profile_KYC.pan_verification_service import PANVerificationService
from schemas.Profile_KYC.pan_schema import PANVerificationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kyc",tags=["PAN Verification"])


@router.post("/pan_verify", response_model=PANVerificationResponse)
def verify_pan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        result = PANVerificationService.verify_pan(
            db=db,
            user_id=current_user.id  # 🔥 comes from token
        )

        return PANVerificationResponse(
            message=result["message"],
            pan_status=result["pan_status"],
            verified_name=result.get("verified_name"),
            identity_status=result["identity_status"],
            next_step=result["next_step"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PAN verification error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="PAN verification service temporarily unavailable"
        )