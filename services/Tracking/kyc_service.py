from sqlalchemy.orm import Session
from repositories.Tracking.kyc_repo import KYCRepository


class KYCService:

    @staticmethod
    def fetch_user_kyc_status(db: Session, user_id: int) -> str | None:
        profile = KYCRepository.get_kyc_status(db, user_id)

        if not profile:
            return None

        return profile.kyc_status

    @staticmethod
    def is_kyc_completed(kyc_status: str | None) -> bool:
        return kyc_status == "COMPLETED"