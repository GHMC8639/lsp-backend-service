from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from models.Auth.user import User
from schemas.Support.chat_schema import ChatCreate, ChatResponse
from services.Support.chat_service import send_chat_message, get_chat_history
from core.dependencies import require_roles

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
def post_chat_message(
    data: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER", "ADMIN", "SUPER_ADMIN"))
):
    return send_chat_message(db, data, current_user)


@router.get("/history", response_model=List[ChatResponse])
def fetch_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER", "ADMIN", "SUPER_ADMIN"))
):
    return get_chat_history(db, current_user)