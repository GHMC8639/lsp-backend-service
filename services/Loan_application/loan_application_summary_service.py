from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker
from models.Auth.user import User

from core.enums import LoanApplicationStep, enum_value
from services.Loan_application.loan_calculator import calculate_loan_summary
from schemas.Loan_application.loan_application_summary import *


class LoanApplicationSummaryService:

    @staticmethod
    def get_summary_by_user(db: Session, user_id: int):

        # 1️⃣ Get latest draft (NOT submitted)
        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail="No active draft application found"
            )

        if not application.approved_amount:
            raise HTTPException(
                status_code=400,
                detail="Eligible amount not available"
            )

        # 2️⃣ Get user profile
        profile = db.query(User).filter(
            User.id == application.user_profile_id
        ).first()

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )

        # 3️⃣ Step tracker validation
        tracker = db.query(LoanApplicationStepTracker).filter(
            LoanApplicationStepTracker.application_id == application.id
        ).first()

        if not tracker:
            raise HTTPException(
                status_code=400,
                detail="Application steps not initialized"
            )

        # 4️⃣ Mandatory step validation
        if not tracker.loan_details_completed:
            raise HTTPException(
                status_code=400,
                detail={"pending_step": "LOAN_DETAILS"}
            )

        if not tracker.purpose_completed:
            raise HTTPException(
                status_code=400,
                detail={"pending_step": "PURPOSE"}
            )

        if not tracker.references_completed:
            raise HTTPException(
                status_code=400,
                detail={"pending_step": "REFERENCES"}
            )

        if not tracker.declaration_completed:
            raise HTTPException(
                status_code=400,
                detail={"pending_step": "DECLARATION"}
            )

        # 5️⃣ Loan calculation
        loan_calc = calculate_loan_summary(
            principal=float(application.approved_amount),
            tenure_months=application.requested_tenure_months
        )

        # 6️⃣ User summary
        user_summary = UserSummarySchema(
            user_id=profile.id,
            full_name=profile.full_name,
            mobile_number=profile.mobile_number,
            email=profile.email
        )

        # 7️⃣ Loan details
        loan_details = LoanDetailsSummarySchema(
            approved_amount=application.approved_amount,
            requested_tenure_months=application.requested_tenure_months,
            interest_rate=loan_calc["interest_rate"],
            emi_amount=loan_calc["emi"],
            total_repayment=loan_calc["total_repayment"],
            processing_fee=loan_calc["processing_fee"],
            gst_on_processing_fee=loan_calc["gst_on_processing_fee"],
            total_processing_charges=loan_calc["total_processing_charges"],
            lender_name=None
        )

        # 8️⃣ Purpose
        if not application.purpose:
            raise HTTPException(
                status_code=400,
                detail={"pending_step": "PURPOSE"}
            )

        purpose = LoanPurposeSummarySchema(
            purpose=application.purpose.purpose_code
        )

        # 9️⃣ References
        if not application.references or len(application.references) < 2:
            raise HTTPException(
                status_code=400,
                detail={"pending_step": "REFERENCES"}
            )

        reference_list = [
            ReferenceSummarySchema(
                name=ref.name,
                relationship=ref.relation_type,
                mobile_number=ref.mobile_number,
                is_mobile_verified=ref.is_verified
            )
            for ref in application.references
        ]

        verified_count = sum(ref.is_verified for ref in application.references)

        reference_status = ReferencesStatusSchema(
            total_required=2,
            total_added=len(application.references),
            verified_count=verified_count,
            remaining_to_verify=max(0, 2 - verified_count)
        )

        # 🔟 Declaration (stored directly in application)
        declaration = DeclarationSummarySchema(
            # has_existing_loans=application.has_existing_loans,
            # has_credit_card=application.has_credit_card,
            # has_default_history=application.has_default_history,
            # declaration_accepted=application.agreed_terms
        )

        # 1️⃣1️⃣ Submission status
        submission_status = SubmissionStatusSchema(
            last_completed_step=tracker.last_completed_step,
            can_submit=True,
            pending_steps=[]
        )

        return LoanApplicationSummaryResponseSchema(
            application_id=application.id,
            user=user_summary,
            loan_details=loan_details,
            purpose=purpose,
            references=reference_list,
            reference_status=reference_status,
            declaration=declaration,
            submission_status=submission_status
        )