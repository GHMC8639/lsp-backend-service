from sqlalchemy.orm import Session
from app.models.faq import FAQ


class FAQRepository:

    def get_all(self, db: Session):
        return db.query(FAQ).all()

    def get_by_category(self, db: Session, category: str):
        return db.query(FAQ).filter(FAQ.category == category).all()