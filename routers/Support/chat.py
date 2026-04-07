from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from models.Support.chat import ChatMessage
from models.Auth.user import User
from schemas.Support.chat_schema import ChatCreate, ChatResponse

# ✅ ADD THESE
from core.permissions import user_required

router = APIRouter(
    prefix="/support/chat",
    tags=["Chat"]
)


# ------------------------------------------------
# SEND MESSAGE (USER)
# ------------------------------------------------
@router.post("/message", response_model=ChatResponse, status_code=201)
def send_chat(
    data: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    chat = ChatMessage(
        user_id=current_user.id,   # ✅ FIXED
        message=data.message,
        sender="user"
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat


# ------------------------------------------------
# CHAT HISTORY
# ------------------------------------------------
@router.get("/history", response_model=List[ChatResponse])
def chat_history(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):

    # ✅ USER → only own chats
    if current_user.role == "USER":
        user_id = current_user.id

    # ✅ ADMIN → can view any user
    if current_user.role in ["ADMIN", "SUPER_ADMIN"] and not user_id:
        raise HTTPException(
            status_code=400,
            detail="user_id is required for admin"
        )

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
        return []  # ✅ better than 404

    return chats