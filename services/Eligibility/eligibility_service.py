from sqlalchemy.orm import Session
from models.Auth.user import User
from models.Eligibility.loan_eligibility import LoanEligibility

from repositories.Eligibility.credit_repository import CreditRepository
from repositories.Eligibility.eligibility_repository import EligibilityRepository

from core.Loan_calculator import (
    MAX_LOAN_AMOUNT as PLATFORM_MAX_LOAN_AMOUNT,
    calculate_emi
)


# ==============================
# CREDIT SCORE TIERS
# ==============================

CREDIT_SCORE_TIERS = [
    (800, 20_000),
    (750, 15_000),
    (700, 10_000),
    (650,  5_000),
]


def _get_tier_max_amount(credit_score: int) -> int:
    for min_score, amount in CREDIT_SCORE_TIERS:
        if credit_score >= min_score:
            return amount
    return 0


# ==============================
# EMI HELPERS (DYNAMIC RATE)
# ==============================

def _monthly_rate(annual_rate: float) -> float:
    return (annual_rate / 12) / 100


def generate_amortization_schedule(
    principal: float,
    tenure: int,
    interest_rate: float   # ✅ NEW
) -> list[dict]:

    r = _monthly_rate(interest_rate)

    emi = float(calculate_emi(principal, interest_rate, tenure))  # ✅ FIXED

    balance = principal
    schedule = []

    for month in range(1, tenure + 1):
        interest_part = round(balance * r, 2)
        principal_part = round(emi - interest_part, 2)
        balance = round(balance - principal_part, 2)

        if month == tenure:
            principal_part = round(principal_part + balance, 2)
            balance = 0.0

        schedule.append({
            "month": month,
            "emi": emi,
            "principal": principal_part,
            "interest": interest_part,
            "balance": max(balance, 0.0),
        })

    return schedule


def get_apr(interest_rate: float) -> float:
    return interest_rate   # ✅ from lender


# ==============================
# ELIGIBILITY SERVICE
# ==============================

class EligibilityService:

    @staticmethod
    def check_eligibility(db: Session, user: User) -> LoanEligibility:

        credit_profile = CreditRepository.get_latest_credit_profile(db, user.id)

        if not credit_profile:
            credit_profile = CreditRepository.create_dummy_credit_profile(db, user.id)

        if not credit_profile:
            return EligibilityRepository.save_or_update_eligibility(
                db,
                user.id,
                eligibility_status="REJECTED",
                failure_reason="CREDIT_PROFILE_NOT_FOUND",
            )

        credit_score = credit_profile.credit_score
        bureau_name = credit_profile.bureau_name
        existing_emi = float(credit_profile.total_existing_emi or 0)

        tier_amount = _get_tier_max_amount(credit_score)

        if tier_amount == 0:
            return EligibilityRepository.save_or_update_eligibility(
                db,
                user.id,
                eligibility_status="REJECTED",
                credit_profile_id=credit_profile.id,
                credit_score_used=credit_score,
                bureau_name=bureau_name,
                existing_emi=existing_emi,
                failure_reason="LOW_CREDIT_SCORE",
            )

        approved_amount = min(tier_amount, PLATFORM_MAX_LOAN_AMOUNT)

        return EligibilityRepository.save_or_update_eligibility(
            db,
            user.id,
            eligibility_status="ELIGIBLE",
            credit_profile_id=credit_profile.id,
            credit_score_used=credit_score,
            bureau_name=bureau_name,
            existing_emi=existing_emi,
            max_eligible_amount=approved_amount,
        )

    @staticmethod
    def validate_and_fetch(db: Session, user_id: int) -> LoanEligibility:

        record = (
            db.query(LoanEligibility)
            .filter(LoanEligibility.user_id == user_id)
            .first()
        )

        if not record:
            raise ValueError(
                "Eligibility not found. Please run eligibility check first."
            )

        if record.eligibility_status != "ELIGIBLE":
            raise ValueError(
                "User is not eligible to apply for loan."
            )

        return record