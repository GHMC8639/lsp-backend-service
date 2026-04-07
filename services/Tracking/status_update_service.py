from sqlalchemy import func
from sqlalchemy.orm import Session

from  repositories.Tracking.loan_application_repo import LoanApplicationRepository
from  repositories.Tracking.loan_status_history_repo import LoanStatusHistoryRepository
from  repositories.Tracking.loan_repo import LoanRepository

from  services.Tracking.kyc_service import KYCService
from  services.Tracking.notification_service import NotificationService

from  utils.enums import LoanStatus
from  utils.notification_messages import NotificationMessages


class StatusUpdateService:

    @staticmethod
    def validate_transition(old_status: str, new_status: str):
        VALID_TRANSITIONS = {
            LoanStatus.SUBMITTED: [LoanStatus.UNDER_REVIEW],
            LoanStatus.UNDER_REVIEW: [
                LoanStatus.VERIFICATION_PENDING,
                LoanStatus.CREDIT_CHECK,
                LoanStatus.REJECTED
            ],
            LoanStatus.VERIFICATION_PENDING: [LoanStatus.UNDER_REVIEW],
            LoanStatus.CREDIT_CHECK: [
                LoanStatus.LENDER_REVIEW,
                LoanStatus.REJECTED
            ],
            LoanStatus.LENDER_REVIEW: [
                LoanStatus.APPROVED,
                LoanStatus.REJECTED
            ],
            LoanStatus.APPROVED: [LoanStatus.AGREEMENT_PENDING],
            LoanStatus.AGREEMENT_PENDING: [LoanStatus.DISBURSEMENT_INITIATED],
            LoanStatus.DISBURSEMENT_INITIATED: [LoanStatus.DISBURSED],
            LoanStatus.DISBURSED: [LoanStatus.ACTIVE],
            LoanStatus.ACTIVE: [LoanStatus.CLOSED]
        }

        allowed = VALID_TRANSITIONS.get(old_status, [])
        return new_status in allowed

    # ✅ FIXED: method moved inside class
    @staticmethod
    def update_status(
        db: Session,
        application_id: int,
        user_id: int,
        new_status: str,
        source="SYSTEM",
        comment=None
    ):
        app = LoanApplicationRepository.get_by_id(db, application_id)
        if not app:
            raise Exception("Application not found")

        old_status = LoanStatus( application_status)
        new_status = LoanStatus(new_status)

        # Ignore NBFC updates after APPROVED
        if (
            source == "NBFC_WEBHOOK"
            and old_status in [
                LoanStatus.APPROVED,
                LoanStatus.AGREEMENT_PENDING,
                LoanStatus.DISBURSEMENT_INITIATED,
                LoanStatus.DISBURSED,
                LoanStatus.ACTIVE
            ]
        ):
            return app

        # KYC check before CREDIT_CHECK
        if new_status == LoanStatus.CREDIT_CHECK:
            kyc_status = KYCService.fetch_user_kyc_status(
                db,
                user_id
            )

            if not KYCService.is_kyc_completed(kyc_status):
                new_status = LoanStatus.VERIFICATION_PENDING
                comment = "KYC incomplete - moved to verification pending"

        if not StatusUpdateService.validate_transition(
            old_status,
            new_status
        ):
            raise Exception(
                f"Invalid status transition: {old_status} → {new_status}"
            )

        if new_status == LoanStatus.DISBURSED:
            existing_loan = LoanRepository.get_by_application_id(
                db,
                application_id
            )
            if not existing_loan:
                loan_data = {
            "application_id":  id,
            "user_id":  user_id,
            "principal":  approved_amount,
            "interest_rate":  interest_rate,
            "tenure_months":  requested_tenure_months,
            "emi_amount":  monthly_emi,
            "status": LoanStatus.ACTIVE,
            "disbursed_at": func.now(),

        }
            LoanRepository.create(db, loan_data)

        updated_app = LoanApplicationRepository.update_status(
            db,
            application_id,
            new_status
        )

        LoanStatusHistoryRepository.insert_history(
            db=db,
            application_id=application_id,
            old_status=old_status,
            new_status=new_status,
            source=source,
            comment=comment
        )

        message_map = {
            LoanStatus.UNDER_REVIEW: NotificationMessages.APPLICATION_UNDER_REVIEW.value,
            LoanStatus.VERIFICATION_PENDING: "KYC verification pending. Please upload missing documents.",
            LoanStatus.CREDIT_CHECK: NotificationMessages.CREDIT_CHECK_STARTED.value,
            LoanStatus.APPROVED: NotificationMessages.APPLICATION_APPROVED.value,
            LoanStatus.REJECTED: NotificationMessages.APPLICATION_REJECTED.value,
            LoanStatus.AGREEMENT_PENDING: NotificationMessages.AGREEMENT_PENDING.value,
            LoanStatus.DISBURSEMENT_INITIATED: NotificationMessages.DISBURSEMENT_INITIATED.value,
            LoanStatus.DISBURSED: NotificationMessages.LOAN_DISBURSED.value,
            LoanStatus.ACTIVE: NotificationMessages.LOAN_ACTIVE.value,
            LoanStatus.CLOSED: NotificationMessages.LOAN_CLOSED.value
           
        }

        message = message_map.get(
            new_status,
            NotificationMessages.NBFC_STATUS_UPDATE.value
        )

        NotificationService.send_custom_message(
            db=db,
            user_id=user_id,
            application_id=application_id,
            title="Loan Status Update",
            message=message,
            notif_type="STATUS_UPDATE"
        )

        return updated_app