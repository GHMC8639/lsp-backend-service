from pydantic import BaseModel


class SettingsResponse(BaseModel):
    push_notification: bool
    sms_notification: bool
    email_notification: bool

    application_updates: bool
    payment_reminders: bool
    promotional_offers: bool
    product_updates: bool

    biometric_enabled: bool
    pin_enabled: bool

    language: str

    class Config:
        from_attributes = True