from utils.enums import ApplicationStatus


def get_notification_message(status: str) -> str:
    messages = {
        ApplicationStatus.SUBMITTED: "Your loan application has been submitted successfully.",
        ApplicationStatus.UNDER_REVIEW: "Your documents are under review.",
        ApplicationStatus.VERIFICATION_PENDING: "Please complete your pending verification.",
        ApplicationStatus.CREDIT_CHECK: "Your credit check has started.",
        ApplicationStatus.LENDER_REVIEW: "Your application is being reviewed by the lender.",
        ApplicationStatus.APPROVED: "Your loan application has been approved.",
        ApplicationStatus.REJECTED: "Your loan application has been rejected.",
        ApplicationStatus.AGREEMENT_PENDING: "Your loan agreement is pending. Please complete it.",
        ApplicationStatus.DISBURSEMENT_INITIATED: "Your loan disbursement is being processed.",
        ApplicationStatus.DISBURSED: "Your loan has been successfully disbursed.",
        ApplicationStatus.ACTIVE: "Your loan is now active.",
        ApplicationStatus.CLOSED: "Your loan has been closed successfully.",
    }

    return messages.get(status, "Status updated.")
