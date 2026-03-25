from pydantic import BaseModel
from typing import Optional
from uuid import UUID

# FAQ Response
class FAQResponse(BaseModel):
    id: int
    question: str
    answer: str

    class Config:
        from_attributes = True


# Contact
class ContactCreate(BaseModel):
    message: str
    user_id: Optional[UUID] = None   # optional, backend generates if not provided


# Chat
class ChatCreate(BaseModel):
    message: str
    user_id: Optional[UUID] = None   # consistent with DB


# Complaint
class ComplaintCreate(BaseModel):
    description: str
    user_id: Optional[UUID] = None


# Ticket Create
class TicketCreate(BaseModel):
    title: str
    description: str
    priority: str
    user_id: Optional[UUID] = None


# Ticket Update
class TicketUpdate(BaseModel):
    status: str
