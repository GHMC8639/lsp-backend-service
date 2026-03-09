from pydantic import BaseModel, Field, field_validator
from typing import Optional
from core.validators import (
    validate_mobile_number,
    validate_otp,
    validate_device_id,
    validate_password,
    validate_username
)

# ================= SEND OTP =================
class SendOTPSchema(BaseModel):
    mobile_number: str
    device_id: str | None = Field(default=None)

    _validate_mobile = field_validator("mobile_number")(validate_mobile_number)
    _validate_device = field_validator("device_id")(validate_device_id)


# ================= VERIFY OTP =================
class VerifyOTPSchema(BaseModel):
    
    mobile_number: str
    otp: str
    username:str
    password: str
    device_id: str
    _validate_mobile = field_validator("mobile_number")(validate_mobile_number)
    _validate_otp = field_validator("otp")(validate_otp)
    _validate_device = field_validator("device_id")(validate_device_id)





class UpdateUserSchema(BaseModel):
    username: Optional[str]
    mobile_number: Optional[str]
    device_id: Optional[str]
    is_active: Optional[bool]