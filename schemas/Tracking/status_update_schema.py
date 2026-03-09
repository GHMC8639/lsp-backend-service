from typing import Optional, Dict
from pydantic import BaseModel


class StatusUpdateRequest(BaseModel):
    application_id: str
    new_status: str
    source: str     # system / admin / nbfc
    metadata: Optional[Dict] = None

    class Config:
        from_attributes = True


class StatusUpdateResponse(BaseModel):
    success: bool
    message: str
    updated_status: Optional[str] = None

    class Config:
        from_attributes = True