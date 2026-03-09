from sqlalchemy.orm import Session
from models.Tracking.loan_status_history import LoanStatusHistory
import uuid

class LoanStatusHistoryRepository:

    @staticmethod
    def create_history(db: Session, loan_application_id: str, previous_status: str | None,
                       new_status: str, source: str, metadata: dict | None):

        obj = LoanStatusHistory(
            loan_application_id=loan_application_id,
            previous_status=previous_status,
            new_status=new_status,
            source=source,
            status_metadata=metadata
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_timeline(db: Session, application_id: str):
        return (
            db.query(LoanStatusHistory)
            .filter(LoanStatusHistory.loan_application_id == application_id)
            .order_by(LoanStatusHistory.created_at.asc())
            .all()
        )
