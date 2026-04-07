from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from core.database import get_db
from models.Support.faq import FAQ

# ✅ ADD THIS
from core.permissions import user_required
from core.dependencies import get_current_user
from models.Auth.user import User


router = APIRouter(
    prefix="/faqs",
    tags=["FAQ"]
)


# ------------------------------------------------
# GET ALL FAQ (PUBLIC / USER)
# ------------------------------------------------
@router.get("/")
def get_faqs(db: Session = Depends(get_db)):
    return db.query(FAQ).all()


# ------------------------------------------------
# CREATE FAQ (ADMIN ONLY)
# ------------------------------------------------
@router.post("/")
def create_faq(
    question: str,
    answer: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    faq = FAQ(question=question, answer=answer)

    db.add(faq)
    db.commit()
    db.refresh(faq)

    return faq


# ------------------------------------------------
# UPDATE FAQ (ADMIN ONLY)
# ------------------------------------------------
@router.put("/{faq_id}")
def update_faq(
    faq_id: int = Path(..., gt=0),
    question: str = None,
    answer: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()

    if not faq:
        return {"error": "FAQ not found"}

    if question:
        faq.question = question
    if answer:
        faq.answer = answer

    db.commit()
    db.refresh(faq)

    return faq


# ------------------------------------------------
# DELETE FAQ (ADMIN ONLY)
# ------------------------------------------------
@router.delete("/{faq_id}")
def delete_faq(
    faq_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()

    if not faq:
        return {"error": "FAQ not found"}

    db.delete(faq)
    db.commit()

    return {"message": "FAQ deleted successfully"}