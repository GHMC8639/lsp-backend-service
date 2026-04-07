from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.Auth.lender import Lender
from models.Auth.lender import Lender
from models.Loan_application.loan_application import LoanApplication
from core.enums import LoanApplicationStatus
from services.Loan_application.loan_calculator import calculate_loan_summary


class PreDisbursementService:

    @staticmethod
    def get_preview(db: Session, application_id: int):
        """
        Shows loan charges preview before actual disbursement.
        Uses approved_amount only.
        """
        application = db.get(LoanApplication, application_id)

        if not application:
            raise HTTPException(404, "Application not found")

        if application.application_status == LoanApplicationStatus.DISBURSED:
            raise HTTPException(
                400,
                "Loan already disbursed"
            )

        if application.application_status != LoanApplicationStatus.APPROVED:
            raise HTTPException(
                400,
                "Loan must be APPROVED to view disbursement preview"
            )

        if not application.approved_amount:
            raise HTTPException(
                400,
                "Approved amount missing"
            )

        if not application.requested_tenure_months:
            raise HTTPException(
                400,
                "Tenure not found"
            )

        try:
            loan_calc = calculate_loan_summary(
                principal=application.approved_amount,
                tenure_months=application.requested_tenure_months
            )
        except ValueError as e:
            raise HTTPException(400, str(e))
        lender = db.query(Lender).filter(
            Lender.id == application.lender_id 
        ).first()
        return {
            "application_id": application.id,
            "lender_name": lender.name if lender else None,
            "approved_amount": loan_calc["approved_amount"],
            "tenure_months": loan_calc["tenure_months"],
            "interest_rate_percent": loan_calc["interest_rate"],
            "emi_amount": loan_calc["emi"],
            "total_repayment": loan_calc["total_repayment"],

            # Charges breakdown
            "processing_fee": loan_calc["processing_fee"],
            "gst_on_processing_fee": loan_calc["gst_on_processing_fee"],
            "total_processing_charges": loan_calc["total_processing_charges"],

            # Final payout amount
            "net_disbursement_amount": loan_calc["net_disbursement_amount"]
        }