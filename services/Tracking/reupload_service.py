from sqlalchemy.orm import Session
from  repositories.Tracking.reupload_repo import DocumentReuploadRepository
from  repositories.Tracking.loan_application_repo import LoanApplicationRepository
from  repositories.Tracking.loan_status_history_repo import LoanStatusHistoryRepository
from  services.Tracking.notification_service import NotificationService
from  utils.notification_messages import NotificationMessages
from  utils.enums import NotificationType

class ReuploadService:

    @staticmethod
    def submit_reupload(
        db: Session,
        application_id: int,
        user_id: int,
        document_type: str,
        new_document_url: str,
        rejection_reason: str = None
    ):
        app = LoanApplicationRepository.get_by_id(db, application_id)
        if not app:
            raise Exception("Application not found")

        data = {
            "application_id": application_id,
            "document_type": document_type,
            "rejection_reason": rejection_reason,
            "old_document_url": None,
            "new_document_url": new_document_url,
            "status": "PENDING_REVIEW",
        }

        record = DocumentReuploadRepository.create(db, data)

        LoanStatusHistoryRepository.insert_history(
            db=db,
            application_id=application_id,
            old_status= application_status,
            new_status= application_status,
            source="DOCUMENT_REUPLOAD",
            comment=f"User reuploaded: {document_type}"
        )

        NotificationService.send_custom_message(
            db=db,
            user_id=user_id,
            application_id=application_id,
            title="Document Reupload Submitted",
            message=NotificationMessages.DOCUMENT_REUPLOAD_SUBMITTED.value,
            notif_type=NotificationType.DOCUMENT
        )

        return {
            "message": "Document reupload submitted successfully",
            "application_id": application_id,
            "document_type": document_type,
            "status": "PENDING_REVIEW"
        }
