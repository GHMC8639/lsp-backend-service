from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from services.Profile_KYC.aadhaar_verification_service import AadhaarVerificationService
from schemas.Profile_KYC.aadhaar_schema import (
    AadhaarInitiateResponse,
    AadhaarVerificationRequest,
    AadhaarVerificationResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kyc",tags=["Aadhaar Verification"])


# =====================================================
# INITIATE AADHAAR (USER ONLY)
# =====================================================
@router.post("/aadhaar_initiate", response_model=AadhaarInitiateResponse)
def initiate_aadhaar(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        result = AadhaarVerificationService.initiate_aadhaar(
            db=db,
            user_id=current_user.id
        )
        return AadhaarInitiateResponse(**result)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Aadhaar initiate error")
        raise HTTPException(
            status_code=500,
            detail="Failed to initiate Aadhaar verification"
        )


# =====================================================
# VERIFY AADHAAR (USER ONLY)
# =====================================================
@router.post("/aadhaar_verify", response_model=AadhaarVerificationResponse)
def verify_aadhaar(
    request: AadhaarVerificationRequest,  # only token + auth_code
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        result = AadhaarVerificationService.verify_aadhaar(
            db=db,
            user_id=current_user.id,   # 🔥 comes from JWT
            initiate_token=request.initiate_token,
            auth_code=request.auth_code,
        )
        return AadhaarVerificationResponse(**result)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Aadhaar verification error")
        raise HTTPException(
            status_code=500,
            detail="Aadhaar verification service temporarily unavailable"
        )