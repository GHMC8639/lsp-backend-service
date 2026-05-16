from sqlalchemy.orm import Session
from repositories.Support.chat_repository import create_chat_message, get_chat_history_by_user
from schemas.Support.chat_schema import ChatCreate
from models.Auth.user import User


def send_chat_message(db: Session, data: ChatCreate, current_user: User):
    
    # decide sender based on role
    if current_user.role in ["ADMIN", "SUPER_ADMIN"]:
        sender = "admin"
    else:
        sender = "user"

    return create_chat_message(
        db=db,
        user_id=current_user.id,   # ✅ FIX (no more NULL error)
        message=data.message,
        sender=sender
    )


def get_chat_history(db: Session, current_user: User):
    return get_chat_history_by_user(db, current_user.id)