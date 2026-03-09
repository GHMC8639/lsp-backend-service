from math import pow
from decimal import Decimal, ROUND_HALF_UP


MIN_LOAN_AMOUNT = Decimal("5000")
MAX_LOAN_AMOUNT = Decimal("20000")

ALLOWED_TENURES = [3, 6, 9, 12]

ANNUAL_INTEREST_RATE = Decimal("12")   # 12%
PROCESSING_FEE_PERCENT = Decimal("5")  # 5%
GST_RATE = Decimal("18")               # 18%


def validate_loan_request(principal, tenure_months):

    if principal is None or tenure_months is None:
        raise ValueError("Loan amount and tenure are required")

    try:
        principal = Decimal(str(principal))
    except Exception:
        raise ValueError("Loan amount must be a valid number")

    if principal < MIN_LOAN_AMOUNT or principal > MAX_LOAN_AMOUNT:
        raise ValueError(
            f"Loan amount must be between ₹{MIN_LOAN_AMOUNT} and ₹{MAX_LOAN_AMOUNT}"
        )

    if tenure_months not in ALLOWED_TENURES:
        raise ValueError(
            f"Tenure must be one of {ALLOWED_TENURES} months"
        )

    return principal


def calculate_emi(principal: Decimal, tenure_months: int) -> Decimal:
    """
    EMI = [P × R × (1+R)^N] / [(1+R)^N - 1]
    """

    monthly_rate = (ANNUAL_INTEREST_RATE / Decimal("12")) / Decimal("100")
    r = monthly_rate
    n = tenure_months

    emi = (principal * r * Decimal(pow(1 + r, n))) / (
        Decimal(pow(1 + r, n)) - Decimal("1")
    )

    return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_processing_fee(principal: Decimal) -> dict:
    """
    GST applies ONLY on processing fee.
    """

    processing_fee = (
        principal * PROCESSING_FEE_PERCENT / Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    gst_on_fee = (
        processing_fee * GST_RATE / Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    total_charges = (
        processing_fee + gst_on_fee
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "processing_fee": processing_fee,
        "gst_on_processing_fee": gst_on_fee,
        "total_processing_charges": total_charges
    }


def calculate_loan_summary(principal, tenure_months) -> dict:
    """
    Uses approved_amount as principal.
    Returns summary for:
    - User summary screen
    - Pre-disbursement preview
    - Disbursement service
    """

    principal = validate_loan_request(principal, tenure_months)

    emi = calculate_emi(principal, tenure_months)
    charges = calculate_processing_fee(principal)

    # Total EMI repayment (principal + interest)
    total_repayment = (
        emi * tenure_months
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Net payout after deducting charges
    net_disbursement_amount = (
        principal - charges["total_processing_charges"]
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "approved_amount": float(principal),
        "tenure_months": tenure_months,
        "interest_rate": float(ANNUAL_INTEREST_RATE),
        "emi": float(emi),
        "total_repayment": float(total_repayment),
        "processing_fee": float(charges["processing_fee"]),
        "gst_on_processing_fee": float(charges["gst_on_processing_fee"]),
        "total_processing_charges": float(charges["total_processing_charges"]),
        "net_disbursement_amount": float(net_disbursement_amount)
    }