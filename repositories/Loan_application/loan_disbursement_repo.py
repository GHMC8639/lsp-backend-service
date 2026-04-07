from sqlalchemy.orm import Session
from typing import Optional

from models.Loan_application.loan_disbursements  import LoanDisbursement
from core.enums import DisbursementStatusEnum


class LoanDisbursementRepository:
    

    @staticmethod
    def create(db: Session, disbursement: LoanDisbursement):
        db.add(disbursement)
        db.commit()
        db.refresh(disbursement)
        return disbursement

    @staticmethod
    def get_by_application_id(
        db: Session,
        application_id: int
    ) -> Optional[LoanDisbursement]:
        return db.query(LoanDisbursement).filter(
            LoanDisbursement.application_id == application_id
        ).order_by(LoanDisbursement.id.desc()).first()

    @staticmethod
    def get_success_disbursement(
        db: Session,
        application_id: int
    ) -> Optional[LoanDisbursement]:
        return db.query(LoanDisbursement).filter(
            LoanDisbursement.application_id == application_id,
            LoanDisbursement.payment_status == DisbursementStatusEnum.SUCCESS
        ).first()
