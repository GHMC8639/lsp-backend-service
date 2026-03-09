from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal
from core.enums import LoanApplicationStep, LoanTenureMonths


# =====================================================
# APPLY REQUEST
# =====================================================
class LoanApplicationCreateSchema(BaseModel):
    requested_tenure_months: LoanTenureMonths

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "requested_tenure_months": 3
            }
        }
    )


# =====================================================
# APPLY RESPONSE (ONLY DRAFT CREATION RESPONSE)
# =====================================================
class LoanApplicationCreateResponseSchema(BaseModel):
    application_id: int
    approved_amount: Decimal
    next_step: LoanApplicationStep


# =====================================================
# UPDATE SCHEMA (IF NEEDED LATER)
# =====================================================
class LoanApplicationUpdateSchema(BaseModel):
    interest_rate: Optional[Decimal] = None
    monthly_emi: Optional[Decimal] = None
    processing_fee: Optional[Decimal] = None
    gst_amount: Optional[Decimal] = None
    total_repayment: Optional[Decimal] = None
    lender_name: Optional[str] = None
    current_step: Optional[str] = None


# =====================================================
# SUBMIT REQUEST
# =====================================================
class LoanSubmitRequestSchema(BaseModel):
    confirm: bool


# =====================================================
# SUBMIT RESPONSE
# =====================================================
class LoanSubmitResponseSchema(BaseModel):
    reference_number: str
    message: str
    expected_decision_time: str

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# FULL APPLICATION RESPONSE (GET APPLICATION)
# =====================================================
class LoanApplicationResponseSchema(BaseModel):
    application_id: int
    application_status: str
    current_step: str
    approved_amount: Decimal
    requested_tenure_months: int
    interest_rate: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)