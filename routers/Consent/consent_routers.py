from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from models.Consent.audit_logs import AuditLog
from models.Consent.consent_master import ConsentMaster
from models.Consent.user_consent import UserConsent
from schemas.Consent.Consent_schemas import (
    UserConsentRequest,
    RevokeConsentRequest,
)

router = APIRouter(prefix="/consent", tags=["Consent"])


# =====================================================
# RECORD CONSENT (USER ONLY)
# =====================================================
@router.post("/record")
def record_consent(
    payload: UserConsentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):

    user_id = current_user.id  # 🔥 from JWT

    if not payload.scroll_completed:
        raise HTTPException(400, "Please scroll through the document before accepting.")

    if not payload.accepted:
        raise HTTPException(400, "Consent not provided.")

    existing = db.query(UserConsent).filter(
        UserConsent.user_id == user_id,
        UserConsent.consent_type == payload.consent_type,
        UserConsent.revoked_at.is_(None)
    ).first()

    if existing:
        raise HTTPException(400, "Active consent already exists.")

    latest_doc = db.query(ConsentMaster).filter(
        ConsentMaster.type == payload.consent_type,
        ConsentMaster.active == True
    ).order_by(ConsentMaster.version.desc()).first()

    if not latest_doc:
        raise HTTPException(404, "Consent document not found.")

    consent = UserConsent(
        user_id=user_id,
        consent_type=payload.consent_type,
        version=latest_doc.version,
        accepted=True,
        scroll_completed=True,
        device_info=payload.device_info,
        ip_address=request.client.host,
        accepted_at=datetime.utcnow(),  # 🔥 fixed
    )

    db.add(consent)
    db.commit()
    db.refresh(consent)

    audit = AuditLog(
        action="CONSENT_ACCEPTED",
        user_id=user_id,
        details=f"{payload.consent_type} v{latest_doc.version} accepted from IP {request.client.host}"
    )

    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "message": "Consent recorded successfully."
    }


# =====================================================
# CONSENT HISTORY (USER ONLY)
# =====================================================
@router.get("/history")
def get_consent_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):

    history = db.query(UserConsent).filter(
        UserConsent.user_id == current_user.id
    ).all()

    if not history:
        return {"message": "No consent history found."}

    return history


# =====================================================
# REVOKE CONSENT (USER ONLY)
# =====================================================
@router.post("/revoke")
def revoke_consent(
    data: RevokeConsentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):

    consent = db.query(UserConsent).filter(
        UserConsent.user_id == current_user.id,
        UserConsent.consent_type == data.consent_type,
        UserConsent.revoked_at.is_(None)
    ).first()

    if not consent:
        raise HTTPException(404, "No active consent found to revoke")

    consent.revoked_at = datetime.utcnow()
    db.commit()
    db.refresh(consent)

    audit_log = AuditLog(
        action="CONSENT_REVOKED",
        user_id=current_user.id,
        details=f"Consent '{data.consent_type}' revoked from IP {request.client.host}"
    )

    db.add(audit_log)
    db.commit()

    return {
        "message": "Consent revoked successfully",
        "consent_id": consent.id
    }


# =====================================================
# CHECK CONSENT STATUS (USER ONLY)
# =====================================================
@router.get("/status")
def check_consent_status(
    consent_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):

    consent = db.query(UserConsent).filter(
        UserConsent.user_id == current_user.id,
        UserConsent.consent_type == consent_type,
        UserConsent.revoked_at.is_(None)
    ).order_by(UserConsent.accepted_at.desc()).first()

    if not consent:
        return {
            "active": False,
            "message": "No active consent found"
        }

    return {
        "active": True,
        "version": consent.version,
        "accepted_at": consent.accepted_at,
        "revoked_at": consent.revoked_at
    }