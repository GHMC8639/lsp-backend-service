from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional

from core.enums import (
    PaymentModeEnum,
    DisbursementStatusEnum)


class DisbursementRequestSchema(BaseModel):
    payment_mode: PaymentModeEnum = Field(
        ...,
        description="Select payout method (BANK or UPI)")


class DisbursementResponseSchema(BaseModel):

    id: int = Field(
        ...,
        description="Disbursement record ID")

    application_id: int = Field(
        ...,
        description="Loan application ID")

    amount: Decimal = Field(
        ...,
        description="Net amount disbursed to user")

    payment_mode: PaymentModeEnum = Field(
        ...,
        description="Selected payout method")

    payment_status: DisbursementStatusEnum = Field(
        ...,
        description="Current status of disbursement")

    payment_reference_id: Optional[str] = Field(
        None,
        description="Reference ID returned by payment gateway (if successful)")

    initiated_at: Optional[datetime] = Field(
        None,
        description="Time when disbursement was initiated")

    completed_at: Optional[datetime] = Field(
        None,
        description="Time when disbursement was completed")

    retry_allowed: Optional[bool] = Field(
        None,
        description="Indicates whether retry is allowed (true if FAILED)")

    class Config:
        from_attributes = True