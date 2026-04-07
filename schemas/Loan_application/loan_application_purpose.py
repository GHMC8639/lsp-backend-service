from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from core.enums import LoanPurpose


class LoanApplicationPurposeCreate(BaseModel):
    purpose_code: LoanPurpose
    purpose_description: Optional[str] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "purpose_code": "MEDICAL",
                "purpose_description": "Hospital expenses"
            }
        }
    )
    
    
class LoanApplicationPurposeUpdate(BaseModel):
    purpose_code: Optional[LoanPurpose] = None
    purpose_description: Optional[str] = Field(
        default=None,
        max_length=500)
    
class LoanApplicationPurposeResponse(BaseModel):
    application_id: int
    purpose_code: LoanPurpose
    purpose_description: Optional[str]
    message: str
    model_config = ConfigDict(from_attributes=True)

class LoanPurposeSummary(BaseModel):
    purpose_code: LoanPurpose
    purpose_description: Optional[str]


