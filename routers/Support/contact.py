from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.Support.contact import ContactMessage
from schemas.Support.contact import ContactCreate

router = APIRouter(
    prefix="/api/v1/support/contact",
    tags=["Contact"]
)


@router.post("/", status_code=201)
def create_contact(data: ContactCreate, db: Session = Depends(get_db)):
    msg = ContactMessage(**data.dict())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"message": "Contact submitted successfully"}
