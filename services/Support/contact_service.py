from sqlalchemy.orm import Session
from repositories.Support.contact_repositories import create_contact_message
from schemas.Support.contact_schema import ContactCreate


def create_contact(db: Session, data: ContactCreate):
    return create_contact_message(db, data)