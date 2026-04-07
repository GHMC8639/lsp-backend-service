from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_references import LoanApplicationReference
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker
from core.enums import LoanApplicationStep, enum_value
from services.Loan_application.loan_application_service import LoanApplicationService


class LoanApplicationReferenceService:

    # =====================================================
    # SAVE REFERENCES (AUTO DRAFT DETECTION)
    # =====================================================
    @staticmethod
    def save_references_form(
        db: Session,
        user_id: int,
        ref1_name,
        ref1_mobile_number,
        ref1_relation_type,
        ref1_is_emergency_contact,
        ref2_name,
        ref2_mobile_number,
        ref2_relation_type,
        ref2_is_emergency_contact,
    ):

        # 🔎 1️⃣ Find latest draft application for this user
        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail="No active draft application found"
            )

        # 🔐 Ensure editable
        LoanApplicationService.ensure_editable(application)

        # 🔎 2️⃣ Get step tracker
        tracker = db.query(LoanApplicationStepTracker).filter(
            LoanApplicationStepTracker.application_id == application.id
        ).first()

        if not tracker:
            raise HTTPException(
                status_code=400,
                detail="Application steps not initialized"
            )

        if not tracker.purpose_completed:
            raise HTTPException(
                status_code=400,
                detail="Complete purpose step before adding references"
            )

        try:
            # 🧹 3️⃣ Remove existing references
            db.query(LoanApplicationReference).filter(
                LoanApplicationReference.application_id == application.id
            ).delete()

            # ➕ 4️⃣ Create new references
            new_refs = [
                LoanApplicationReference(
                    application_id=application.id,
                    name=ref1_name,
                    mobile_number=ref1_mobile_number,
                    relation_type=ref1_relation_type,
                    is_emergency_contact=ref1_is_emergency_contact,
                    is_verified=False
                ),
                LoanApplicationReference(
                    application_id=application.id,
                    name=ref2_name,
                    mobile_number=ref2_mobile_number,
                    relation_type=ref2_relation_type,
                    is_emergency_contact=ref2_is_emergency_contact,
                    is_verified=False
                )
            ]

            db.add_all(new_refs)

            # ✅ 5️⃣ Update tracker
            tracker.references_completed = True
            tracker.last_completed_step = enum_value(LoanApplicationStep.REFERENCES)

            # Move to next step
            tracker.current_step = enum_value(LoanApplicationStep.DECLARATION)
            application.current_step = enum_value(LoanApplicationStep.DECLARATION)

            db.commit()

            for ref in new_refs:
                db.refresh(ref)

            return new_refs

        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to save references"
            )

    # =====================================================
    # GET REFERENCES (AUTO DRAFT DETECTION)
    # =====================================================
    @staticmethod
    def get_references(db: Session, user_id: int):

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail="No active draft application found"
            )

        refs = db.query(LoanApplicationReference).filter(
            LoanApplicationReference.application_id == application.id
        ).all()

        if not refs:
            raise HTTPException(
                status_code=404,
                detail="No references found"
            )

        return refs