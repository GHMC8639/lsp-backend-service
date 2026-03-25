from pydantic import BaseModel


class GrievanceCreate(BaseModel):
    name: str
    designation: str
    email: str
    phone: str
    office_address: str
    working_hours: str

