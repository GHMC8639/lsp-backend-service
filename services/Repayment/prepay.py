from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.Repayment.emi_scheduled import EMISchedule
from models.Loan_application.loan_application import LoanApplication
from models.Auth.lender import Lender
from models.Repayment.lender_payment_details import LenderPaymentDetails

from schemas.Repayment.prepayment_schema import (
    PaymentModeEnum,
    PrepayResponse,
    PrepayEMIItem,
    LenderUPIDetails,
    LenderBankTransferDetails,
    LenderCreditCardDetails
)


OVERDUE_PENALTY_RATE = Decimal("0.02")
GST_RATE = Decimal("0.18")


# =====================================================
# SAFE DECIMAL
# =====================================================
def safe_decimal(value):
    return Decimal(str(value or 0))


# =====================================================
# 🔥 PREPAY CALCULATION ONLY
# =====================================================
def process_prepay(
    db: Session,
    user_id: int,
    emi_count: int,
    payment_mode: PaymentModeEnum,
):
    """
    Calculates prepayment details.
    DOES NOT update DB.
    Execution is handled by webhook in manual_payment.
    """

    if emi_count <= 0:
        raise HTTPException(400, "emi_count must be greater than 0")

    # 🔐 GET ACTIVE LOAN
    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == user_id,
        LoanApplication.application_status == "ACTIVE"
    ).first()

    if not loan:
        raise HTTPException(404, "No ACTIVE loan found")

    application_id = loan.id

    # 📊 GET EMIs
    emis = db.query(EMISchedule).filter(
        EMISchedule.application_id == application_id,
        EMISchedule.status != "PAID"
    ).order_by(EMISchedule.due_date).limit(emi_count).all()

    if not emis:
        raise HTTPException(404, "No pending EMIs found")

    # 💰 CALCULATIONS
    total_emi = sum(safe_decimal(e.emi_amount) for e in emis)
    total_principal = sum(safe_decimal(e.principal_component) for e in emis)
    total_interest = sum(safe_decimal(e.interest_component) for e in emis)
    total_gst = sum(safe_decimal(e.gst_amount) for e in emis)

    prepay_penalty = (total_principal * OVERDUE_PENALTY_RATE).quantize(Decimal("0.01"))
    penalty_gst = (prepay_penalty * GST_RATE).quantize(Decimal("0.01"))

    total_payable = (total_emi + prepay_penalty + penalty_gst).quantize(Decimal("0.01"))

    # 📦 EMI ITEMS
    emi_items = [
        PrepayEMIItem(
            emi_number=e.emi_number,
            due_date=e.due_date,
            emi_amount=e.emi_amount,
            principal_component=e.principal_component,
            interest_component=e.interest_component,
            gst_amount=e.gst_amount or 0
        )
        for e in emis
    ]

    # =====================================================
    # 🔍 GET LENDER
    # =====================================================
    lender = db.query(Lender).filter(
        Lender.id == getattr(loan, "lender_id", None)
    ).first()

    if not lender:
        raise HTTPException(404, "Lender not found")

    # =====================================================
    # 🔍 GET PAYMENT DETAILS
    # =====================================================
    payment = db.query(LenderPaymentDetails).filter(
        LenderPaymentDetails.lender_id == lender.id
    ).first()

    if not payment:
        raise HTTPException(404, "Lender payment details not configured")

    # =====================================================
    # 💳 PAYMENT MODE HANDLING
    # =====================================================
    if payment_mode == PaymentModeEnum.UPI:
        lender_details = LenderUPIDetails(
            lender_upi=payment.upi_id or "N/A",
            lender_account_holder_name=lender.company_name or "N/A"
        )

    elif payment_mode == PaymentModeEnum.BANK_TRANSFER:
        lender_details = LenderBankTransferDetails(
            lender_account_holder_name=lender.company_name or "N/A",
            lender_account_number=payment.account_number or "N/A",
            ifsc=payment.ifsc or "N/A",
            lender_bank_name=payment.bank_name or "N/A"
        )

    elif payment_mode == PaymentModeEnum.CREDIT_CARD:
        card_number = payment.card_number or "0000000000000000"

        lender_details = LenderCreditCardDetails(
            lender_account_holder_name=lender.company_name or "N/A",
            lender_card_number=f"**** **** **** {card_number[-4:]}",
            lender_card_type=payment.card_type or "N/A",
            lender_expiry=payment.expiry or "N/A"
        )

    else:
        raise HTTPException(400, "Invalid payment mode")

    # =====================================================
    # 📦 FINAL RESPONSE
    # =====================================================
    return PrepayResponse(
        application_id=application_id,
        total_emis_selected=len(emis),
        emis=emi_items,
        total_emi_amount=total_emi,
        total_principal=total_principal,
        total_interest=total_interest,
        total_gst=total_gst,
        prepay_penalty=prepay_penalty,
        penalty_gst=penalty_gst,
        total_payable=total_payable,
        payment_mode=payment_mode,
        lender_details=lender_details
    )