from fastapi import APIRouter, Depends, Request, Header, Body
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db

from services.Esign.esign_service import EsignService

from schemas.Esign.esign_schema import InitiateRequest, VerifyRequest
from schemas.Esign.callback_schema import EsignCallbackRequest

from utils.signature import verify_callback_signature
from utils.response import success_response

from core.exceptions import throw_error
from core.logger import logger

# ✅ ADD THIS
from core.permissions import user_required

router = APIRouter(
    prefix="/loan/esign",
    tags=["E-Sign"]
)


def get_esign_service() -> EsignService:
    return EsignService()


# ------------------------------------------------
# INITIATE ESIGN (USER + ADMIN)
# ------------------------------------------------
@router.post("/initiate")
async def initiate_esign(
    request_data: InitiateRequest,
    db: Session = Depends(get_db),
    service: EsignService = Depends(get_esign_service),

    # ✅ ROLE CHECK
    current_user=Depends(user_required)
):
    logger.info(f"E-Sign initiate request for loan_id={request_data.loan_id}")

    result = await service.initiate_esign(request_data, db)
    return success_response(result)


# ------------------------------------------------
# VERIFY OTP (USER + ADMIN)
# ------------------------------------------------
@router.post("/verify")
async def verify_esign(
    request_data: VerifyRequest,
    db: Session = Depends(get_db),
    service: EsignService = Depends(get_esign_service),

    # ✅ ROLE CHECK
    current_user=Depends(user_required)
):
    logger.info(f"E-Sign verify request for txn={request_data.transaction_id}")

    result = await service.verify_esign(request_data, db)
    return success_response(result)


# ------------------------------------------------
# PROVIDER CALLBACK (NO USER AUTH)
# ------------------------------------------------
@router.post("/callback")
async def esign_callback(
    request: Request,
    callback_body: EsignCallbackRequest = Body(...),
    db: Session = Depends(get_db),
    service: EsignService = Depends(get_esign_service),
    x_signature: str | None = Header(None, alias="X-Signature"),
):
    logger.info(f"E-Sign callback received for txn={callback_body.transaction_id}")

    raw_body = await request.body()

    # DEV mode → skip signature validation
    if settings.ENV.upper() == "DEV":
        logger.info("DEV mode: skipping signature validation")
        return await service.handle_callback(callback_body, db)

    # PROD mode → validate signature
    if not x_signature:
        throw_error("Missing X-Signature header", 401)

    if not verify_callback_signature(raw_body, x_signature):
        logger.warning(f"Invalid callback signature for txn={callback_body.transaction_id}")
        throw_error("Invalid callback signature", 403)

    result = await service.handle_callback(callback_body, db)

    logger.info(f"E-Sign callback processed for txn={callback_body.transaction_id}")
    return result