from repositories.Tracking.loan_application_repo import LoanApplicationRepository
from repositories.Tracking.loan_status_history_repo import LoanStatusHistoryRepository
from schemas.Tracking.loan_application_schema import (
    LoanApplicationListItem,
    LoanApplicationListResponse,
    LoanApplicationBase
)
from schemas.Tracking.loan_status_schema import (
    LoanStatusTimelineItem,
    LoanStatusTimelineResponse
)
from models.Loan_application.loan_application import LoanApplication
from services.Tracking.kyc_service import KYCService
import uuid


class TrackingService:

    @staticmethod
    def list_applications(db, user_id: int):
        apps = LoanApplicationRepository.get_user_applications(db, user_id)

        response_items = []

        for app in apps:
            kyc = KYCService.fetch_kyc_status(db, user_id)

            item = LoanApplicationListItem.model_validate(app)
            item_dict = item.model_dump()

            item_dict["pan_status"] = kyc["pan"]
            item_dict["aadhaar_status"] = kyc["aadhaar"]
            item_dict["bank_status"] = kyc["bank"]
            item_dict["overall_kyc"] = kyc["overall"]

            response_items.append(item_dict)

        return {
            "total": len(response_items),
            "applications": response_items
        }

    @staticmethod
    def get_current_status(db, application_id: str):
        app = LoanApplicationRepository.get_application(db, application_id)
        if not app:
            return None

        kyc = KYCService.fetch_kyc_status(db, app.user_id)

        base = LoanApplicationBase.model_validate(app)
        base_dict = base.model_dump()

        base_dict["pan_status"] = kyc["pan"]
        base_dict["aadhaar_status"] = kyc["aadhaar"]
        base_dict["bank_status"] = kyc["bank"]
        base_dict["overall_kyc"] = kyc["overall"]

        return base_dict

    @staticmethod
    def get_timeline(db, application_id: str):
        history = LoanStatusHistoryRepository.get_timeline(db, application_id)
        items = [LoanStatusTimelineItem.model_validate(h) for h in history]

        if not items:
            app = db.query(LoanApplication).filter(
                LoanApplication.id == application_id
            ).first()

            if not app:
                return LoanStatusTimelineResponse(total=0, timeline=[])

            return {
                "total": 1,
                "timeline": [
                    LoanStatusTimelineItem(
                        previous_status=None,
                        new_status="DRAFT",
                        source="system",
                        status_metadata={"fallback": True},
                        created_at=app.created_at
                    ).model_dump()
                ]
            }

        return {
            "total": len(items),
            "timeline": [i.model_dump() for i in items]
        }

    @staticmethod
    def create_tracking_entry(
        db,
        user_id: int,
        loan_origination_id: int,
        loan_amount: float,
        tenure: int
    ):
        tracking = LoanApplication(
            user_profile_id=user_id,
            eligibility_id=loan_origination_id,
            approved_amount=loan_amount,
            requested_tenure_months=tenure,
            application_status="DRAFT",
            current_step="OPENED"
        )

        db.add(tracking)
        db.commit()
        db.refresh(tracking)

        LoanStatusHistoryRepository.create_history(
            db=db,
            loan_application_id=tracking.id,
            previous_status=None,
            new_status="DRAFT",
            source="system",
            metadata={"origin": "module_5"}
        )

        return tracking