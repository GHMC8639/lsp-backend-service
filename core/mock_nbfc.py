import uuid
import random
from typing import Dict


class MockNBFCPaymentGateway:
    """
    Mock NBFC Payment Gateway
    Simulates Bank & UPI disbursement responses.
    """

    SUCCESS_RATE = 0.75  # 75% success probability

    @staticmethod
    def _generate_response() -> Dict:

        is_success = random.random() < MockNBFCPaymentGateway.SUCCESS_RATE

        if not is_success:
            return {
                "success": False,
                "reference_id": None,
                "message": "Mock transfer failed due to bank rejection"
            }

        return {
            "success": True,
            "reference_id": f"MOCKNBFC-{uuid.uuid4().hex[:10].upper()}",
            "message": "Transfer successful"
        }

    @staticmethod
    def transfer_bank(
        account_number: str,
        ifsc_code: str,
        account_holder_name: str,
        amount: float
    ) -> Dict:
        """
        Simulates bank account disbursement (NEFT/IMPS/RTGS).
        """

        if not account_number or not ifsc_code:
            return {
                "success": False,
                "reference_id": None,
                "message": "Invalid bank details"
            }

        if amount <= 0:
            return {
                "success": False,
                "reference_id": None,
                "message": "Invalid transfer amount"
            }

        return MockNBFCPaymentGateway._generate_response()

    @staticmethod
    def transfer_upi(
        upi_id: str,
        amount: float
    ) -> Dict:
        """
        Simulates UPI payout.
        """

        if not upi_id or "@" not in upi_id:
            return {
                "success": False,
                "reference_id": None,
                "message": "Invalid UPI ID"
            }

        if amount <= 0:
            return {
                "success": False,
                "reference_id": None,
                "message": "Invalid transfer amount"
            }

        return MockNBFCPaymentGateway._generate_response()