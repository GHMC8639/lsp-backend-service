from pydantic import BaseModel

class CreateTrackingRequest(BaseModel):
    loan_origination_id: int
    loan_amount: float
    tenure_months: int