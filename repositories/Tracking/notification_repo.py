from sqlalchemy.orm import Session
from models.Tracking.notification import Notification
import uuid

class NotificationRepository:

    @staticmethod
    def create_notification(db: Session, user_id: int, title: str, message: str,
                            application_id: str | None = None):
        notification = Notification(

            user_id=user_id,
            application_id=application_id,
            title=title,
            message=message
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_notifications(db: Session, user_id: int):
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )
