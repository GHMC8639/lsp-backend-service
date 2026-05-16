from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from decimal import Decimal

from models.Repayment.emi_scheduled import EMISchedule
from models.Repayment.payments import Payment_Transaction
from models.Repayment.foreclosure import ForeclosureRequest
from models.Loan_application.loan_application import LoanApplication

from services.payment.razorpay_service import RazorpayService
from utils.status import close_loan


# =====================================================
# 🔐 GET ACTIVE LOAN
# =====================================================
def _get_active_loan(db: Session, user_id: int):

    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == user_id,
        LoanApplication.application_status == "ACTIVE"
    ).first()

    if not loan:
        raise HTTPException(status_code=404, detail="No ACTIVE loan found")

    return loan


# =====================================================
# 📊 STEP 1: CREATE FORECLOSURE REQUEST
# =====================================================
def create_foreclosure_request(db: Session, user_id: int):
    """
    Creates foreclosure request and stores snapshot of amount
    """

    loan = _get_active_loan(db, user_id)

    # Get all unpaid EMIs
    emis = db.query(EMISchedule).filter(
        EMISchedule.application_id == loan.id,
        EMISchedule.status != "PAID"
    ).all()

    if not emis:
        raise HTTPException(status_code=400, detail="Nothing to foreclose")

    # Calculate amounts
    outstanding = sum(float(e.emi_amount) for e in emis)
    charge = outstanding * 0.02
    gst = charge * 0.18
    total_amount = outstanding + charge + gst

    # Prevent duplicate pending request
    existing = db.query(ForeclosureRequest).filter(
        ForeclosureRequest.application_id == loan.id,
        ForeclosureRequest.status == "PENDING"
    ).first()

    if existing:
        return {
            "message": "Foreclosure already requested",
            "foreclosure_id": existing.id,
            "amount": float(existing.total_amount)
        }

    # Create foreclosure record
    foreclosure = ForeclosureRequest(
        application_id=loan.id,
        outstanding=outstanding,
        charge=charge,
        gst=gst,
        total_amount=total_amount,
        status="PENDING"
    )

    db.add(foreclosure)
    db.commit()
    db.refresh(foreclosure)

    return {
        "message": "Foreclosure request created",
        "foreclosure_id": foreclosure.id,
        "application_id": loan.id,
        "total_amount": float(total_amount)
    }


# =====================================================
# 💳 STEP 2: INITIATE PAYMENT
# =====================================================
def initiate_foreclosure_payment(db: Session, foreclosure_id: int):
    """
    Creates Razorpay order and Payment_Transaction
    """

    foreclosure = db.query(ForeclosureRequest).filter(
        ForeclosureRequest.id == foreclosure_id
    ).first()

    if not foreclosure:
        raise HTTPException(status_code=404, detail="Foreclosure request not found")

    if foreclosure.status != "PENDING":
        raise HTTPException(status_code=400, detail="Invalid foreclosure status")

    rzp = RazorpayService()

    # Create Razorpay order
    order = rzp.create_order(
        float(foreclosure.total_amount),
        receipt=f"foreclosure_{foreclosure.id}"
    )

    # Save order_id
    foreclosure.order_id = order["id"]

    # Prevent duplicate INITIATED txn
    existing_txn = db.query(Payment_Transaction).filter(
        Payment_Transaction.order_id == order["id"]
    ).first()

    if existing_txn:
        return {
            "message": "Payment already initiated",
            "order_id": existing_txn.order_id
        }

    txn = Payment_Transaction(
        application_id=foreclosure.application_id,
        emi_number="FORECLOSURE",
        amount_paid=Decimal("0"),
        payment_mode="ONLINE",
        payment_option="FORECLOSURE",
        order_id=order["id"],
        status="INITIATED",
        retry_count=0,
        created_at=datetime.utcnow()
    )

    db.add(txn)
    db.commit()

    return {
        "message": "Foreclosure payment initiated",
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "key": "RAZORPAY_KEY_ID"
    }


# =====================================================
# 🔥 STEP 3: WEBHOOK HANDLER
# =====================================================
def process_foreclosure_webhook(
    db: Session,
    body: bytes,
    signature: str,
    payload: dict
):
    """
    Handles Razorpay webhook for foreclosure
    """

    rzp = RazorpayService()

    # 🔐 Verify webhook signature
    try:
        rzp.verify_webhook(body, signature)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid webhook: {str(e)}")

    event = payload.get("event")
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

    payment_id = entity.get("id")
    order_id = entity.get("order_id")
    amount = (entity.get("amount") or 0) / 100

    # =====================================================
    # ✅ PAYMENT SUCCESS
    # =====================================================
    if event == "payment.captured":

        # Idempotency check
        existing_txn = db.query(Payment_Transaction).filter(
            Payment_Transaction.transaction_id == payment_id
        ).first()

        if existing_txn:
            return {"message": "Already processed"}

        txn = db.query(Payment_Transaction).filter(
            Payment_Transaction.order_id == order_id,
            Payment_Transaction.payment_option == "FORECLOSURE"
        ).first()

        if not txn:
            return {"message": "Transaction not found"}

        foreclosure = db.query(ForeclosureRequest).filter(
            ForeclosureRequest.order_id == order_id
        ).first()

        if not foreclosure:
            return {"message": "Foreclosure not found"}

        # 🔐 Verify payment status via Razorpay API
        try:
            rzp.verify_payment(payment_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Update transaction
        txn.transaction_id = payment_id
        txn.amount_paid = amount
        txn.status = "SUCCESS"

        # Update foreclosure
        foreclosure.status = "SUCCESS"
        foreclosure.payment_id = payment_id

        # =====================================================
        # 🔄 MARK ALL EMIs AS PAID
        # =====================================================
        emis = db.query(EMISchedule).filter(
            EMISchedule.application_id == foreclosure.application_id,
            EMISchedule.status != "PAID"
        ).all()

        now = datetime.utcnow()

        for emi in emis:
            emi.status = "PAID"
            emi.paid_date = now

        # =====================================================
        # 🔐 CLOSE LOAN
        # =====================================================
        loan = db.query(LoanApplication).filter(
            LoanApplication.id == foreclosure.application_id
        ).first()

        if loan:
            close_loan(loan.id, loan.user_profile_id)

        db.commit()

        return {
            "message": "Foreclosure successful",
            "loan_status": "CLOSED",
            "payment_id": payment_id
        }

    # =====================================================
    # ❌ PAYMENT FAILED
    # =====================================================
    elif event == "payment.failed":

        foreclosure = db.query(ForeclosureRequest).filter(
            ForeclosureRequest.order_id == order_id
        ).first()

        if foreclosure:
            foreclosure.status = "FAILED"

        txn = db.query(Payment_Transaction).filter(
            Payment_Transaction.order_id == order_id,
            Payment_Transaction.payment_option == "FORECLOSURE"
        ).first()

        if txn:
            txn.status = "FAILED"
            txn.retry_count += 1

        db.commit()

        return {"message": "Foreclosure payment failed"}

    return {"message": "Event ignored"}