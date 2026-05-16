from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime

from models.Repayment.emi_scheduled import EMISchedule
from models.Repayment.lender_payment_details import LenderPaymentDetails
from models.Loan_application.loan_application import LoanApplication
from models.Repayment.payments import Payment_Transaction

from services.payment.razorpay_service import RazorpayService


# =====================================================
# COMMON: FETCH ACTIVE LOAN + EMI
# =====================================================
def _get_active_loan_and_emi(db: Session, user_id: int):

    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == user_id,
        LoanApplication.application_status == "ACTIVE"
    ).first()

    if not loan:
        raise HTTPException(404, "No ACTIVE loan found")

    emi = db.query(EMISchedule).filter(
        EMISchedule.application_id == loan.id,
        EMISchedule.status == "DUE"
    ).order_by(EMISchedule.emi_number).first()

    return loan, emi


# =====================================================
# STEP 1: EMI SUMMARY
# =====================================================
def get_payment_summary(db: Session, user_id: int):

    loan, _ = _get_active_loan_and_emi(db, user_id)

    emis = db.query(EMISchedule).filter(
        EMISchedule.application_id == loan.id,
        EMISchedule.status != "PAID"
    ).all()

    return {
        "total_due": sum(e.emi_amount for e in emis),
        "emis": [
            {
                "emi_number": e.emi_number,
                "amount": e.emi_amount,
                "due_date": e.due_date
            }
            for e in emis
        ]
    }


# =====================================================
# STEP 2: INITIATE PAYMENT (REGULAR + PREPAY)
# =====================================================
def initiate_payment(
    db: Session,
    user_id: int,
    payment_mode: str,
    payment_option: str = "REGULAR"
):

    loan, emi = _get_active_loan_and_emi(db, user_id)

    rzp = RazorpayService()

    # =====================================================
    # PREPAY FLOW
    # =====================================================
    if payment_option == "PREPAY":

        emis = db.query(EMISchedule).filter(
            EMISchedule.application_id == loan.id,
            EMISchedule.status != "PAID"
        ).order_by(EMISchedule.emi_number).all()

        if not emis:
            raise HTTPException(400, "No EMIs to prepay")

        amount = sum(float(e.emi_amount) for e in emis)
        emi_number = "PREPAY"

    # =====================================================
    # REGULAR EMI FLOW
    # =====================================================
    else:

        if not emi:
            raise HTTPException(404, "No pending EMI")

        amount = float(emi.emi_amount)
        emi_number = str(emi.emi_number)

    # 🔒 Prevent duplicate INITIATED
    existing = db.query(Payment_Transaction).filter(
        Payment_Transaction.application_id == loan.id,
        Payment_Transaction.emi_number == emi_number,
        Payment_Transaction.status.in_(["INITIATED", "RETRY"])
    ).first()

    if existing:
        return {
            "message": "Payment already initiated",
            "order_id": existing.order_id
        }

    # =====================================================
    # UPI QR
    # =====================================================
    if payment_mode == "UPI":
        qr = rzp.create_upi_qr(amount)
        return {
            "mode": "UPI",
            "amount": amount,
            "qr": qr
        }

    # =====================================================
    # CARD / NETBANKING
    # =====================================================
    elif payment_mode in ["CARD", "NETBANKING"]:

        order = rzp.create_order(amount)

        txn = Payment_Transaction(
            application_id=loan.id,
            emi_number=emi_number,
            amount_paid=Decimal("0"),
            payment_mode=payment_mode,
            payment_option=payment_option,
            order_id=order["id"],
            status="INITIATED",
            retry_count=0,
            created_at=datetime.utcnow()
        )

        db.add(txn)
        db.commit()

        return {
            "mode": payment_mode,
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key": "RAZORPAY_KEY_ID"
        }

    # =====================================================
    # BANK TRANSFER
    # =====================================================
    elif payment_mode == "BANK_TRANSFER":

        payment = db.query(LenderPaymentDetails).filter(
            LenderPaymentDetails.lender_id == loan.lender_id
        ).first()

        if not payment:
            raise HTTPException(404, "Bank details not configured")

        return {
            "mode": "BANK_TRANSFER",
            "account_number": payment.account_number,
            "ifsc": payment.ifsc,
            "bank_name": payment.bank_name,
            "amount": amount
        }

    else:
        raise HTTPException(400, "Invalid payment mode")


# =====================================================
# 🔥 RETRY PAYMENT
# =====================================================
def retry_payment(db: Session, user_id: int):

    loan, emi = _get_active_loan_and_emi(db, user_id)

    txn = db.query(Payment_Transaction).filter(
        Payment_Transaction.application_id == loan.id,
        Payment_Transaction.status == "FAILED"
    ).order_by(Payment_Transaction.created_at.desc()).first()

    if not txn:
        raise HTTPException(404, "No failed payment found")

    if txn.retry_count >= 3:
        raise HTTPException(400, "Retry limit exceeded")

    rzp = RazorpayService()
    order = rzp.create_order(float(txn.amount_paid or 0))

    txn.order_id = order["id"]
    txn.status = "RETRY"
    txn.retry_count += 1

    db.commit()

    return {
        "message": "Retry initiated",
        "order_id": order["id"]
    }


# =====================================================
# 🔥 WEBHOOK HANDLER (FINAL)
# =====================================================
def process_webhook_event(db: Session, payload: dict):

    event = payload.get("event")

    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

    payment_id = entity.get("id")
    order_id = entity.get("order_id")
    amount = (entity.get("amount") or 0) / 100

    # =====================================================
    # SUCCESS
    # =====================================================
    if event == "payment.captured":

        existing = db.query(Payment_Transaction).filter(
            Payment_Transaction.transaction_id == payment_id
        ).first()

        if existing:
            return {"message": "Already processed"}

        txn = db.query(Payment_Transaction).filter(
            Payment_Transaction.order_id == order_id
        ).first()

        if not txn:
            return {"message": "Order not found"}

        txn.transaction_id = payment_id
        txn.amount_paid = amount
        txn.status = "SUCCESS"

        # =====================================================
        # PREPAY FLOW
        # =====================================================
        if txn.payment_option == "PREPAY":

            emis = db.query(EMISchedule).filter(
                EMISchedule.application_id == txn.application_id,
                EMISchedule.status != "PAID"
            ).all()

            for e in emis:
                e.status = "PAID"
                e.paid_date = datetime.utcnow()

        # =====================================================
        # REGULAR EMI
        # =====================================================
        else:

            emi = db.query(EMISchedule).filter(
                EMISchedule.application_id == txn.application_id,
                EMISchedule.emi_number == txn.emi_number
            ).first()

            if emi and emi.status != "PAID":
                emi.status = "PAID"

        db.commit()

        return {"message": "Payment success processed"}

    # =====================================================
    # FAILURE
    # =====================================================
    elif event == "payment.failed":

        txn = db.query(Payment_Transaction).filter(
            Payment_Transaction.order_id == order_id
        ).first()

        if txn:
            txn.status = "FAILED"
            txn.retry_count += 1
            db.commit()

        return {"message": "Payment failure recorded"}

    return {"message": "Event ignored"}