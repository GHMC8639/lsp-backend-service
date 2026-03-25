from pydantic import BaseModel
from typing import Optional   


class SettingsUpdate(BaseModel):
    biometric_enabled: Optional[bool] = None
    pin_enabled: Optional[bool] = None
    language: Optional[str] = None
    push_notification: Optional[bool] = None
    sms_notification: Optional[bool] = None
    email_notification: Optional[bool] = None


class SettingsResponse(BaseModel):
    id: int
    user_id: int
    biometric_enabled: bool
    pin_enabled: bool
    account_locked: bool
    is_deleted: bool
    language: str
    push_notification: bool
    sms_notification: bool
    email_notification: bool

    class Config:
        from_attributes = True