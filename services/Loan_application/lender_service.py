from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from  models.Loan_application.loan_application import LoanApplication
from  models.Eligibility.loan_eligibility import LoanEligibility
from  models.Auth.user import User
from  core.enums import LoanApplicationStatus, LoanApplicationStep, enum_value


class LenderService:

    @staticmethod
    def get_submitted_applications(db: Session):

        return db.query(LoanApplication).filter(
            LoanApplication.application_status == LoanApplicationStatus.SUBMITTED,
            LoanApplication.lender_id == None
        ).order_by(LoanApplication.created_at.desc()).all()

    @staticmethod
    def get_lender_applications(db: Session, lender_id: int):

        return db.query(LoanApplication).filter(
            LoanApplication.lender_id == lender_id
        ).order_by(LoanApplication.updated_at.desc()).all()

    @staticmethod
    def pick_application(db: Session, application_id: int, lender_id: int):

        lender = db.query(User).filter(
            User.id == lender_id,
            User.is_active == True,
            User.is_blocked == False
        ).first()

        if not lender:
            raise HTTPException(404, "Lender not found or inactive")

        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).with_for_update().first()

        if not application:
            raise HTTPException(404, "Application not found")

        if application.lender_id is not None:
            raise HTTPException(400, "Already picked by another lender")

        if application.application_status != LoanApplicationStatus.SUBMITTED:
            raise HTTPException(400, "Application not available for picking")

        application.lender_id = lender.id
        application.application_status = LoanApplicationStatus.UNDER_REVIEW
        application.current_step = enum_value(LoanApplicationStep.SUBMITTED)
        application.reviewed_at = datetime.utcnow()

        db.commit()

        return {"message": "Application picked successfully"}

    @staticmethod
    def approve_application(db: Session, application_id: int, lender_id: int):

        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).with_for_update().first()

        if not application:
            raise HTTPException(404, "Application not found")

        if application.lender_id != lender_id:
            raise HTTPException(403, "You did not pick this application")

        if application.application_status != LoanApplicationStatus.UNDER_REVIEW:
            raise HTTPException(400, "Application not in review stage")

        # Just update status (amount already from eligibility)
        application.application_status = LoanApplicationStatus.APPROVED
        application.current_step = enum_value(LoanApplicationStep.SUBMITTED)
        application.approved_at = datetime.utcnow()

        db.commit()

        return {"message": "Application approved successfully"}

    @staticmethod
    def reject_application(
        db: Session,
        application_id: int,
        lender_id: int,
        rejection_reason: str
    ):

        if not rejection_reason:
            raise HTTPException(400, "Rejection reason required")

        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).with_for_update().first()

        if not application:
            raise HTTPException(404, "Application not found")

        if application.lender_id != lender_id:
            raise HTTPException(403, "You did not pick this application")

        if application.application_status != LoanApplicationStatus.UNDER_REVIEW:
            raise HTTPException(400, "Application not in review stage")

        application.application_status = LoanApplicationStatus.REJECTED
        application.rejected_at = datetime.utcnow()
        application.rejection_reason = rejection_reason

        db.commit()

        return {"message": "Application rejected successfully"}