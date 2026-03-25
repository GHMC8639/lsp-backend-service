from pydantic import BaseModel
from typing import Optional


class ChatCreate(BaseModel):
    user_id: int
    message: str


class ChatResponse(BaseModel):
    id: int
    user_id: int
    message: str
    sender: str

    class Config:
        from_attributes = True