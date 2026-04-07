from pydantic import BaseModel
from typing import Optional


# =====================================================
# ADMIN – Create Consent Document
# =====================================================
class ConsentMasterCreate(BaseModel):
    type: str
    version: str
    content: str
    active: bool = True


# =====================================================
# USER – Record Consent
# =====================================================
class UserConsentRequest(BaseModel):
    consent_type: str
    accepted: bool
    scroll_completed: bool
    device_info: Optional[str] = None


# =====================================================
# USER – Revoke Consent
# =====================================================
class RevokeConsentRequest(BaseModel):
    consent_type: str
    reason: Optional[str] = None