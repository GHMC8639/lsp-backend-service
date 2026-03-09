from enum import Enum, IntEnum
from pydantic import BaseModel


def enum_value(value):
    """
    Safely convert Enum → string for DB / JSON
    """
    if isinstance(value, Enum):
        return value.value
    return value


class LoanPurpose(str, Enum):
    MEDICAL = "MEDICAL"
    EDUCATION = "EDUCATION"
    EMERGENCY = "EMERGENCY"
    PERSONAL = "PERSONAL"


class LoanApplicationStep(str, Enum):
    LOAN_DETAILS = "LOAN_DETAILS"
    PURPOSE = "PURPOSE"
    REFERENCES = "REFERENCES"
    DECLARATION = "DECLARATION"
    SUMMARY = "SUMMARY"
    SUBMITTED = "SUBMITTED"


class LoanApplicationStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NBFC_APPROVED = "NBFC_APPROVED"
    DISBURSED = "DISBURSED"
    CLOSED = "CLOSED"



class EligibilityStatusEnum(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    REJECTED = "REJECTED"


class ReferenceRelation(str, Enum):
    FRIEND = "FRIEND"
    BROTHER = "BROTHER"
    SISTER = "SISTER"
    FATHER = "FATHER"
    MOTHER = "MOTHER"
    SPOUSE = "SPOUSE"
    COLLEAGUE = "COLLEAGUE"
    
class LoanTenureMonths(IntEnum):
    THREE = 3
    SIX = 6
    NINE = 9
    TWELVE = 12

class DisbursementStatusEnum(str, Enum):
    INITIATED = "INITIATED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
    
    
class PaymentModeEnum(str, Enum):
    BANK = "BANK"
    UPI = "UPI"

