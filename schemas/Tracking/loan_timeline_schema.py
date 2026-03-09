from pydantic import BaseModel
from typing import List
from datetime import datetime


class StatusStep(BaseModel):
    status: str
    completed: bool
    timestamp: datetime | None

    class Config:
        from_attributes = True


class FullTimelineResponse(BaseModel):
    application_id: str
    steps: List[StatusStep]

    class Config:
        from_attributes = True
