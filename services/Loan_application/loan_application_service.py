from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker

from core.enums import (
    LoanApplicationStatus,
    LoanApplicationStep,
    enum_value,
    EligibilityStatusEnum,
)

from repositories.Eligibility.eligibility_repository import EligibilityRepository
from core.reference_generator import generate_loan_reference_number
from services.Loan_application.loan_application_validation import validate_final_submission
from services.Loan_application.loan_application_lock_manager_service import ApplicationLockManager
from services.Loan_application.loan_calculator import calculate_loan_summary

from schemas.Loan_application.loan_application import (
    LoanSubmitResponseSchema,
    LoanApplicationResponseSchema,
)


class LoanApplicationService:

    # ---------------------------------------------------
    # STATE PROTECTION
    # ---------------------------------------------------
    @staticmethod
    def ensure_editable(application: LoanApplication):

        if application.is_submitted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submitted applications cannot be modified"
            )

        if application.application_status in [
            enum_value(LoanApplicationStatus.SUBMITTED),
            enum_value(LoanApplicationStatus.APPROVED),
            enum_value(LoanApplicationStatus.REJECTED),
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application cannot be modified in current state"
            )

    # ---------------------------------------------------
    # APPLY LOAN
    # ---------------------------------------------------
    @staticmethod
    def apply_loan(
        db: Session,
        user_id: int,
        requested_tenure: int
    ):

        eligibility = EligibilityRepository.get_latest_by_user(db, user_id)

        if not eligibility:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Run eligibility check first."
            )

        if eligibility.eligibility_status == EligibilityStatusEnum.REJECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=eligibility.failure_reason or "User not eligible"
            )

        if not eligibility.max_eligible_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Eligible amount missing"
            )

        # Enforce only ONE draft per user
        existing_draft = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).first()

        if existing_draft:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have an active draft application"
            )

        application = LoanApplication(
            user_profile_id=user_id,
            eligibility_id=eligibility.id,
            approved_amount=eligibility.max_eligible_amount,
            requested_tenure_months=requested_tenure,
            application_status=enum_value(LoanApplicationStatus.DRAFT),
            current_step=enum_value(LoanApplicationStep.LOAN_DETAILS),
            is_submitted=False,
        )

        db.add(application)
        db.flush()

        tracker = LoanApplicationStepTracker(
            application_id=application.id,
            loan_details_completed=True,
            purpose_completed=False,
            references_completed=False,
            declaration_completed=False,
            current_step=enum_value(LoanApplicationStep.LOAN_DETAILS),
            last_completed_step=enum_value(LoanApplicationStep.LOAN_DETAILS)
        )

        db.add(tracker)
        db.commit()
        db.refresh(application)

        return {
            "application_id": application.id,
            "application_status": application.application_status,
            "approved_amount": application.approved_amount,
            "requested_tenure_months": application.requested_tenure_months,
        }

    # ---------------------------------------------------
    # GET LATEST APPLICATION
    # ---------------------------------------------------
    @staticmethod
    def get_latest_application(
        db: Session,
        user_id: int
    ):

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id
        ).order_by(LoanApplication.created_at.desc()).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No application found"
            )

        return LoanApplicationResponseSchema(
            application_id=application.id,
            application_status=application.application_status,
            current_step=application.current_step,
            approved_amount=application.approved_amount,
            requested_tenure_months=application.requested_tenure_months,
            interest_rate=application.interest_rate
        )

    # ---------------------------------------------------
    # SUBMIT LATEST DRAFT
    # ---------------------------------------------------
    @staticmethod
    def submit_latest_application(
        db: Session,
        user_id: int,
        confirm: bool
    ) -> LoanSubmitResponseSchema:

        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation required"
            )

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.created_at.desc()).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No draft application found"
            )

        tracker = db.query(LoanApplicationStepTracker).filter(
            LoanApplicationStepTracker.application_id == application.id
        ).first()

        if not tracker:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Step tracker missing"
            )

        # Validate entire workflow before submission
        validate_final_submission(db, application, tracker)

        # Update steps
        tracker.current_step = enum_value(LoanApplicationStep.SUBMITTED)
        tracker.last_completed_step = enum_value(LoanApplicationStep.SUMMARY)

        # Calculate EMI
        loan_summary = calculate_loan_summary(
            principal=float(application.approved_amount),
            tenure_months=application.requested_tenure_months
        )

        # Finalize Application
        application.reference_number = generate_loan_reference_number(db)
        application.application_status = enum_value(LoanApplicationStatus.SUBMITTED)
        application.current_step = enum_value(LoanApplicationStep.SUBMITTED)
        application.is_submitted = True
        application.submitted_at = datetime.now(timezone.utc)

        application.interest_rate = loan_summary["interest_rate"]
        application.monthly_emi = loan_summary["emi"]
        application.processing_fee = loan_summary["processing_fee"]
        application.gst_amount = loan_summary["gst_on_processing_fee"]
        application.total_repayment = loan_summary["total_repayment"]

        # Lock application
        ApplicationLockManager.lock_application(application)

        db.commit()
        db.refresh(application)

        return LoanSubmitResponseSchema(
            reference_number=application.reference_number,
            message="Loan application submitted successfully",
            expected_decision_time="24 hours"
        )