from datetime import datetime
from pydantic import BaseModel
from uuid import UUID
 
 
class LoanApplicationBase(BaseModel):
    id: UUID
    loan_amount: float
    tenure_months: int
    current_status: str
    submitted_at: datetime
 
    model_config = {
        "from_attributes": True
    }
 
 
class LoanApplicationListItem(BaseModel):
    id: UUID
    loan_amount: float
    tenure_months: int
    current_status: str
    submitted_at: datetime
 
    model_config = {
        "from_attributes": True
    }
 
 
class LoanApplicationListResponse(BaseModel):
    success: bool = True
    total: int
    applications: list[LoanApplicationListItem]
 
    model_config = {
        "from_attributes": True
    }