from datetime import datetime
import json
from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional, Dict, Any

class LoanStatusTimelineItem(BaseModel):
    id: int
    previous_status: Optional[str]
    new_status: str
    source: str
    status_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    @field_validator("status_metadata", mode="before")
    @classmethod
    def parse_status_metadata(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return None
        return value

    class Config:
        from_attributes = True



class LoanStatusTimelineResponse(BaseModel):
    success: bool = True
    total: int
    timeline: list[LoanStatusTimelineItem]

    class Config:
        from_attributes = True
