from typing import List, Optional

from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from schemas.Support.complaint_schema import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintDetailResponse,
)

from services.Support.complaint_service import (
    register_complaint,
    list_complaints,
    get_complaint_detail,
)

from services.Support.cloudinary_upload_services import upload_support_attachment

from core.enums import ComplaintCategory, ComplaintPriority


router = APIRouter(
    prefix="/api/v1/support",
    tags=["Complaints"]
)


# =====================================================
# USER - CREATE COMPLAINT
# =====================================================
@router.post("/complaint", response_model=ComplaintResponse)
async def create_new_complaint(
    category: ComplaintCategory = Form(...),
    subject: str = Form(...),
    description: str = Form(...),
    priority: ComplaintPriority = Form(ComplaintPriority.MEDIUM),
    attachment: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    attachment_url = None

    if attachment:
        attachment_url = await upload_support_attachment(
            attachment=attachment,
            category=category.value,
            user_id=current_user.id,
        )

    data = ComplaintCreate(
        category=category,
        subject=subject,
        description=description,
        priority=priority,
        attachment_url=attachment_url,
    )

    return register_complaint(
        db=db,
        payload=data,
        current_user=current_user,
        attachment_path=attachment_url,
    )


# =====================================================
# USER - GET OWN COMPLAINTS
# =====================================================
@router.get("/complaints", response_model=List[ComplaintResponse])
def get_complaint_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    return list_complaints(db, current_user)


# =====================================================
# USER - GET SINGLE COMPLAINT
# =====================================================
@router.get("/complaint/{complaint_id}", response_model=ComplaintDetailResponse)
def get_single_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    return get_complaint_detail(db, complaint_id, current_user)