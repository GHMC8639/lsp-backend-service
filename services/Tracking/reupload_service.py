from repositories.Tracking.loan_application_repo import LoanApplicationRepository
from repositories.Tracking.loan_status_history_repo import LoanStatusHistoryRepository
from repositories.Tracking.notification_repo import NotificationRepository


class ReuploadService:

    @staticmethod
    def reupload_document(db, application_id: str, document_type: str,
                          reason: str = None, comments: str = None):

        application = LoanApplicationRepository.get_application(db, application_id)
        if not application:
            return {"success": False, "message": "Application not found"}

        metadata = {
            "document_type": document_type,
            "reason": reason,
            "comments": comments
        }

        prev_status = application.current_status

      
        LoanStatusHistoryRepository.create_history(
            db=db,
            application_id=application_id,
            previous_status=prev_status,
            new_status="VERIFICATION_PENDING",
            source="reupload",
            metadata=metadata
        )

    
        LoanApplicationRepository.update_status(
            db=db,
            application_id=application_id,
            new_status="VERIFICATION_PENDING"
        )


        NotificationRepository.create_notification(
            db=db,
            user_id=application.user_id,
            application_id=application_id,
            title="Document Reuploaded",
            message=f"Document reuploaded: {document_type}"
        )

        return {"success": True, "message": "Document reupload recorded"}
