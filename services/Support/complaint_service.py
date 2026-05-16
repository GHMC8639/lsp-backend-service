from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from core.email_service import sendmail
from models.Support.complaint import Complaint
from models.Support.complaint_history import ComplaintHistory
from models.Profile_KYC.user_profile import UserProfile

from core.enums import ComplaintStatusEnum


# =====================================================
# GENERATE COMPLAINT NUMBER
# =====================================================

def generate_complaint_number(db: Session):
    count = db.query(Complaint).count() + 1
    today = datetime.utcnow().strftime("%Y%m%d")
    return f"CMP-{today}-{count:05d}"


# =====================================================
# USER - CREATE COMPLAINT
# =====================================================
def register_complaint(db: Session, payload, current_user, attachment_path=None):
    user_profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if not user_profile:
        raise HTTPException(
            status_code=404,
            detail="User profile not found. Please complete profile first."
        )

    if not user_profile.email:
        raise HTTPException(
            status_code=400,
            detail="Email not found in user profile."
        )

    if user_profile.email_verified is False:
        raise HTTPException(
            status_code=400,
            detail="Please verify your email before raising a complaint."
        )

    complaint = Complaint(
        complaint_number=generate_complaint_number(db),
        user_id=current_user.id,
        application_id=getattr(payload, "application_id", None),
        category=payload.category.value if hasattr(payload.category, "value") else payload.category,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority.value if hasattr(payload.priority, "value") else payload.priority,
        status=ComplaintStatusEnum.OPEN.value,
        attachment_url=attachment_path,
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    history = ComplaintHistory(
        complaint_id=complaint.id,
        old_status=None,
        new_status=ComplaintStatusEnum.OPEN.value,
        changed_by=str(current_user.id),
        comment="Complaint created by user",
    )

    db.add(history)
    db.commit()
    db.refresh(complaint)

    subject = f"Complaint Registered Successfully - {complaint.complaint_number}"

    body = f"""
Hello {user_profile.full_name},

Your complaint has been registered successfully.

Complaint Number: {complaint.complaint_number}
Category: {complaint.category}
Subject: {complaint.subject}
Priority: {complaint.priority}
Status: {complaint.status}

Our support team will review your complaint and update you soon.

Thank you,
LSP Support Team
"""

    try:
        sendmail(
            to=user_profile.email,
            subject=subject,
            body=body,
        )
    except Exception as e:
        print("Email sending failed:", str(e))

    return complaint


# =====================================================
# USER - LIST OWN COMPLAINTS
# =====================================================
def list_complaints(db: Session, current_user):
    return db.query(Complaint).filter(
        Complaint.user_id == current_user.id
    ).order_by(
        Complaint.created_at.desc()
    ).all()


# =====================================================
# USER - GET OWN COMPLAINT DETAIL
# =====================================================
def get_complaint_detail(db: Session, complaint_id: int, current_user):
    complaint = db.query(Complaint).filter(
        Complaint.id == complaint_id,
        Complaint.user_id == current_user.id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return complaint


# =====================================================
# SUPER ADMIN - LIST ALL COMPLAINTS GROUPED BY USER
# =====================================================
def admin_list_all_complaints_grouped_by_user(db: Session, current_user):
    complaints = db.query(Complaint).order_by(
        Complaint.created_at.desc()
    ).all()

    grouped_data = {}

    for complaint in complaints:
        user_id = complaint.user_id

        if user_id not in grouped_data:
            grouped_data[user_id] = {
                "user_id": user_id,
                "total_complaints": 0,
                "complaints": []
            }

        grouped_data[user_id]["total_complaints"] += 1
        grouped_data[user_id]["complaints"].append({
            "id": complaint.id,
            "complaint_number": complaint.complaint_number,
            "category": complaint.category,
            "subject": complaint.subject,
            "priority": complaint.priority,
            "status": complaint.status,
            "created_at": complaint.created_at,
        })

    return {
        "total_users": len(grouped_data),
        "data": list(grouped_data.values())
    }


# =====================================================
# SUPER ADMIN - GET COMPLAINT DETAIL
# =====================================================
def admin_get_complaint_detail(db: Session, complaint_id: int, current_user):
    complaint = db.query(Complaint).filter(
        Complaint.id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return complaint


# =====================================================
# SUPPORT TEAM - LIST ALL COMPLAINTS
# =====================================================
def support_list_all_complaints(db: Session, current_user):
    complaints = db.query(Complaint).order_by(
        Complaint.created_at.desc()
    ).all()

    return {
        "total_complaints": len(complaints),
        "open": sum(1 for c in complaints if c.status == ComplaintStatusEnum.OPEN.value),
        "in_progress": sum(1 for c in complaints if c.status == ComplaintStatusEnum.IN_PROGRESS.value),
        "resolved": sum(1 for c in complaints if c.status == ComplaintStatusEnum.RESOLVED.value),
        "closed": sum(1 for c in complaints if c.status == ComplaintStatusEnum.CLOSED.value),
        "complaints": complaints
    }


# =====================================================
# SUPPORT TEAM - GET COMPLAINT DETAIL
# =====================================================
def support_get_complaint_detail(db: Session, complaint_id: int, current_user):
    complaint = db.query(Complaint).filter(
        Complaint.id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return complaint


# =====================================================
# SUPPORT TEAM - UPDATE COMPLAINT STATUS
# =====================================================
def support_update_complaint_status(db: Session, complaint_id: int, payload, current_user):
    complaint = db.query(Complaint).filter(
        Complaint.id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    current_status = complaint.status
    new_status = payload.status.value if hasattr(payload.status, "value") else payload.status

    allowed_transitions = {
        ComplaintStatusEnum.OPEN.value: [
            ComplaintStatusEnum.IN_PROGRESS.value,
        ],
        ComplaintStatusEnum.IN_PROGRESS.value: [
            ComplaintStatusEnum.RESOLVED.value,
            ComplaintStatusEnum.CLOSED.value,
        ],
        ComplaintStatusEnum.RESOLVED.value: [
            ComplaintStatusEnum.CLOSED.value,
        ],
        ComplaintStatusEnum.CLOSED.value: [],
    }

    if new_status not in allowed_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status change from {current_status} to {new_status}"
        )

    complaint.status = new_status
    complaint.updated_at = datetime.utcnow()

    if new_status == ComplaintStatusEnum.RESOLVED.value:
        complaint.resolved_at = datetime.utcnow()

    if new_status == ComplaintStatusEnum.CLOSED.value:
        complaint.closed_at = datetime.utcnow()

    history = ComplaintHistory(
        complaint_id=complaint.id,
        old_status=current_status,
        new_status=new_status,
        changed_by=str(current_user.id),
        comment=payload.comment,
    )

    db.add(history)
    db.commit()
    db.refresh(complaint)

    # Fetch user profile email
    user_profile = db.query(UserProfile).filter(
        UserProfile.user_id == complaint.user_id
    ).first()

    if user_profile and user_profile.email and user_profile.email_verified:
        subject = f"Complaint Status Updated - {complaint.complaint_number}"

        body = f"""
Hello {user_profile.full_name},

Your complaint status has been updated.

Complaint Number: {complaint.complaint_number}
Subject: {complaint.subject}
Old Status: {current_status}
New Status: {complaint.status}

Support Comment:
{payload.comment if payload.comment else "No comment provided."}

Thank you,
LSP Support Team
"""

        try:
            sendmail(
                to=user_profile.email,
                subject=subject,
                body=body,
            )
        except Exception as e:
            print("Status update email sending failed:", str(e))

    return {
        "message": "Complaint status updated successfully",
        "complaint_id": complaint.id,
        "complaint_number": complaint.complaint_number,
        "old_status": current_status,
        "new_status": complaint.status,
        "updated_by": current_user.id,
    }