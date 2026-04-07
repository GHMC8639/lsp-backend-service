from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_disbursements import LoanDisbursement
from repositories.Loan_application.loan_disbursement_repo import LoanDisbursementRepository
from core.enums import (
    LoanApplicationStatus,
    DisbursementStatusEnum,
    PaymentModeEnum)
from services.Loan_application.loan_calculator import calculate_loan_summary
from core.mock_nbfc import MockNBFCPaymentGateway


class LoanDisbursementService:

    @staticmethod
    def disburse_loan(
        db: Session,
        application_id: int,
        payment_mode: PaymentModeEnum
    ):

        application = db.get(LoanApplication, application_id)

        if not application:
            raise HTTPException(404, "Application not found")

        # Prevent duplicate successful disbursement
        if application.application_status == LoanApplicationStatus.DISBURSED:
            raise HTTPException(400, "Loan already disbursed")

        if application.application_status != LoanApplicationStatus.APPROVED:
            raise HTTPException(
                400,
                "Loan must be APPROVED before disbursement"
            )

        if not application.approved_amount:
            raise HTTPException(400, "Approved amount missing")

        loan_calc = calculate_loan_summary(
            principal=application.approved_amount,
            tenure_months=application.requested_tenure_months
        )

        net_amount = loan_calc["net_disbursement_amount"]

        profile = application.user_profile

        if not profile or not profile.bank_details:
            raise HTTPException(400, "No payout method found")

        payout_method = next(
            (
                method for method in profile.bank_details
                if method.payment_mode == payment_mode
                and method.is_verified
            ),
            None
        )

        if not payout_method:
            raise HTTPException(
                400,
                f"No verified {payment_mode.value} payout method found"
            )

        disbursement = LoanDisbursement(
            application_id=application.id,
            amount=net_amount,
            payment_mode=payment_mode,
            payment_status=DisbursementStatusEnum.INITIATED,
            initiated_at=datetime.utcnow()
        )

        disbursement = LoanDisbursementRepository.create(db, disbursement)

        try:

            if payment_mode == PaymentModeEnum.BANK:

                payment_response = MockNBFCPaymentGateway.transfer_bank(
                    account_number=payout_method.account_number,
                    ifsc_code=payout_method.ifsc_code,
                    account_holder_name=payout_method.account_holder_name,
                    amount=float(net_amount)
                )

            elif payment_mode == PaymentModeEnum.UPI:

                payment_response = MockNBFCPaymentGateway.transfer_upi(
                    upi_id=payout_method.upi_id,
                    amount=float(net_amount)
                )

            else:
                raise HTTPException(400, "Unsupported payment mode")

        except Exception as e:
            # System-level failure 
            disbursement.payment_status = DisbursementStatusEnum.FAILED
            disbursement.completed_at = datetime.utcnow()
            db.commit()

            return {
                "id": disbursement.id,
                "application_id": disbursement.application_id,
                "amount": disbursement.amount,
                "payment_mode": disbursement.payment_mode,
                "payment_status": disbursement.payment_status,
                "payment_reference_id": None,
                "initiated_at": disbursement.initiated_at,
                "completed_at": disbursement.completed_at
            }

        if not payment_response.get("success"):

            disbursement.payment_status = DisbursementStatusEnum.FAILED
            disbursement.completed_at = datetime.utcnow()
            db.commit()

            return {
                "id": disbursement.id,
                "application_id": disbursement.application_id,
                "amount": disbursement.amount,
                "payment_mode": disbursement.payment_mode,
                "payment_status": disbursement.payment_status,
                "payment_reference_id": None,
                "initiated_at": disbursement.initiated_at,
                "completed_at": disbursement.completed_at
            }

        disbursement.payment_status = DisbursementStatusEnum.SUCCESS
        disbursement.payment_reference_id = payment_response.get("reference_id")
        disbursement.completed_at = datetime.utcnow()

        application.application_status = LoanApplicationStatus.DISBURSED
        application.disbursed_at = datetime.utcnow()

        db.commit()

        return {
            "id": disbursement.id,
            "application_id": disbursement.application_id,
            "amount": disbursement.amount,
            "payment_mode": disbursement.payment_mode,
            "payment_status": disbursement.payment_status,
            "payment_reference_id": disbursement.payment_reference_id,
            "initiated_at": disbursement.initiated_at,
            "completed_at": disbursement.completed_at
        }