from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from schemas.Profile_KYC.bank_schema import (
    BankVerificationRequest,
    BankVerificationResponse,
)
from services.Profile_KYC.bank_verification_service import BankVerificationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kyc", tags=["Bank Verification"])


@router.post("/bank_verify", response_model=BankVerificationResponse)
def verify_bank(
    request: BankVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        # 🔥 identity comes from token
        profile = current_user.profile

        if profile.identity_status != "VERIFIED":
            raise HTTPException(
                status_code=400,
                detail="Complete PAN + Aadhaar verification before bank verification"
            )

        if profile.bank_status == "VERIFIED":
            return BankVerificationResponse(
                message="Bank already verified",
                next="Upload required documents"
            )

        BankVerificationService.verify_bank_account(
            db=db,
            user=profile,
            account_number=request.account_number,
            account_holder_name=request.account_holder_name,
            bank_name=request.bank_name,
            ifsc=request.ifsc,
        )

        return BankVerificationResponse(
            message="Bank account verified successfully",
            next="Upload required documents for final KYC approval"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bank verification error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Verification service temporarily unavailable"
        )