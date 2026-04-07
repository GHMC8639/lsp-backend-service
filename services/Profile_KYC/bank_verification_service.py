from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.Profile_KYC.attempt_tracker import VerificationType
from models.Profile_KYC.user_profile import UserProfile
from repositories.Profile_KYC.user_repository import UserRepository
from repositories.Profile_KYC.attempt_tracker_repository import AttemptTrackerRepository
from repositories.Profile_KYC.kyc_bank_verification_repository import KYCBankVerificationRepository
from repositories.Profile_KYC.dummy_bank_account_repository import DummyBankAccountRepository
from utils.name_matcher import name_match_percentage
from core.config import settings

class BankVerificationService:

    @staticmethod
    def verify_bank_account(
        db: Session,
        user: UserProfile,
        account_number: str,
        account_holder_name: str,
        bank_name: str,
        ifsc: str,
    ) -> dict:
        if user.bank_status == "VERIFIED":
            raise HTTPException(400, "Bank account already verified")
        existing_verified_bank = KYCBankVerificationRepository.get_verified_by_account_number(db, account_number)
        if existing_verified_bank:
            raise HTTPException(409, "This bank account is already linked to another user")

        tracker = AttemptTrackerRepository.get_by_email_and_type(db, user.email, VerificationType.BANK)
        if not tracker:
            tracker = AttemptTrackerRepository.create_tracker(db, user.email, VerificationType.BANK)
        now = datetime.now(timezone.utc)
    

        if tracker.locked_until and tracker.locked_until > now:
            raise HTTPException(423, f"Bank verification blocked. Try after {settings.BANK_COOLDOWN_HOURS} hours.")

        if tracker.locked_until and tracker.locked_until <= now:
            AttemptTrackerRepository.reset_attempts(db, tracker)

        current_attempt = AttemptTrackerRepository.increment_attempt(db, tracker)

        bank_account   = DummyBankAccountRepository.get_by_account_number(db, account_number)
        failure_reason = None
        match_pct      = 0.0

        if not bank_account:
            failure_reason = "Bank account number not found in records"
        elif bank_account.ifsc.upper() != ifsc.upper():
            failure_reason = "IFSC code does not match bank records"
        elif bank_account.bank_name.upper().strip() != bank_name.upper().strip():
            failure_reason = "Bank name does not match records"
        elif not bank_account.is_active:
            failure_reason = "Bank account is inactive or closed - please use an active account"
        else:
            match_pct = name_match_percentage(account_holder_name, bank_account.account_holder_name)
            if match_pct < settings.NAME_MATCH_THRESHOLD:
                failure_reason = "Account holder name does not match bank records"

        if failure_reason:
            if current_attempt >= settings.BANK_MAX_ATTEMPTS:
                status           = "BLOCKED"
                user.bank_status = "BLOCKED"
                AttemptTrackerRepository.lock_tracker(
                    db, tracker, now + timedelta(hours=settings.BANK_COOLDOWN_HOURS)
                )
            else:
                status           = "FAILED"
                user.bank_status = "FAILED"

            KYCBankVerificationRepository.create_verification_log(
                db                    = db,
                user_id               = user.user_id,
                account_number        = account_number,
                account_holder_name   = account_holder_name,
                bank_name             = bank_name,
                ifsc                  = ifsc,
                name_match_percentage = match_pct,
                status                = status,
                failure_reason        = failure_reason,
                attempt_number        = current_attempt,
            )
            UserRepository.save(db) 

            remaining = settings.BANK_MAX_ATTEMPTS - current_attempt
            if remaining > 0:
                raise HTTPException(400, f"{failure_reason}. {remaining} attempt(s) remaining.")
            raise HTTPException(423, f"{failure_reason}. Maximum attempts reached. Blocked for {settings.BANK_COOLDOWN_HOURS} hours.")

    
        user.bank_status      = "VERIFIED"
        user.bank_locked      = True
        user.bank_verified_at = now

        KYCBankVerificationRepository.create_verification_log(
            db                    = db,
            user_id               = user.user_id,
            account_number        = account_number,
            account_holder_name   = account_holder_name,
            bank_name             = bank_name,
            ifsc                  = ifsc,
            name_match_percentage = match_pct,
            status                = "VERIFIED",
            failure_reason        = None,
            attempt_number        = current_attempt,
        )
        AttemptTrackerRepository.reset_attempts(db, tracker)
        UserRepository.update_user(db, user)

        return {
            "bank_status": "VERIFIED",
            "message":     "Bank account verified successfully",
        }
