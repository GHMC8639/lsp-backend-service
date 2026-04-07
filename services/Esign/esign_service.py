from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import httpx

from models.Esign.esign_session import EsignSession, EsignStatus
from models.Esign.audit_logs import EsignAuditLog
from models.Esign.signed_documents import SignedDocument
from models.Esign.agreements import Agreement

from providers.factory import get_esign_provider

from core.exceptions import throw_error
from core.logger import logger
from core.config import settings

from utils.file_handler import FileHandler


class EsignService:

    def __init__(self):
        self.file_handler = FileHandler()

    # INITIATE E-SIGN
    async def initiate_esign(self, data, db: Session):

        logger.info(f"[E-SIGN INIT] loan_id={data.loan_id}")

        provider = get_esign_provider()
        payload = data.model_dump()

        try:
            provider_resp = await provider.initiate_esign(payload)
        except Exception as exc:
            logger.error(f"[E-SIGN INIT] Provider error: {exc}")
            throw_error("eSign provider unreachable", 503)

        txn = provider_resp.get("transaction_id")

        if not txn:
            throw_error("Invalid provider response", 502)

        session = EsignSession(
            loan_id=data.loan_id,
            user_id=1,  # TODO: replace after auth integration
            transaction_id=txn,
            request_payload=payload,
            response_payload=provider_resp,
            status=EsignStatus.OTP_SENT
        )

        log = EsignAuditLog(
            session_id=None,
            event_type="OTP_SENT",
            event_description=f"OTP sent for txn={txn}"
        )

        try:
            db.add(session)
            db.flush()  # get session.id

            log.session_id = session.id
            db.add(log)

            db.commit()

        except IntegrityError:
            db.rollback()
            throw_error("Duplicate transaction id", 409)


        return {
            "transaction_id": txn,
            "masked_aadhaar": provider_resp.get("masked_aadhaar")
        }
      

    # VERIFY OTP
    async def verify_esign(self, data, db: Session):

        logger.info(f"[E-SIGN VERIFY] txn={data.transaction_id}")

        provider = get_esign_provider()

        session = db.query(EsignSession).filter(
            EsignSession.transaction_id == data.transaction_id
        ).first()

        if not session:
            throw_error("Invalid transaction ID", 404)

        if session.status == EsignStatus.SIGNED:
            return {"transaction_id": session.transaction_id, "status": "SIGNED"}

        if session.status != EsignStatus.OTP_SENT:
            throw_error("Invalid signing state", 400)

        try:
            provider_resp = await provider.verify_esign(data.model_dump())
        except Exception as exc:
            logger.error(f"[E-SIGN VERIFY] Provider error: {exc}")
            throw_error("OTP verification failed", 503)

        if provider_resp.get("status") != "SIGNED":

            log = EsignAuditLog(
                session_id=session.id,
                event_type="OTP_FAILED",
                event_description="OTP verification failed"
            )

            db.add(log)
            db.commit()

            throw_error("Invalid OTP", 400)

        session.status = EsignStatus.OTP_SENT

        log = EsignAuditLog(
            session_id=session.id,
            event_type="SIGNED",
            event_description="OTP verified successfully"
        )

        db.add(log)
        db.commit()

        return {
            "transaction_id": session.transaction_id,
            "status": "SIGNED"
        }

    # CALLBACK HANDLER
    async def handle_callback(self, data, db: Session):

        logger.info(f"[CALLBACK] txn={data.transaction_id}")

        # ------------------------------------------------
        # FETCH SESSION
        # ------------------------------------------------
        session = db.query(EsignSession).filter(
            EsignSession.transaction_id == data.transaction_id
        ).first()

        if not session:
            throw_error("Unknown transaction ID", 404)

        # ------------------------------------------------
        # IDEMPOTENCY CHECK
        # ------------------------------------------------
        if session.status == EsignStatus.SIGNED:
            logger.info("[CALLBACK] already processed")
            return {"status": "already_processed"}

        # ------------------------------------------------
        # FAILURE CASE
        # ------------------------------------------------
        if data.status != "SIGNED":
            session.status = EsignStatus.FAILED
            db.commit()
            db.refresh(session)
            throw_error("Callback status FAILED", 400)

        signed_url = data.signed_pdf_url

        # ------------------------------------------------
        # DOWNLOAD / GENERATE SIGNED PDF
        # ------------------------------------------------
        if signed_url == "LOCAL":

            # Create mock PDF content
            content = b"%PDF-1.4 mock signed document"

            file_path, file_hash = await self.file_handler.save_signed_pdf_async(
                content=content,
                txn=session.transaction_id
            )

        else:

            file_path, file_hash = await self.file_handler.download_and_save_pdf_async(
                url=signed_url,
                txn=session.transaction_id
                )

        # ------------------------------------------------
        # SAVE SIGNED DOCUMENT
        # ------------------------------------------------
        signed_doc = SignedDocument(
            session_id=session.id,
            signed_pdf_path=file_path,
            file_hash=file_hash
        )

        db.add(signed_doc)

        # ------------------------------------------------
        # UPDATE SESSION
        # ------------------------------------------------
        session.status = EsignStatus.SIGNED
        session.callback_payload = data.model_dump()
        
        # ------------------------------------------------
        # UPDATE AGREEMENT (ADD HERE)
        # ------------------------------------------------
        agreement = db.query(Agreement).filter(
            Agreement.loan_id == session.loan_id,
            Agreement.is_active == True
        ).first()

        if agreement:
            agreement.status = "SIGNED"

        # ------------------------------------------------
        # AUDIT LOG
        # ------------------------------------------------
        log = EsignAuditLog(
            session_id=session.id,
            event_type="CALLBACK_RECEIVED",
            event_description=f"Signed document stored: {file_path}"
        )

        db.add(log)

        db.commit()
        db.refresh(session)

        # ------------------------------------------------
        # 🚀 DISBURSEMENT TRIGGER (IMPORTANT)
        # ------------------------------------------------
        try:
            from services.Esign.disbursement_service import DisbursementService
            
            disbursement_service = DisbursementService()

            DisbursementService().confirm(session.loan_id, db)

            logger.info(f"[DISBURSEMENT] Triggered for loan_id={session.loan_id}")
            # ✅ STEP 7 — NOTIFICATION (ADD HERE)
            print(f"[NOTIFICATION] Loan {session.loan_id} disbursed successfully")

        except Exception as e:
            # Do NOT fail callback if disbursement fails
            logger.error(f"[DISBURSEMENT ERROR] {str(e)}")

        # ------------------------------------------------
        # RESPONSE
        # ------------------------------------------------
        return {
            "status": "ok",
            "file_path": file_path,
            "loan_id": session.loan_id
        }