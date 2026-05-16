import hmac
import hashlib
import json
import os
import logging
from datetime import datetime

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from core.session import get_db
from repositories.Loan_application.loan_disbursement_repo import LoanDisbursementRepository
from core.enums import DisbursementStatusEnum, LoanApplicationStatus


# =====================================================
# LOGGER
# =====================================================
logger = logging.getLogger("razorpayx_webhook")
logging.basicConfig(level=logging.INFO)


router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"]
)


# =====================================================
# 🔐 VERIFY SIGNATURE
# =====================================================
def verify_signature(request_body: bytes, signature: str):
    webhook_secret = os.getenv("RAZORPAYX_WEBHOOK_SECRET")

    if not webhook_secret:
        logger.error("Webhook secret not configured")
        raise HTTPException(500, "Webhook configuration error")

    generated_signature = hmac.new(
        webhook_secret.encode(),
        msg=request_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(generated_signature, signature):
        logger.error("Invalid webhook signature")
        raise HTTPException(400, "Invalid signature")


# =====================================================
# 🔥 RAZORPAYX WEBHOOK (PAYOUT)
# =====================================================
@router.post("/razorpayx", operation_id="razorpayx_payout_webhook")
async def razorpayx_payout_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    # =========================
    # READ BODY
    # =========================
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    if not signature:
        logger.error("Missing RazorpayX signature")
        raise HTTPException(400, "Missing signature")

    # =========================
    # VERIFY SIGNATURE
    # =========================
    verify_signature(body, signature)

    # =========================
    # PARSE JSON
    # =========================
    try:
        data = json.loads(body)
    except Exception:
        logger.error("Invalid JSON payload")
        raise HTTPException(400, "Invalid JSON payload")

    event = data.get("event")
    logger.info(f"RazorpayX Event Received: {event}")

    # =========================
    # FILTER ONLY PAYOUT EVENTS
    # =========================
    allowed_events = [
        "payout.processed",
        "payout.failed",
        "payout.reversed",
        "payout.processing",
        "payout.queued"
    ]

    if event not in allowed_events:
        logger.info(f"Ignored event: {event}")
        return {"status": "ignored_event"}

    # =========================
    # EXTRACT PAYOUT DATA
    # =========================
    payout = data.get("payload", {}).get("payout", {}).get("entity", {})

    # 🔥 FIX: use reference_id (NOT payout id)
    reference_id = payout.get("reference_id")
    status = payout.get("status")

    if not reference_id:
        logger.warning("Missing reference_id in webhook")
        return {"status": "ignored_no_reference"}

    try:
        # =========================
        # FETCH DISBURSEMENT WITH LOCK
        # =========================
        disbursement = LoanDisbursementRepository.get_by_reference(
            db=db,
            reference_id=reference_id,
            for_update=True   # ✅ important for concurrency
        )

        if not disbursement:
            logger.warning(f"Disbursement not found: {reference_id}")
            return {"status": "not_found"}

        application = disbursement.application

        # =========================
        # IDEMPOTENCY CHECK
        # =========================
        if (
            disbursement.payment_status == DisbursementStatusEnum.SUCCESS
            and status == "processed"
        ):
            logger.info("Already processed payout")
            return {"status": "already_processed"}

        # =========================
        # STATUS HANDLING
        # =========================
        if status == "processed":
            disbursement.payment_status = DisbursementStatusEnum.SUCCESS

            application.application_status = LoanApplicationStatus.ACTIVE
            application.payout_status = "SUCCESS"
            application.disbursed_at = datetime.utcnow()

        elif status in ["failed", "reversed"]:
            disbursement.payment_status = DisbursementStatusEnum.FAILED
            application.payout_status = "FAILED"

        elif status in ["processing", "queued"]:
            disbursement.payment_status = DisbursementStatusEnum.PROCESSING
            application.payout_status = "PROCESSING"

        else:
            logger.info(f"Ignored payout status: {status}")
            return {"status": f"ignored_status_{status}"}

        # =========================
        # OPTIONAL: UPDATE TRANSACTIONS
        # =========================
        if hasattr(disbursement, "transactions") and disbursement.transactions:
            for txn in disbursement.transactions:
                txn.status = disbursement.payment_status.value

        # =========================
        # SAVE
        # =========================
        disbursement.completed_at = datetime.utcnow()

        db.commit()

        logger.info(f"Payout updated successfully: {reference_id} → {status}")

    except Exception as e:
        db.rollback()
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(500, "Webhook processing failed")

    return {
        "status": "updated",
        "reference_id": reference_id,
        "payout_status": status
    }