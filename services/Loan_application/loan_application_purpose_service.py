from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_purpose import LoanApplicationPurpose
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker

from repositories.Loan_application.loan_application_purpose_repo import (
    LoanApplicationPurposeRepository,
)

from core.enums import LoanApplicationStep, enum_value
from services.Loan_application.loan_application_service import LoanApplicationService


class LoanApplicationPurposeService:

    # -----------------------------------------------------
    # SAVE PURPOSE (AUTO USER BASED)
    # -----------------------------------------------------
    @staticmethod
    def save_purpose(
        db: Session,
        user_id: int,
        purpose_code,
        purpose_description: str | None,
    ):

        # 1️⃣ Get latest draft application for user
        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active draft application found"
            )

        LoanApplicationService.ensure_editable(application)

        application_id = application.id

        # 2️⃣ Get step tracker
        tracker = db.query(LoanApplicationStepTracker).filter(
            LoanApplicationStepTracker.application_id == application_id
        ).first()

        if not tracker:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application steps not initialized"
            )

        if not tracker.loan_details_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complete loan details before selecting purpose"
            )

        # 3️⃣ Create or Update purpose
        existing = LoanApplicationPurposeRepository.get_by_application_id(
            db, application_id
        )

        if existing:
            existing.purpose_code = purpose_code
            existing.purpose_description = purpose_description
            purpose = existing
        else:
            purpose = LoanApplicationPurpose(
                application_id=application_id,
                purpose_code=purpose_code,
                purpose_description=purpose_description
            )
            purpose = LoanApplicationPurposeRepository.create(db, purpose)

        # 4️⃣ Update step tracker
        tracker.purpose_completed = True
        tracker.last_completed_step = enum_value(LoanApplicationStep.PURPOSE)

        # Move to next step only if currently at LOAN_DETAILS
        if tracker.current_step == enum_value(LoanApplicationStep.LOAN_DETAILS):
            next_step = enum_value(LoanApplicationStep.REFERENCES)
            tracker.current_step = next_step
            application.current_step = next_step

        db.commit()
        db.refresh(purpose)
        db.refresh(tracker)

        return {
    "application_id": application.id,
    "purpose_code": purpose.purpose_code,
    "purpose_description": purpose.purpose_description,
    "message": "Purpose saved successfully"
}

    # -----------------------------------------------------
    # GET PURPOSE (AUTO USER BASED)
    # -----------------------------------------------------
    @staticmethod
    def get_purpose(
        db: Session,
        user_id: int,
    ):

        # Get latest draft application
        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active draft application found"
            )

        purpose = LoanApplicationPurposeRepository.get_by_application_id(
            db, application.id
        )

        if not purpose:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purpose not found"
            )

        return purpose