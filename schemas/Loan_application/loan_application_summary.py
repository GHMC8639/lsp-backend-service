from pydantic import BaseModel, Field
from typing import Optional, List
from  core.enums import LoanApplicationStep
from  services.Loan_application.loan_calculator import MIN_LOAN_AMOUNT, MAX_LOAN_AMOUNT

class UserSummarySchema(BaseModel):
    user_id: Optional[int] = None
    full_name: str
    mobile_number: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class EligibilitySummarySchema(BaseModel):
    eligible: bool
    max_loan_amount: float
    approved_interest_rate: float
    risk_category: Optional[str] = None

    class Config:
        from_attributes = True


class LoanDetailsSummarySchema(BaseModel):

    # Loan Basics
    approved_amount: float
    requested_tenure_months: int
    interest_rate: Optional[float] = None

    #  EMI
    emi_amount: Optional[float] = None
    total_repayment: Optional[float] = None

    # Processing Charges
    processing_fee: Optional[float] = None
    gst_on_processing_fee: Optional[float] = None
    total_processing_charges: Optional[float] = None

    #  Lender Details
    lender_name: Optional[str] = None

    class Config:
        from_attributes = True


class LoanPurposeSummarySchema(BaseModel):
    purpose: str

    class Config:
        from_attributes = True


class ReferenceSummarySchema(BaseModel):
    name: str
    relationship: str
    mobile_number: str
    is_mobile_verified: bool

    class Config:
        from_attributes = True


class ReferencesStatusSchema(BaseModel):
    total_required: int = 2
    total_added: int
    verified_count: int
    remaining_to_verify: int

    class Config:
        from_attributes = True


class DeclarationSummarySchema(BaseModel):
    has_existing_loans: bool
    has_credit_card: bool
    has_default_history: bool
    declaration_accepted: bool

    class Config:
        from_attributes = True


class SubmissionStatusSchema(BaseModel):
    last_completed_step: Optional[LoanApplicationStep] = None
    can_submit: bool
    pending_steps: List[str]

    class Config:
        from_attributes = True


class LoanApplicationSummaryResponseSchema(BaseModel):
    application_id: int
    user: UserSummarySchema
    eligibility: Optional[EligibilitySummarySchema] = None
    loan_details: LoanDetailsSummarySchema
    purpose: LoanPurposeSummarySchema
    references: List[ReferenceSummarySchema]
    reference_status: ReferencesStatusSchema
    declaration: DeclarationSummarySchema
    submission_status: SubmissionStatusSchema

    class Config:
        from_attributes = True


class EditLoanDetailsSchema(BaseModel):
    approved_amount: Optional[float] = Field(
        None,
        ge=MIN_LOAN_AMOUNT,   # ← from loan_calculator.py
        le=MAX_LOAN_AMOUNT,   # ← from loan_calculator.py
        description=f"Loan amount between ₹{MIN_LOAN_AMOUNT} and ₹{MAX_LOAN_AMOUNT}"
    )
    requested_tenure_months: Optional[int] = Field(
        None,
        description="Tenure: 3, 6, 9, or 12 months"
    )

    class Config:
        from_attributes = True


class EditLoanPurposeSchema(BaseModel):
    purpose_code: str = Field(
        ...,
        description="Updated loan purpose code")
    purpose_description: Optional[str] = Field(
        None,
        description="Optional description for the purpose")

    class Config:
        from_attributes = True


class EditSingleReferenceSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    mobile_number: str = Field(..., min_length=10, max_length=10)
    relation_type: str = Field(...)
    is_emergency_contact: Optional[bool] = False

    class Config:
        from_attributes = True


class EditReferenceSchema(BaseModel):
    references: List[EditSingleReferenceSchema] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Exactly 2 references required")

    class Config:
        from_attributes = True


class EditDeclarationSchema(BaseModel):
    agreed_terms: bool
    consent_credit_check: bool
    consent_data_sharing: bool
    has_existing_loans: bool
    has_credit_card: bool
    has_default_history: bool
    terms_version: str
    privacy_policy_version: str

    class Config:
        from_attributes = True


class EditFieldResponseSchema(BaseModel):
    success: bool
    message: str
    updated_fields: List[str]
    application_id: int
    step_reset_to: Optional[str] = None

    class Config:
        from_attributes = True