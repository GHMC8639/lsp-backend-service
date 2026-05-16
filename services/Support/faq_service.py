from sqlalchemy.orm import Session
from repositories.Support.faq_repository import get_all_active_faqs


def list_faqs(db: Session):
    return get_all_active_faqs(db)