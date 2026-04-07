from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from core.database import get_db
from core.config import settings

from services.Tracking.nbfc_service import NBFCService
from schemas.Tracking.webhook_schema import (
    NBFCWebhookRequest,
    NBFCWebhookResponse
)

from utils.signature import verify_callback_signature
from core.logger import logger


router = APIRouter(
    prefix="/webhook",
    tags=["NBFC Webhooks"]
)


@router.post("/nbfc", response_model=NBFCWebhookResponse)
async def receive_nbfc_webhook(
    request: Request,
    payload: NBFCWebhookRequest,
    db: Session = Depends(get_db),
    x_signature: str | None = Header(None, alias="X-Signature"),
):
    raw_body = await request.body()

    try:
        logger.info(f"NBFC webhook received: {payload.dict()}")

        # ------------------------------------------------
        # DEV MODE (skip validation)
        # ------------------------------------------------
        if settings.ENV.upper() == "DEV":
            logger.warning("⚠️ DEV mode: skipping signature validation")

        else:
            # ------------------------------------------------
            # SIGNATURE VALIDATION
            # ------------------------------------------------
            if not x_signature:
                raise HTTPException(
                    status_code=401,
                    detail="Missing X-Signature header"
                )

            if not verify_callback_signature(raw_body, x_signature):
                logger.warning("❌ Invalid NBFC webhook signature")
                raise HTTPException(
                    status_code=403,
                    detail="Invalid signature"
                )

        # ------------------------------------------------
        # IDEMPOTENCY CHECK (VERY IMPORTANT)
        # ------------------------------------------------
        if NBFCService.is_duplicate_event(db, payload.transaction_id):
            logger.info(f"Duplicate webhook ignored: {payload.transaction_id}")
            return {
                "success": True,
                "message": "Duplicate webhook ignored"
            }

        # ------------------------------------------------
        # PROCESS WEBHOOK
        # ------------------------------------------------
        result = NBFCService.process_webhook(
            db=db,
            data=payload.dict()
        )

        logger.info(f"✅ NBFC webhook processed: application_id={payload.application_id}")

        return result

    except HTTPException:
        raise  # ✅ don't override HTTP errors

    except Exception as e:
        logger.error(f"🔥 NBFC webhook failed: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )