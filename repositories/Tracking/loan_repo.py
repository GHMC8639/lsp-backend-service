from sqlalchemy.orm import Session
from models.Tracking.loan import Loan
import uuid

class LoanRepository:

    @staticmethod
    def create_loan(db: Session, application_id: str, principal: float,
                    interest_rate: float, emi_amount: float):

        loan = Loan(
            id=uuid.uuid4(),
            application_id=application_id,
            principal=principal,
            interest_rate=interest_rate,
            emi_amount=emi_amount,
            status="ACTIVE"
        )
        db.add(loan)
        db.commit()
        db.refresh(loan)
        return loan

    @staticmethod
    def get_loan_by_application(db: Session, application_id: str):
        return db.query(Loan).filter(Loan.application_id == application_id).first()
