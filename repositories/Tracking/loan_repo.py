

from sqlalchemy.orm import Session
from models.Tracking.loan import Loan


class LoanRepository:

    @staticmethod
    def get_by_application_id(db: Session, app_id: int):
        return db.query(Loan).filter(
            Loan.application_id == app_id
        ).first()

    @staticmethod
    def create(db: Session, data: dict):
        loan = Loan(**data)
        db.add(loan)
        db.commit()
        db.refresh(loan)
        return loan