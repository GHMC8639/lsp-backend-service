from sqlalchemy.orm import Session
from models.Esign.disbursement import Disbursement
from core.exceptions import throw_error
from core.logger import logger
from datetime import datetime


class DisbursementService:

    # ------------------------------------------------
    # GET DISBURSEMENT STATUS
    # ------------------------------------------------
    def get_status(self, loan_id: int, db: Session):

        logger.info(f"[DISBURSEMENT] Fetching status for loan_id={loan_id}")

        if loan_id <= 0:
            throw_error("Invalid loan id", 400)

        disbursement = db.query(Disbursement).filter(
            Disbursement.loan_id == loan_id
        ).first()

        # If no record → still pending
        if not disbursement:
            return {
                "loan_id": loan_id,
                "status": "PENDING"
            }

        return {
                "loan_id": loan_id,
                "status": disbursement.status,
                "amount": disbursement.amount,
                "utr_number": disbursement.utr_number,
                "expected_credit_time": "24-48 hours",
                "bank_account": "XXXXXX1234",  # mock for now
                "updated_at": disbursement.updated_at
        }

    # ------------------------------------------------
    # CONFIRM DISBURSEMENT
    # ------------------------------------------------
    def confirm(self, loan_id: int, db: Session):

        logger.info(f"[DISBURSEMENT] Confirming disbursement for loan_id={loan_id}")

        if loan_id <= 0:
            throw_error("Invalid loan id", 400)

        disbursement = db.query(Disbursement).filter(
            Disbursement.loan_id == loan_id
        ).first()

        # If no record → create
        if not disbursement:
            disbursement = Disbursement(
                loan_id=loan_id,
                status="SUCCESS",
                amount=0,  # can update later from loan service
                utr_number=f"UTR{loan_id}123",
                bank_account="XXXXXX1234",
                updated_at=datetime.utcnow()
            )
            db.add(disbursement)

        else:
            # If already success → idempotent
            if disbursement.status == "SUCCESS":
                return {
                    "loan_id": loan_id,
                    "status": "SUCCESS",
                    "message": "Already disbursed"
                }

            disbursement.status = "SUCCESS"
            disbursement.updated_at = datetime.utcnow()

        db.commit()

        return {
        "loan_id": loan_id,
        "status": "SUCCESS",
        "message": "Loan Disbursed Successfully",
        "utr_number": disbursement.utr_number,
        "amount": disbursement.amount,
        "first_emi_date": "2026-04-01"  # TODO: Fetch from Loan Service
    }