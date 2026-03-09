from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import random
import hashlib
from fastapi import HTTPException

from models.Loan_application.loan_application_references_otp import ReferenceMobileOTP
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker
from models.Loan_application.loan_application import LoanApplication
from repositories.Loan_application.loan_application_reference_repo import (
    LoanApplicationReferenceRepository
)
from core.enums import LoanApplicationStep, enum_value


COOLDOWN_SECONDS = 30
MAX_OTP_PER_IP_10_MIN = 5
OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 3


class ReferenceOTPService:

    # =====================================================
    # SEND OTP (AUTO DRAFT + MOBILE)
    # =====================================================
    @staticmethod
    def send_reference_otp(
        db: Session,
        user_id: int,
        mobile_number: str,
        client_ip: str
    ):

        # 1️⃣ Get latest draft
        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail="No active draft application found"
            )

        # 2️⃣ Find reference under this application
        references = LoanApplicationReferenceRepository.get_by_application_id(
            db, application.id
        )

        reference = next(
            (r for r in references if r.mobile_number == mobile_number),
            None
        )

        if not reference:
            raise HTTPException(
                status_code=404,
                detail="Reference not found for this application"
            )

        now = datetime.now(timezone.utc)

        # 3️⃣ Cooldown
        cooldown_time = now - timedelta(seconds=COOLDOWN_SECONDS)

        recent_otp = db.query(ReferenceMobileOTP).filter(
            ReferenceMobileOTP.reference_id == reference.id,
            ReferenceMobileOTP.created_at >= cooldown_time,
            ReferenceMobileOTP.is_used == False
        ).first()

        if recent_otp:
            raise HTTPException(
                status_code=400,
                detail="Please wait before requesting OTP again"
            )

        # 4️⃣ IP rate limit
        ten_min_ago = now - timedelta(minutes=10)

        otp_count = db.query(ReferenceMobileOTP).filter(
            ReferenceMobileOTP.ip_address == client_ip,
            ReferenceMobileOTP.created_at >= ten_min_ago
        ).count()

        if otp_count >= MAX_OTP_PER_IP_10_MIN:
            raise HTTPException(
                status_code=429,
                detail="Too many OTP requests from this IP"
            )

        # 5️⃣ Invalidate old unused OTPs
        db.query(ReferenceMobileOTP).filter(
            ReferenceMobileOTP.reference_id == reference.id,
            ReferenceMobileOTP.is_used == False
        ).update({"is_used": True})

        # 6️⃣ Generate OTP
        otp_plain = str(random.randint(100000, 999999))
        hashed_otp = hashlib.sha256(otp_plain.encode()).hexdigest()

        new_otp = ReferenceMobileOTP(
            reference_id=reference.id,
            otp_code=hashed_otp,
            expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES),
            attempts=0,
            is_used=False,
            ip_address=client_ip
        )

        db.add(new_otp)
        db.commit()

        print(f"Reference OTP (Dev Mode): {otp_plain}")

        return {"message": "OTP sent successfully"}


    # =====================================================
    # VERIFY OTP (AUTO DRAFT + AUTO REFERENCE)
    # =====================================================
    @staticmethod
    def verify_reference_otp(
        db: Session,
        user_id: int,
        otp_code: str,
        client_ip: str
    ):

        now = datetime.now(timezone.utc)

        # 1️⃣ Get latest draft
        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail="No active draft application found"
            )

        # 2️⃣ Get all references
        references = LoanApplicationReferenceRepository.get_by_application_id(
            db, application.id
        )

        if not references:
            raise HTTPException(
                status_code=404,
                detail="No references found"
            )

        reference_ids = [ref.id for ref in references]

        # 3️⃣ Get latest active OTP among references
        otp = db.query(ReferenceMobileOTP).filter(
            ReferenceMobileOTP.reference_id.in_(reference_ids),
            ReferenceMobileOTP.is_used == False
        ).order_by(
            ReferenceMobileOTP.created_at.desc()
        ).first()

        if not otp:
            raise HTTPException(
                status_code=400,
                detail="No active OTP found"
            )

        # 4️⃣ Expiry check
        if otp.expires_at < now:
            otp.is_used = True
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="OTP expired"
            )

        # 5️⃣ Attempt limit
        if otp.attempts >= MAX_ATTEMPTS:
            otp.is_used = True
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="OTP attempts exceeded"
            )

        # 6️⃣ Verify
        hashed_input = hashlib.sha256(otp_code.encode()).hexdigest()

        if otp.otp_code != hashed_input:
            otp.attempts += 1
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP"
            )

        # ✅ SUCCESS
        otp.is_used = True
        otp.verified_at = now
        otp.reference.is_verified = True

        db.commit()
        db.refresh(otp.reference)

        ReferenceOTPService.update_application_step_if_references_verified(
            db,
            otp.reference.application_id
        )

        return {
            "reference_id": otp.reference_id,
            "verified": True,
            "verified_at": otp.verified_at
        }


    # =====================================================
    # AUTO STEP UPDATE
    # =====================================================
    @staticmethod
    def update_application_step_if_references_verified(
        db: Session,
        application_id: int
    ):

        references = LoanApplicationReferenceRepository.get_by_application_id(
            db, application_id
        )

        if not references:
            return

        if all(ref.is_verified for ref in references):

            tracker = db.query(LoanApplicationStepTracker).filter_by(
                application_id=application_id
            ).first()

            if not tracker:
                return

            tracker.references_completed = True
            tracker.last_completed_step = enum_value(
                LoanApplicationStep.REFERENCES
            )
            tracker.current_step = enum_value(
                LoanApplicationStep.DECLARATION
            )

            application = db.get(LoanApplication, application_id)

            if application:
                application.current_step = enum_value(
                    LoanApplicationStep.DECLARATION
                )

            db.commit()