from sqlalchemy.orm import Session
import json

from  repositories.Tracking.webhook_event_repo import WebhookEventRepository
from  repositories.Tracking.loan_application_repo import LoanApplicationRepository

from  services.Tracking.status_update_service import StatusUpdateService
from  services.Tracking.notification_service import NotificationService

from  utils.enums import LoanStatus, NotificationType
from  utils.notification_messages import NotificationMessages
from  core.config import settings


class NBFCService:

    @staticmethod
    def process_webhook(db: Session, data: dict):

        event_id = data["event_id"]
        application_id = data["application_id"]
        new_status = data["status"]
        payload = data.get("payload", {})

        # ✅ handle duplicate event_id
        existing = WebhookEventRepository.exists(db, event_id)
        if existing:
            return {
                "success": True,
                "message": "Duplicate event ignored"
            }

        # ✅ create initial pending event
        event = WebhookEventRepository.create(
            db,
            {
                "event_id": event_id,
                "application_id": application_id,
                "payload": json.dumps(payload),
                "status": "PENDING"
            }
        )

        try:
            app = LoanApplicationRepository.get_by_id(
                db,
                application_id
            )

            if not app:
                # ✅ CHANGED: failed instead of processed
                WebhookEventRepository.mark_failed(
                    db,
                    event_id
                )
                raise Exception("Loan application not found.")

            user_id =  user_id

            mapped_status = NBFCService.map_nbfc_status(
                new_status
            )

            StatusUpdateService.update_status(
                db=db,
                application_id=application_id,
                user_id=user_id,
                new_status=mapped_status,
                source="NBFC_WEBHOOK",
                comment=f"NBFC event: {new_status}"
            )

            # ✅ success
            WebhookEventRepository.mark_processed(
                db,
                event_id
            )

            return {
                "success": True,
                "message": "Webhook stored and processed successfully"
            }

        except Exception as e:
            # ✅ NEW: failed status
            WebhookEventRepository.mark_failed(
                db,
                event_id
            )
            raise e

    @staticmethod
    def map_nbfc_status(nbfc_status: str):

        # 🔥 NBFC controls only till APPROVED / REJECTED
        mapping = {
            "UNDER_REVIEW": LoanStatus.UNDER_REVIEW,
            "VERIFICATION_PENDING": LoanStatus.VERIFICATION_PENDING,
            "CREDIT_CHECK": LoanStatus.CREDIT_CHECK,
            "LENDER_REVIEW": LoanStatus.LENDER_REVIEW,
            "LOAN_APPROVED": LoanStatus.APPROVED,
            "LOAN_REJECTED": LoanStatus.REJECTED
        }

        return mapping.get(
            nbfc_status,
            LoanStatus.UNDER_REVIEW
        )