from pydantic import BaseModel, EmailStr
from typing import Optional


class ProfileUpdate(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    mobile: Optional[str]
    address: Optional[str]


class ProfileResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    mobile: Optional[str]

    class Config:
        from_attributes = True