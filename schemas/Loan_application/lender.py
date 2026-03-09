from pydantic import BaseModel
from datetime import datetime


class LenderApplicationListResponse(BaseModel):
    application_id: int
    reference_number: str
    approved_amount: float
    tenure_months: int
    application_status: str
    submitted_at: datetime

    class Config:
        from_attributes = True


class LenderApplicationDetailResponse(BaseModel):
    id: int
    reference_number: str
    approved_amount: float
    requested_tenure_months: int
    interest_rate: float
    application_status: str
    created_at: datetime

    class Config:
        from_attributes = True
        
class LenderResponse(BaseModel):
    id: int
    company_name: str
    gst_number: str | None
    address: str | None
    is_active: bool

    class Config:
        from_attributes = True
