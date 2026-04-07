from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from typing import List

from core.database import get_db
from models.Support.complaint import Complaint
from schemas.Support.complaint_schema import ComplaintCreate, ComplaintResponse

# ✅ ADD THESE
from core.permissions import user_required
from models.Auth.user import User

router = APIRouter(
    prefix="/api/v1/support",
    tags=["Complaint"]
)


# ------------------------------------------------
# CREATE COMPLAINT (USER)
# ------------------------------------------------
@router.post("/complaint", response_model=ComplaintResponse, status_code=201)
def create_complaint(
    data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    complaint_number = "CMP-" + str(random.randint(10000, 99999))
    sla_deadline = datetime.utcnow() + timedelta(days=30)

    complaint = Complaint(
        complaint_number=complaint_number,
        user_id=current_user.id,  # ✅ FIXED (secure)
        category=data.category,
        subject=data.subject,
        description=data.description,
        priority=data.priority,
        status="Open",
        sla_deadline=sla_deadline,
        escalated=False
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return complaint


# ------------------------------------------------
# GET ALL COMPLAINTS (ADMIN ONLY)
# ------------------------------------------------
@router.get("/complaints", response_model=List[ComplaintResponse])
def get_all_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    complaints = db.query(Complaint).all()

    for c in complaints:
        if c.status not in ["Resolved", "Closed"] and datetime.utcnow() > c.sla_deadline:
            c.escalated = True

    db.commit()
    return complaints


# ------------------------------------------------
# GET SINGLE COMPLAINT
# ------------------------------------------------
@router.get("/complaint/{id}", response_model=ComplaintResponse)
def get_complaint(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_required)
):
    complaint = db.query(Complaint).filter(Complaint.id == id).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # ✅ USER → only own complaint
    if current_user.role == "USER" and complaint.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # SLA check
    if complaint.status not in ["Resolved", "Closed"] and datetime.utcnow() > complaint.sla_deadline:
        complaint.escalated = True
        db.commit()

    return complaint