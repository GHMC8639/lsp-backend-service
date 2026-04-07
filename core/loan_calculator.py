from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta
from datetime import date


# ==============================
# CONFIG
# ==============================

MIN_LOAN_AMOUNT = Decimal("5000")
MAX_LOAN_AMOUNT = Decimal("20000")

ALLOWED_TENURES = [3, 6, 9, 12]

ANNUAL_INTEREST_RATE = Decimal("12")   # %
PROCESSING_FEE_PERCENT = Decimal("5")  # %
GST_RATE = Decimal("18")               # %


# ==============================
# VALIDATION
# ==============================

def validate_loan_request(principal, tenure_months) -> Decimal:
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
        raise ValueError(f"Tenure must be one of {ALLOWED_TENURES}")

    return principal


# ==============================
# EMI CALCULATION
# ==============================

def calculate_emi(principal: Decimal, annual_rate: Decimal, tenure: int) -> Decimal:
    monthly_rate = annual_rate / Decimal("100") / Decimal("12")

    if monthly_rate == 0:
        return (principal / tenure).quantize(Decimal("0.01"))

    r = monthly_rate
    n = tenure

    factor = (Decimal("1") + r) ** n

    emi = (principal * r * factor) / (factor - Decimal("1"))

    return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ==============================
# PROCESSING FEE + GST
# ==============================

def calculate_processing_fee(principal: Decimal) -> dict:
    processing_fee = (
        principal * PROCESSING_FEE_PERCENT / Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    gst_on_fee = (
        processing_fee * GST_RATE / Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    total_charges = (processing_fee + gst_on_fee).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return {
        "processing_fee": processing_fee,
        "gst_on_processing_fee": gst_on_fee,
        "total_processing_charges": total_charges
    }


# ==============================
# AMORTIZATION SCHEDULE
# ==============================

def generate_schedule(
    principal: Decimal,
    annual_rate: Decimal,
    tenure: int,
    first_emi_date: date
):
    emi_fixed = calculate_emi(principal, annual_rate, tenure)

    monthly_rate = annual_rate / Decimal("100") / Decimal("12")

    remaining = principal
    schedule = []

    for emi_number in range(1, tenure + 1):

        opening = remaining

        interest = (opening * monthly_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        principal_component = (emi_fixed - interest).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # LAST EMI ADJUSTMENT
        if emi_number == tenure:
            principal_component = opening
            interest = (opening * monthly_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        emi_to_use = (principal_component + interest).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        closing = (opening - principal_component).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        closing = max(closing, Decimal("0.00"))

        gst_on_interest = (interest * GST_RATE / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        due_date = first_emi_date + relativedelta(months=emi_number - 1)

        # Safe date handling (avoid Feb issues)
        due_date = due_date.replace(day=min(first_emi_date.day, 28))

        schedule.append({
            "emi_number": emi_number,
            "due_date": due_date,
            "opening_principal": opening,
            "principal_component": principal_component,
            "interest_component": interest,
            "gst_on_interest": gst_on_interest,
            "emi_amount": emi_to_use,
            "closing_principal": closing
        })

        remaining = closing

    return schedule


# ==============================
# LOAN SUMMARY (MAIN FUNCTION)
# ==============================

def calculate_loan_summary(
    principal,
    tenure_months,
    first_emi_date: date
) -> dict:

    principal = validate_loan_request(principal, tenure_months)

    emi = calculate_emi(principal, ANNUAL_INTEREST_RATE, tenure_months)

    schedule = generate_schedule(
        principal,
        ANNUAL_INTEREST_RATE,
        tenure_months,
        first_emi_date
    )

    charges = calculate_processing_fee(principal)

    total_repayment = (emi * tenure_months).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    total_interest = total_repayment - principal

    total_gst = sum(row["gst_on_interest"] for row in schedule)

    net_disbursement_amount = (
        principal - charges["total_processing_charges"]
    ).quantize(Decimal("0.01"))

    apr = (
        (total_interest / principal) *
        (Decimal("12") / Decimal(tenure_months)) *
        Decimal("100")
    ).quantize(Decimal("0.01"))

    return {
        "loan_summary": {
            "approved_amount": str(principal),
            "tenure_months": tenure_months,
            "interest_rate": str(ANNUAL_INTEREST_RATE),
            "emi": str(emi),
            "total_repayment": str(total_repayment),
            "total_interest": str(total_interest),
            "apr": str(apr)
        },
        "charges": {
            "processing_fee": str(charges["processing_fee"]),
            "gst_on_processing_fee": str(charges["gst_on_processing_fee"]),
            "total_processing_charges": str(charges["total_processing_charges"])
        },
        "disbursement": {
            "approved_amount": str(principal),
            "net_disbursement_amount": str(net_disbursement_amount)
        },
        "totals": {
            "total_gst_on_interest": str(total_gst)
        },
        "amortization_schedule": schedule
    }