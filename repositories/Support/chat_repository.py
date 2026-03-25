from sqlalchemy.orm import Session
from app.models.chat import Chat


class ChatRepository:

    def create_message(self, db: Session, chat: Chat):
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat

    def get_chat_history(self, db: Session, user_id: int):
        return db.query(Chat).filter(Chat.user_id == user_id).all()