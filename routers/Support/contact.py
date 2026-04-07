from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from models.Support.contact import ContactMessage
from schemas.Support.contact import ContactCreate

# ✅ ADD THIS
from core.permissions import user_required
from core.dependencies import get_current_user
from models.Auth.user import User


router = APIRouter(
    prefix="/api/v1/support/contact",
    tags=["Contact"]
)


# ------------------------------------------------
# CREATE CONTACT (PUBLIC / USER)
# ------------------------------------------------
@router.post("/", status_code=201)
def create_contact(
    data: ContactCreate,
    db: Session = Depends(get_db),
):
    msg = ContactMessage(**data.dict())

    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {"message": "Contact submitted successfully"}


# ------------------------------------------------
# LIST CONTACT MESSAGES (ADMIN ONLY)
# ------------------------------------------------
@router.get("/")
def list_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    return db.query(ContactMessage).all()