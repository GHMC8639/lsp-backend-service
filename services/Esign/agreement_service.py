from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models.Esign.agreements import Agreement
from models.Loan_application.loan_application import LoanApplication
from models.Profile_KYC.user_profile import UserProfile

from core.logger import logger
from core.exceptions import throw_error

from services.Esign.pdf_generator import PDFGenerator


class AgreementService:

    def __init__(self, pdf: PDFGenerator):
        self.pdf = pdf

    # =====================================================
    # 📄 GENERATE / FETCH AGREEMENT
    # =====================================================
    def fetch_agreement_for_user(self, user_id: int, db: Session):

        logger.info(f"[Agreement] Fetching for user_id={user_id}")

        try:
            # -------------------------------------------------
            # 🔍 GET USER PROFILE
            # -------------------------------------------------
            profile = db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()

            if not profile:
                throw_error("User profile not found", 404)

            # ✅ FIXED HERE
            user_profile_id = profile.id
            logger.info(f"[PROFILE ID]: {user_profile_id}")

            # -------------------------------------------------
            # 🔍 FETCH APPROVED APPLICATION
            # -------------------------------------------------
            application = db.query(LoanApplication).filter(
                LoanApplication.user_profile_id == user_profile_id,
                LoanApplication.application_status == "APPROVED"
            ).order_by(LoanApplication.id.desc()).with_for_update().first()

            if not application:
                throw_error("No approved application found", 404)

            application_id = application.id

            # -------------------------------------------------
            # 🔍 CHECK EXISTING AGREEMENT
            # -------------------------------------------------
            existing = db.query(Agreement).filter(
                Agreement.application_id == application_id,
                Agreement.is_active == True
            ).first()

            if existing:
                return {
                    "exists": True,
                    "loan_id": application_id,
                    "pdf_path": existing.agreement_pdf_path,
                    "status": existing.esign_status,
                    "provider_ref": getattr(existing, "provider_ref", None),
                    "signed_pdf_path": getattr(existing, "signed_pdf_path", None)
                }

            # -------------------------------------------------
            # 🔢 VERSIONING
            # -------------------------------------------------
            latest = db.query(Agreement).filter(
                Agreement.application_id == application_id
            ).order_by(Agreement.version.desc()).first()

            new_version = 1 if not latest else latest.version + 1

            # -------------------------------------------------
            # 📄 GENERATE PDF
            # -------------------------------------------------
            pdf_output = self.pdf.generate_agreement(
                application_id=application_id,
                borrower_name=getattr(application, "full_name", f"User-{user_id}"),
                loan_amount=application.approved_amount,
            )

            file_path = pdf_output.get("file_path")

            if not file_path:
                throw_error("PDF generation failed", 500)

            file_hash = self.pdf.generate_hash(file_path)

            # -------------------------------------------------
            # ❗ DEACTIVATE OLD AGREEMENTS (IMPORTANT)
            # -------------------------------------------------
            db.query(Agreement).filter(
                Agreement.application_id == application_id,
                Agreement.is_active == True
            ).update({"is_active": False})

            # -------------------------------------------------
            # 💾 SAVE AGREEMENT
            # -------------------------------------------------
            agreement = Agreement(
                application_id=application_id,
                user_id=user_id,
                version=new_version,
                agreement_pdf_path=file_path,
                file_hash=file_hash,
                is_active=True,
                esign_status="PENDING"
            )

            db.add(agreement)

            # -------------------------------------------------
            # 🔄 UPDATE APPLICATION STATUS
            # -------------------------------------------------
            application.application_status = "AGREEMENT_GENERATED"

            db.commit()
            db.refresh(agreement)

            return {
                "exists": False,
                "loan_id": application_id,
                "pdf_path": file_path,
                "status": agreement.esign_status,
                "provider_ref": None,
                "signed_pdf_path": None
            }

        except SQLAlchemyError as db_err:
            db.rollback()
            logger.error(f"[Agreement][DB ERROR]: {str(db_err)}")
            throw_error("Database error while generating agreement", 500)

        except Exception as e:
            db.rollback()
            logger.error(f"[Agreement][ERROR]: {str(e)}")
            throw_error("Agreement generation failed", 500)