from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.Support.chat import ChatMessage
from models.Auth.user import User
from schemas.Support.chat_schema import ChatCreate, ChatResponse
from typing import List
from fastapi import HTTPException


router = APIRouter(
    prefix="/api/v1/support/chat",
    tags=["Chat"]
)


@router.post("/message", response_model=ChatResponse, status_code=201)
def send_chat(data: ChatCreate, db: Session = Depends(get_db)):
    chat = ChatMessage(
        user_id=data.user_id,
        message=data.message,
        sender="user"   # default sender
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat

@router.get("/history", response_model=List[ChatResponse])
def chat_history(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found"
        )

    chats = db.query(ChatMessage).filter(
        ChatMessage.user_id == user_id
    ).all()

 
    if not chats:
        raise HTTPException(
            status_code=404,
            detail=f"No chat history found for user_id {user_id}"
        )

    return chats