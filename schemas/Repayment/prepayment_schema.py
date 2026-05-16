from pydantic import BaseModel, model_validator, Field
from enum import Enum
from typing import Optional, List, Union
from datetime import date
from decimal import Decimal


# ======================================================
# PAYMENT MODE ENUM
# ======================================================
class PaymentModeEnum(str, Enum):
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"
    CREDIT_CARD = "CREDIT_CARD"


# ======================================================
# REQUEST SCHEMA
# ======================================================
class PrepaymentRequest(BaseModel):
    emi_count: int = Field(..., gt=0, description="Number of EMIs to prepay")
    payment_mode: PaymentModeEnum


# ======================================================
# LENDER DETAILS
# ======================================================
class LenderUPIDetails(BaseModel):
    lender_upi: str
    lender_account_holder_name: str


class LenderBankTransferDetails(BaseModel):
    lender_account_holder_name: str
    lender_account_number: str
    ifsc: str
    lender_bank_name: str


class LenderCreditCardDetails(BaseModel):
    lender_account_holder_name: str
    lender_card_number: str
    lender_card_type: str
    lender_expiry: str


# ======================================================
# EMI ITEM
# ======================================================
class PrepayEMIItem(BaseModel):
    emi_number: int
    due_date: date
    emi_amount: Decimal
    principal_component: Decimal
    interest_component: Decimal
    gst_amount: Decimal


# ======================================================
# RESPONSE SCHEMA
# ======================================================
class PrepayResponse(BaseModel):
    application_id: int
    total_emis_selected: int = Field(..., gt=0)

    emis: List[PrepayEMIItem]

    total_emi_amount: Decimal
    total_principal: Decimal
    total_interest: Decimal
    total_gst: Decimal

    prepay_penalty: Decimal
    penalty_gst: Decimal
    total_payable: Decimal

    payment_mode: PaymentModeEnum

    lender_details: Union[
        LenderUPIDetails,
        LenderBankTransferDetails,
        LenderCreditCardDetails
    ]

    currency: str = "INR"
    transaction_id: Optional[str] = None

    # ======================================================
    # VALIDATION
    # ======================================================
    @model_validator(mode="after")
    def validate_lender_details(self):

        if self.payment_mode == PaymentModeEnum.UPI:
            if not isinstance(self.lender_details, LenderUPIDetails):
                raise ValueError("UPI requires LenderUPIDetails")

        elif self.payment_mode == PaymentModeEnum.BANK_TRANSFER:
            if not isinstance(self.lender_details, LenderBankTransferDetails):
                raise ValueError("Bank Transfer requires LenderBankTransferDetails")

        elif self.payment_mode == PaymentModeEnum.CREDIT_CARD:
            if not isinstance(self.lender_details, LenderCreditCardDetails):
                raise ValueError("Credit Card requires LenderCreditCardDetails")

        return self

    class Config:
        from_attributes = True

        # 🔥 IMPORTANT FIX (Decimal → JSON)
        json_encoders = {
            Decimal: lambda v: float(v)
        }