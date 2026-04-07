from sqlalchemy.orm import Session
from repositories.Tracking.notification_repo import NotificationRepository
from core.config import settings


class NotificationService:

    @staticmethod
    def send_status_update(db: Session, user_id: int, application_id: int, status: str):
        data = {
            "user_id": user_id,
            "application_id": application_id,
            "title": "Loan Application Status Updated",
            "message": f"Your loan application status is now: {status}",
            "type": "STATUS_UPDATE",
            "channel": "IN_APP",
            "status": "SENT"
        }

        if settings.USE_MOCK_DATA:
            return NotificationRepository.create(db, data)

        try:
            return NotificationRepository.create(db, data)
        except Exception:
            data["status"] = "FAILED"
            return NotificationRepository.create(db, data)

    @staticmethod
    def send_custom_message(db: Session, user_id: int, application_id: int, title: str, message: str, notif_type="DOCUMENT"):
        data = {
            "user_id": user_id,
            "application_id": application_id,
            "title": title,
            "message": message,
            "type": notif_type,
            "channel": "IN_APP",
            "status": "SENT"
        }

        if settings.USE_MOCK_DATA:
            return NotificationRepository.create(db, data)

        try:
            return NotificationRepository.create(db, data)
        except:
            data["status"] = "FAILED"
            return NotificationRepository.create(db, data)

    @staticmethod
    def get_user_notifications(db: Session, user_id: int):
        return NotificationRepository.get_user_notifications(db, user_id)

    @staticmethod
    def mark_as_read(db: Session, notification_id: int):
        return NotificationRepository.mark_as_read(db, notification_id)
