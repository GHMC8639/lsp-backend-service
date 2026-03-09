from pydantic import BaseModel
from typing import Optional


# =====================================================
# INITIATE (No request body needed)
# =====================================================

class AadhaarInitiateResponse(BaseModel):
    message: str
    auth_url: Optional[str] = None
    initiate_token: str
    token_expires_in: str
    attempt: str
    mode: str


# =====================================================
# VERIFY
# =====================================================

class AadhaarVerificationRequest(BaseModel):
    initiate_token: str
    auth_code: Optional[str] = None


class AadhaarVerificationResponse(BaseModel):
    message: str
    aadhaar_status: str
    identity_status: str
    next_step: str