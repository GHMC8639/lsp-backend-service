from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.Support.faq import FAQ

router = APIRouter(prefix="/faqs", tags=["FAQ"])


@router.get("/")
def get_faqs(db: Session = Depends(get_db)):
    return db.query(FAQ).all()


