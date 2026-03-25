from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class ComplaintCreate(BaseModel):
    user_id: int
    category: str
    subject: str
    description: str
    priority: Literal["LOW", "MEDIUM", "HIGH"]


class ComplaintResponse(BaseModel):
    id: int
    complaint_number: str
    user_id: int
    category: str
    subject: str
    description: str
    priority: str
    status: str
    escalated: bool
    sla_deadline: datetime

    class Config:
        from_attributes = True





