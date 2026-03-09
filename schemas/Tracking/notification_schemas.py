from datetime import datetime
from pydantic import BaseModel
from typing import List
from uuid import UUID


class NotificationSchema(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    success: bool = True
    total: int
    notifications: List[NotificationSchema]

    class Config:
        from_attributes = True


class NotificationMarkReadRequest(BaseModel):
    notification_id: str

    class Config:
        from_attributes = True
