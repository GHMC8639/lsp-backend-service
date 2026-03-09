from sqlalchemy.orm import Session
from models.Loan_application.loan_application import LoanApplication
from sqlalchemy import desc

class LoanApplicationRepository:

    @staticmethod
    def get_application(db: Session, application_id: str):
        return db.query(LoanApplication).filter(LoanApplication.id == application_id).first()

    @staticmethod
    def get_user_applications(db: Session, user_id: int):
        return (
            db.query(LoanApplication)
            .filter(LoanApplication.user_profile_id == user_id)
            .order_by(desc(LoanApplication.submitted_at))
            .all()
        )

    @staticmethod
    def update_status(db: Session, application_id: str, new_status: str):
        app = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()
        if not app:
            return None
        current_status = new_status
        db.commit()
        db.refresh(app)
        return app
