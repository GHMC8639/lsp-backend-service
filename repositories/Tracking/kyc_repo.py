from sqlalchemy.orm import Session
from models.Profile_KYC.user_profile import UserProfile as KYCProfile


class KYCRepository:

    @staticmethod
    def get_kyc_status(db: Session, user_id: int):
        return db.query(KYCProfile).filter(
            KYCProfile.user_id == user_id
        ).first()