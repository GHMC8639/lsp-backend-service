from pydantic import BaseModel


class FAQBase(BaseModel):
    category: str
    question: str
    answer: str


class FAQCreate(FAQBase):
    pass


class FAQResponse(FAQBase):
    id: int

    class Config:
        orm_mode = True

