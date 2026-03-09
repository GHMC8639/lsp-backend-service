from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker
from core.enums import LoanApplicationStep, enum_value
from schemas.Loan_application.loan_application_declaration import (
    LoanApplicationDeclarationResponse
)


class LoanApplicationDeclarationService:

    @staticmethod
    def save_declaration(
        db: Session,
        user_id: int,
        payload,
        ip_address: str,
        user_agent: str,
    ):

        # 1️⃣ Get latest draft
        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active draft application found"
            )

        # 2️⃣ Get tracker
        tracker = db.query(LoanApplicationStepTracker).filter(
            LoanApplicationStepTracker.application_id == application.id
        ).first()

        if not tracker:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application steps not initialized"
            )

        if not tracker.references_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complete reference verification first"
            )

        # 3️⃣ Mandatory consent validation
        if not payload.agreed_terms:
            raise HTTPException(
                status_code=400,
                detail="You must agree to Terms & Conditions"
            )

        if not payload.consent_credit_check:
            raise HTTPException(
                status_code=400,
                detail="Credit bureau consent is mandatory"
            )

        if not payload.consent_data_sharing:
            raise HTTPException(
                status_code=400,
                detail="Data sharing consent is mandatory"
            )

        # 4️⃣ Save declaration fields
        application.has_existing_loans = payload.has_existing_loans
        application.has_credit_card = payload.has_credit_card
        application.has_default_history = payload.has_default_history

        application.agreed_terms = payload.agreed_terms
        application.consent_credit_check = payload.consent_credit_check
        application.consent_data_sharing = payload.consent_data_sharing

        application.terms_version = payload.terms_version
        application.privacy_policy_version = payload.privacy_policy_version

        application.declaration_accepted_at = datetime.now(timezone.utc)
        application.declaration_ip = ip_address
        application.declaration_user_agent = user_agent

        # 5️⃣ Move step to SUMMARY
        tracker.declaration_completed = True
        tracker.last_completed_step = enum_value(LoanApplicationStep.DECLARATION)
        tracker.current_step = enum_value(LoanApplicationStep.SUMMARY)

        application.current_step = enum_value(LoanApplicationStep.SUMMARY)

        db.commit()
        db.refresh(application)

        # 6️⃣ RETURN PROPER RESPONSE (NOT ORM)
        return LoanApplicationDeclarationResponse(
            has_existing_loans=application.has_existing_loans,
            has_credit_card=application.has_credit_card,
            has_default_history=application.has_default_history,
            agreed_terms=application.agreed_terms,
            consent_credit_check=application.consent_credit_check,
            consent_timestamp=application.declaration_accepted_at,
            ip_address=application.declaration_ip,
            user_agent=application.declaration_user_agent,
        )