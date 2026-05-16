from fastapi import HTTPException, BackgroundTasks
import requests

from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from decimal import Decimal

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_transaction import LoanTransaction
from models.Profile_KYC.user_profile import UserProfile
from models.Esign.agreements import Agreement

from services.payment.razorpay_service import RazorpayService

from repositories.Loan_application.loan_disbursement_repo import LoanDisbursementRepository
from repositories.Loan_application.loan_transaction_repo import LoanTransactionRepository

from core.enums import (
    LoanApplicationStatus,
    DisbursementStatusEnum,
    PaymentModeEnum
)
from core.config import settings
from core.email_service import EmailService
from core.logger import logger


def match_payment_method(b, payment_mode):
    if getattr(b, "status", None) != "VERIFIED":
        return False

    if payment_mode.value == "BANK":
        return bool(getattr(b, "account_number", None))

    if payment_mode.value == "UPI":
        return bool(getattr(b, "upi_id", None))

    return False


class LoanDisbursementService:

    @staticmethod
    def disburse_loan(
        db: Session,
        application_id: int,
        payment_mode: PaymentModeEnum,
        background_tasks: BackgroundTasks | None = None   # ✅ NEW
    ):

        try:
            application = db.query(LoanApplication).options(
                joinedload(LoanApplication.user_profile)
                .joinedload(UserProfile.bank_verifications),
                joinedload(LoanApplication.user_profile)
                .joinedload(UserProfile.user)
            ).filter(
                LoanApplication.id == application_id
            ).with_for_update().first()

            if not application:
                raise HTTPException(404, "Application not found")

            existing = LoanDisbursementRepository.get_by_application_id(db, application.id)
            if existing and existing.payment_status == DisbursementStatusEnum.SUCCESS:
                raise HTTPException(400, "Loan already disbursed")

            if application.application_status not in [
                LoanApplicationStatus.DISBURSEMENT_INITIATED,
                LoanApplicationStatus.ESIGN_COMPLETED
            ]:
                raise HTTPException(400, "Invalid state for disbursement")

            agreement = db.query(Agreement).filter(
                Agreement.application_id == application.id,
                Agreement.is_active == True
            ).first()

            if not agreement or agreement.esign_status != "SIGNED":
                raise HTTPException(400, "Agreement not signed")

            if not application.disbursed_amount:
                raise HTTPException(400, "Amount not ready")

            profile = application.user_profile
            user = profile.user

            payout_method = next(
                (b for b in profile.bank_verifications if match_payment_method(b, payment_mode)),
                None
            )

            if not payout_method:
                raise HTTPException(400, "No verified payout method")

            net_amount = float(application.disbursed_amount)

            # 💸 Razorpay
            razorpay = RazorpayService()
            payout = razorpay.process_payout(
                name=profile.full_name,
                account_number=payout_method.account_number,
                ifsc=payout_method.ifsc_code,
                amount=net_amount,
                email=profile.email,
                phone=user.mobile_number
            )

            if not payout.get("success"):
                raise HTTPException(500, payout.get("error"))

            payout_id = payout.get("payout_id")
            payout_status = payout.get("status")

            disbursement = LoanDisbursementRepository.upsert(
                db,
                application_id=application.id,
                data={
                    "amount": Decimal(net_amount),
                    "payment_mode": payment_mode,
                    "payment_status": DisbursementStatusEnum.PROCESSING,
                    "payment_reference_id": payout_id,
                    "updated_at": datetime.utcnow()
                }
            )

            transaction = LoanTransaction(
                application_id=application.id,
                disbursement_id=disbursement.id,
                transaction_type="DISBURSEMENT",
                amount=Decimal(net_amount),
                status="PROCESSING",
                payment_mode=payment_mode.value,
                remarks="Payout initiated via Razorpay"
            )

            LoanTransactionRepository.create(db, transaction)

            # 🔄 Update application
            application.application_status = LoanApplicationStatus.DISBURSED
            application.payout_status = payout_status.upper()
            application.disbursed_at = datetime.utcnow()

            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"[DISBURSE ERROR] {str(e)}")
            raise

        # =====================================================
        # 📧 EMAIL (ASYNC - NON BLOCKING)
        # =====================================================
        try:
            email_body = f"""
            Dear {profile.full_name},

            Your loan has been successfully disbursed.

            Details:
            Amount: ₹{net_amount}
            Application ID: {application.id}

            Thank you.
            """

            if background_tasks:
                background_tasks.add_task(
                    EmailService.send_email,
                    profile.email,
                    "Loan Disbursed Successfully",
                    email_body
                )
            else:
                # fallback (sync)
                EmailService.send_email(
                    profile.email,
                    "Loan Disbursed Successfully",
                    email_body
                )

            logger.info(f"[EMAIL QUEUED] user={profile.email}")

        except Exception as e:
            logger.error(f"[EMAIL ERROR] {str(e)}")

        # =====================================================
        # 🔄 EXTERNAL MODULE CALL
        # =====================================================
        try:
            requests.post(
                settings.TRACKING_URL,
                json={
                    "application_id": application.id,
                    "user_id": application.user_profile.user_id,
                    "status": "DISBURSED"
                },
                timeout=5
            )
        except Exception as e:
            logger.error(f"[TRACKING ERROR] {str(e)}")

        return {
            "application_id": application.id,
            "payout_id": payout_id,
            "payout_status": payout_status,
            "application_status": application.application_status
        }