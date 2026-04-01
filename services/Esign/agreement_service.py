from sqlalchemy.orm import Session

from models.Esign.agreements import Agreement

from core.logger import logger
from core.exceptions import throw_error

from services.Esign.pdf_generator import PDFGenerator
from services.Esign.loan_client import LoanClient

from utils.response import success_response


class AgreementService:

    def __init__(self, pdf: PDFGenerator, loan_client: LoanClient):
        self.pdf = pdf
        self.loan_client = loan_client

    # FETCH AGREEMENT (RETURN EXISTING OR CREATE NEW)
    def fetch_agreement(self, loan_id: int, db: Session):

        logger.info(f"[Agreement] Fetching agreement for loan_id={loan_id}")

        if loan_id <= 0:
            throw_error("Invalid loan id", 400)

        # Fetch loan details
        loan = self.loan_client.get_loan_sync(loan_id)

        if not loan:
            throw_error("Loan not found", 404)

        if loan["loan_status"] != "APPROVED":
            throw_error("Loan is not approved", 403)

        # Check existing agreement
        existing = db.query(Agreement).filter(
            Agreement.loan_id == loan_id,
            Agreement.is_active == True
        ).first()

        if existing:
            return success_response(
                "Agreement already exists",
                {
                    "exists": True,
                    "loan_id": loan_id,
                    "version": existing.version,
                    "pdf_path": existing.agreement_pdf_path,
                    "file_hash": existing.file_hash,
                }
            )

        # Determine next version
        latest = db.query(Agreement).filter(
            Agreement.loan_id == loan_id
        ).order_by(Agreement.version.desc()).first()

        new_version = 1 if not latest else latest.version + 1

        # Generate agreement PDF
        pdf_output = self.pdf.generate_agreement(
            loan_id=loan_id,
            borrower_name=loan["borrower_name"],
            loan_amount=loan["loan_amount"],
        )

        file_path = pdf_output["file_path"]

        # Generate hash
        file_hash = self.pdf.generate_hash(file_path)

        # Save agreement
        agreement = Agreement(
            loan_id=loan_id,
            user_id=1,
            version=new_version,
            agreement_pdf_path=file_path,
            file_hash=file_hash,
            is_active=True,
        )

        db.add(agreement)
        db.commit()
        db.refresh(agreement)

        return success_response(
            "Agreement generated",
            {
                "exists": False,
                "loan_id": loan_id,
                "version": new_version,
                "pdf_path": file_path,
                "file_hash": file_hash,
            }
        )

    # VERIFY HASH
    def verify_hash(self, loan_id: int, db: Session):

        logger.info(f"[Agreement] Verifying hash for loan_id={loan_id}")

        agreement = db.query(Agreement).filter(
            Agreement.loan_id == loan_id,
            Agreement.is_active == True
        ).first()

        if not agreement:
            throw_error("Agreement not found", 404)

        generated_hash = self.pdf.generate_hash(
            agreement.agreement_pdf_path
        )

        if generated_hash != agreement.file_hash:
            throw_error("Document has been modified", 409)

        return success_response(
            "Hash verified",
            {
                "loan_id": loan_id,
                "hash": generated_hash
            }
        )