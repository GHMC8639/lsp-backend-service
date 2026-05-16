import razorpay
import os
import hmac
import hashlib
from decimal import Decimal
from typing import Dict
from datetime import datetime

from core.logger import logger


class RazorpayService:

    def __init__(self):
        key_id = os.getenv("RAZORPAY_KEY_ID")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET")

        if not key_id or not key_secret:
            raise Exception("Razorpay credentials missing")

        self.client = razorpay.Client(auth=(key_id, key_secret))

        self.account_number = os.getenv("RAZORPAYX_ACCOUNT_NUMBER")
        self.webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    # =====================================================
    # 💰 CREATE ORDER
    # =====================================================
    def create_order(self, amount: Decimal, receipt: str = None) -> Dict:
        try:
            logger.info(f"[RAZORPAY] Creating order amount={amount}")

            order = self.client.order.create({
                "amount": int(amount * 100),
                "currency": "INR",
                "receipt": receipt or f"receipt_{datetime.utcnow().timestamp()}",
                "payment_capture": 1
            })

            return order

        except Exception as e:
            logger.error(f"[RAZORPAY ORDER ERROR] {str(e)}")
            raise

    # =====================================================
    # 🔐 VERIFY SIGNATURE
    # =====================================================
    def verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        body = f"{order_id}|{payment_id}"

        generated = hmac.new(
            bytes(os.getenv("RAZORPAY_KEY_SECRET"), "utf-8"),
            bytes(body, "utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(generated, signature):
            raise Exception("Invalid Signature")

        return True

    # =====================================================
    # 🔐 VERIFY WEBHOOK
    # =====================================================
    def verify_webhook(self, body: bytes, signature: str) -> bool:
        generated = hmac.new(
            bytes(self.webhook_secret, "utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(generated, signature):
            raise Exception("Invalid Webhook Signature")

        return True

    # =====================================================
    # 💸 PAYOUT FLOW
    # =====================================================
    def process_payout(
        self,
        name: str,
        account_number: str,
        ifsc: str,
        amount: Decimal,
        application_id: int,
        email: str = None,
        phone: str = None
    ) -> Dict:

        try:
            logger.info(f"[PAYOUT INIT] app={application_id}, amount={amount}")

            contact = self.client.contact.create({
                "name": name,
                "email": email,
                "contact": phone,
                "type": "customer"
            })

            fund_account = self.client.fund_account.create({
                "contact_id": contact["id"],
                "account_type": "bank_account",
                "bank_account": {
                    "name": name,
                    "ifsc": ifsc,
                    "account_number": account_number
                }
            })

            payout = self.client.payout.create({
                "account_number": self.account_number,
                "fund_account_id": fund_account["id"],
                "amount": int(amount * 100),
                "currency": "INR",
                "mode": "IMPS",
                "purpose": "loan_disbursement",
                "queue_if_low_balance": True,
                "reference_id": f"loan_{application_id}_{int(datetime.utcnow().timestamp())}",
                "narration": "Loan Disbursement"
            })

            logger.info(f"[PAYOUT SUCCESS] payout_id={payout.get('id')}")

            return {
                "success": True,
                "payout_id": payout.get("id"),
                "status": payout.get("status"),
                "raw": payout
            }

        except Exception as e:
            logger.error(f"[PAYOUT ERROR] {str(e)}")

            return {
                "success": False,
                "error": str(e)
            }