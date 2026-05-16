from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from schemas.Repayment.manual_schema import (
    PaymentModeEnum,
    PaymentOptionEnum
)

from services.Repayment.manual_payment import (
    get_payment_summary,
    initiate_payment,
    retry_payment
)


router = APIRouter(
    prefix="/manual-payment",
    tags=["Payments"]
)


# =====================================================
# COMMON RESPONSE FORMAT
# =====================================================
def success_response(data):
    return {
        "success": True,
        "data": data
    }


# =====================================================
# STEP 1: GET EMI SUMMARY
# =====================================================
@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        result = get_payment_summary(db, current_user.id)
        return success_response(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# STEP 2: INITIATE PAYMENT (REGULAR + PREPAY)
# =====================================================
@router.post("/initiate")
def initiate(
    payment_mode: PaymentModeEnum,
    payment_option: PaymentOptionEnum,   # 🔥 supports PREPAY
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        result = initiate_payment(
            db=db,
            user_id=current_user.id,
            payment_mode=payment_mode.value,
            payment_option=payment_option.value
        )

        return success_response(result)

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# STEP 3: RETRY PAYMENT
# =====================================================
@router.post("/retry")
def retry(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        result = retry_payment(
            db=db,
            user_id=current_user.id
        )

        return success_response(result)

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))