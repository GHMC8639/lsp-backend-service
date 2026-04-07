from http.client import HTTPException

from sqlalchemy.orm import Session

from repositories.Tracking.loan_application_repo import LoanApplicationRepository
from repositories.Tracking.loan_status_history_repo import LoanStatusHistoryRepository


class TrackingService:

    @staticmethod
    def get_user_applications(db: Session, user_id: int):
        apps = LoanApplicationRepository.get_user_applications(db, user_id)
        response = []
        for app in apps:
            response.append({
                "id": app.id,
                "reference_number": app.reference_number,
                "approved_amount": app.approved_amount,
                "interest_rate": app.interest_rate,
                "requested_tenure_months": app.requested_tenure_months, 
                "application_status": app.application_status,
                "monthly_emi": app.monthly_emi,
                "current_status": app.application_status,
            })
        return response

    @staticmethod
    def get_application_status(db: Session, application_id: str, user_id: int):
        app = LoanApplicationRepository.get_by_id(db, application_id)
        if not app or app.user_id != user_id:
            return None

        return {
            "application_id": app.id,
            "reference_number": app.reference_number,
            "application_status": app.application_status

            }

    @staticmethod
    def get_application_timeline(db: Session, application_id: str, user_id: int):
        app = LoanApplicationRepository.get_by_id(db, application_id)
        if not app or app.user_id != user_id:
            raise HTTPException(status_code=404, 
                detail="Loan application not found.")  
        history = LoanStatusHistoryRepository.get_timeline(db, application_id)
        response = []
        for item in history:
            response.append({
                "id": item.id,
                "old_status": item.old_status,
                "new_status": item.new_status,
                "comment": item.comment,
                "created_at": item.created_at
            })
        return response
    
