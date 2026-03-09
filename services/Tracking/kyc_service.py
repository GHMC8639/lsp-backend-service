from repositories.Tracking.kyc_repo import KYCRepository

class KYCService:

    @staticmethod
    def fetch_kyc_status(db, user_id: int):
        profile = KYCRepository.get_user_kyc(db, user_id)

        if not profile:
            return {
                "pan": "PENDING",
                "aadhaar": "PENDING",
                "bank": "PENDING",
                "overall": "INCOMPLETE"
            }

        return {
            "pan": profile.pan_status,
            "aadhaar": profile.aadhaar_status,
            "bank": profile.bank_status,
            "identity": profile.identity_status,
            "document": profile.document_status,
            "overall": profile.kyc_status
        }