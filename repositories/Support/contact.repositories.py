from sqlalchemy.orm import Session
from app.models.contact import Contact


class ContactRepository:

    def create(self, db: Session, contact: Contact):
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact