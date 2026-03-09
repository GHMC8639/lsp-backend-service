from repositories.Tracking.notification_repo import NotificationRepository
from utils.notification_messages import get_notification_message


class NotificationService:

    @staticmethod
    def send_status_notification(db, user_id: int, application_id: str, status: str):
        message = get_notification_message(status)
        return NotificationRepository.create_notification(
            db=db,
            user_id=user_id,
            application_id=application_id,
            title=f"Loan Status: {status}",
            message=message
        )

    @staticmethod
    def send_custom_notification(db, user_id: int, title: str, message: str, application_id: str | None = None):
        return NotificationRepository.create_notification(
            db=db,
            user_id=user_id,
            application_id=application_id,
            title=title,
            message=message
        )

    @staticmethod
    def get_notifications(db, user_id: int):
        return NotificationRepository.get_notifications(db, user_id)
