from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import traceback

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from schemas.Repayment.prepayment_schema import (
    PrepaymentRequest,
    PrepayResponse,
    PaymentModeEnum
)

from services.Repayment.prepay import process_prepay


router = APIRouter(
    prefix="/prepayment",
    tags=["Prepayment"]
)


# =====================================================
# PREPAYMENT CALCULATION ONLY (NO PAYMENT)
# =====================================================
@router.post(
    "/calculate",
    response_model=PrepayResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate prepayment details for current user's loan"
)
def calculate_prepayment(
    payload: PrepaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    """
    🔥 PURPOSE:
    - Only calculates prepayment amount
    - Does NOT perform payment
    - Does NOT update EMI

    💡 Used for:
    - UI preview
    - Showing breakdown before payment

    📌 Flow:
    1. Call this API → get total payable
    2. Call /manual-payment/initiate (payment_option=prepay)
    3. Razorpay payment
    4. Webhook updates EMI
    """

    # ✅ Basic validation
    if payload.emi_count <= 0:
        raise HTTPException(
            status_code=400,
            detail="emi_count must be greater than 0"
        )

    try:
        return process_prepay(
            db=db,
            user_id=current_user.id,
            emi_count=payload.emi_count,
            payment_mode=payload.payment_mode
        )

    except HTTPException as e:
        raise e

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        print("❌ PREPAY CALCULATION ERROR:")
        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )