from sqlalchemy.orm import Session
from models.Profile_KYC.user_profile import UserProfile

class KYCRepository:

    @staticmethod
    def get_user_kyc(db: Session, user_id: int):
        return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
