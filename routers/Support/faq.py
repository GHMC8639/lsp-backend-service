from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from schemas.Support.faq_schema import FAQResponse
from services.Support.faq_service import list_faqs

router = APIRouter(prefix="/faqs")

@router.get("/", response_model=List[FAQResponse])
def get_faqs(db: Session = Depends(get_db)):
    return list_faqs(db)