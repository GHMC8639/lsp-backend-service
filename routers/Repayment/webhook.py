from fastapi import APIRouter, Request, Header, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from services.payment.razorpay_service import RazorpayService
from services.Repayment.manual_payment import process_webhook_event


# =====================================================
# LOGGER (PRODUCTION USE)
# =====================================================
logger = logging.getLogger("razorpay_payment_webhook")
logging.basicConfig(level=logging.INFO)


router = APIRouter(
    prefix="/Repayment/webhook",
    tags=["RepaymentWebhook"]
)


# =====================================================
# 🔥 RAZORPAY PAYMENT WEBHOOK
# =====================================================
@router.post(
    "/razorpay",
    operation_id="razorpay_payment_webhook"   # ✅ UNIQUE ID (fixes warning)
)
async def razorpay_payment_webhook(   # ✅ UNIQUE FUNCTION NAME
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Handles Razorpay payment events:
    - payment.captured (SUCCESS)
    - payment.failed (FAILURE)
    """

    # =========================
    # READ RAW BODY
    # =========================
    body = await request.body()

    if not x_razorpay_signature:
        logger.error("❌ Missing Razorpay signature")
        raise HTTPException(status_code=400, detail="Missing signature")

    # =========================
    # VERIFY SIGNATURE
    # =========================
    try:
        rzp = RazorpayService()
        rzp.verify_webhook(body, x_razorpay_signature)
    except Exception as e:
        logger.error(f"❌ Signature verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # =========================
    # PARSE PAYLOAD
    # =========================
    try:
        payload = await request.json()
    except Exception:
        logger.error("❌ Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("event")

    # =========================
    # FILTER EVENTS
    # =========================
    allowed_events = ["payment.captured", "payment.failed"]

    if event not in allowed_events:
        logger.info(f"⚠️ Ignored event: {event}")
        return {"status": "ignored", "event": event}

    logger.info(f"📩 Razorpay Event Received: {event}")

    # =========================
    # PROCESS EVENT
    # =========================
    try:
        result = process_webhook_event(db, payload)

        logger.info(f"✅ Processed {event}: {result}")

        return {
            "status": "ok",
            "event": event,
            "data": result
        }

    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}")

        # IMPORTANT: Return 200 to stop Razorpay retries
        return {
            "status": "error",
            "message": str(e)
        }