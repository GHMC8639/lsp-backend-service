from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.Support.contact_schema import ContactCreate, ContactResponse
from services.Support.contact_service import create_contact

router = APIRouter()

@router.post("/contact", response_model=ContactResponse)
def submit_contact(data: ContactCreate, db: Session = Depends(get_db)):
    return create_contact(db, data)