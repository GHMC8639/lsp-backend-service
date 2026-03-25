from pydantic import BaseModel


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    status: str

    class Config:
        from_attributes = True
