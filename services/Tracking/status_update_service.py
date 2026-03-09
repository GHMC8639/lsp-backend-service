from typing import Optional
from fastapi import HTTPException, status

from repositories.Tracking.loan_application_repo import LoanApplicationRepository
from repositories.Tracking.loan_status_history_repo import LoanStatusHistoryRepository
from repositories.Tracking.loan_repo import LoanRepository
from repositories.Tracking.notification_repo import NotificationRepository

from utils.notification_messages import get_notification_message
from utils.enums import ApplicationStatus

from services.Tracking.kyc_service import KYCService


class StatusUpdateService:

    @staticmethod
    def validate_transition(current: str, new: str) -> bool:
        workflow = {
            ApplicationStatus.DRAFT: [ApplicationStatus.SUBMITTED],
            ApplicationStatus.SUBMITTED: [ApplicationStatus.UNDER_REVIEW],
            ApplicationStatus.UNDER_REVIEW: [ApplicationStatus.VERIFICATION_PENDING],
            ApplicationStatus.VERIFICATION_PENDING: [ApplicationStatus.CREDIT_CHECK],
            ApplicationStatus.CREDIT_CHECK: [ApplicationStatus.LENDER_REVIEW],
            ApplicationStatus.LENDER_REVIEW: [
                ApplicationStatus.APPROVED,
                ApplicationStatus.REJECTED
            ],
            ApplicationStatus.APPROVED: [ApplicationStatus.AGREEMENT_PENDING],
            ApplicationStatus.AGREEMENT_PENDING: [ApplicationStatus.DISBURSEMENT_INITIATED],
            ApplicationStatus.DISBURSEMENT_INITIATED: [ApplicationStatus.DISBURSED],
            ApplicationStatus.DISBURSED: [ApplicationStatus.ACTIVE],
            ApplicationStatus.ACTIVE: [ApplicationStatus.CLOSED],
            ApplicationStatus.REJECTED: [],
            ApplicationStatus.CLOSED: [],
        }

        return ApplicationStatus(new) in workflow.get(ApplicationStatus(current), [])

    @staticmethod
    def update_status(db, application_id: str, new_status: str, source: str, metadata: Optional[dict] = None):

        application = LoanApplicationRepository.get_application(db, application_id)
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        current_status = application.current_status

        if not StatusUpdateService.validate_transition(current_status, new_status):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status transition")

        kyc = KYCService.fetch_kyc_status(db, application.user_id)

        if new_status == ApplicationStatus.UNDER_REVIEW:
            if (
                kyc["pan"] != "VERIFIED"
                or kyc["aadhaar"] != "VERIFIED"
                or kyc["bank"] not in ["VERIFIED", "APPROVED"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="KYC incomplete. Cannot move to UNDER_REVIEW."
                )

        if new_status == ApplicationStatus.CREDIT_CHECK:
            if kyc["overall"] != "APPROVED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="KYC not approved by Module-2. Cannot move to CREDIT_CHECK."
                )

        LoanStatusHistoryRepository.create_history(
            db=db,
            application_id=application_id,
            previous_status=current_status,
            new_status=new_status,
            source=source,
            metadata=metadata
        )

        updated_app = LoanApplicationRepository.update_status(
            db=db,
            application_id=application_id,
            new_status=new_status
        )

        if new_status == ApplicationStatus.VERIFICATION_PENDING:
            if kyc["overall"] == "APPROVED":
                return StatusUpdateService.update_status(
                    db=db,
                    application_id=application_id,
                    new_status=ApplicationStatus.CREDIT_CHECK,
                    source="kyc_auto"
                )

        if new_status == ApplicationStatus.DISBURSED:
            LoanRepository.create_loan(
                db=db,
                application_id=application_id,
                principal=float(application.loan_amount),
                interest_rate=12.5,
                emi_amount=metadata.get("emi") if metadata else None
            )

        message = get_notification_message(new_status)
        NotificationRepository.create_notification(
            db=db,
            user_id=application.user_id,
            application_id=application_id,
            title=f"Loan Status: {new_status}",
            message=message
        )

        return updated_app