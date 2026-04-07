from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
 
class IncomeTypeEnum(str, Enum):
    SALARY_SLIP    = "SALARY_SLIP"
    BANK_STATEMENT = "BANK_STATEMENT"

class DocumentStatusEnum(str, Enum):
    UPLOADED     = "UPLOADED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED     = "APPROVED"
    REJECTED     = "REJECTED"
 
class SingleDocumentResult(BaseModel):
    document_type: str
    file_name:     str
    file_size:     int
    status:        str
    uploaded_at:   str
    message:       str
 
class BulkDocumentUploadResponse(BaseModel):
    user_id:               int
    email:                 str
    uploaded_documents:    List[SingleDocumentResult]
    total_uploaded:        int
    skipped_documents:     List[str]
    missing_documents:     List[str]
    all_required_uploaded: bool
    message:               str
 
class DocumentListItem(BaseModel):
    id:                    int
    document_type:         str
    file_name:             str
    file_size:             int
    status:                str
    uploaded_at:           str
    reviewed_at:           Optional[str]   = None
    admin_remarks:         Optional[str]   = None
 
 
class AllDocumentsResponse(BaseModel):
    user_id:            int
    email:              str
    documents:          List[DocumentListItem]
    total_documents:    int
    required_documents: List[str]
    missing_documents:  List[str]
    all_approved:       bool
 
class DocumentApprovalRequest(BaseModel):
    document_id:   int
    status:        DocumentStatusEnum
    admin_remarks: Optional[str] = None
 
class DocumentApprovalResponse(BaseModel):
    message:         str
    document_id:     int
    new_status:      str
    user_email:      str
    user_kyc_status: str

class PendingDocumentItem(BaseModel):
    id:            int
    user_id:       int
    email:         str
    full_name:     str
    document_type: str
    file_name:     str
    file_path:     str
    file_size:     int
    uploaded_at:   str
    status:        str


class PendingDocumentsResponse(BaseModel):
    pending_documents: List[PendingDocumentItem]
    total_pending:     int


class DocumentReviewRequest(BaseModel):
    document_id:   int
    action:        str              # "APPROVE" or "REJECT"
    admin_remarks: Optional[str] = None

class DocumentReviewResponse(BaseModel):
    document_id:   int
    document_type: str
    user_email:    str
    status:        str
    message:       str
    kyc_completed: bool = False

 
class UserKYCDetails(BaseModel):
    user_id:             int
    email:               str
    full_name:           str
    pan_number:          str
    aadhaar_number:      str
    pan_status:          str
    aadhaar_status:      str
    bank_status:         str
    document_status:     str
    kyc_status:          str
    created_at:          str
    pan_verified_at:     Optional[str]
    aadhaar_verified_at: Optional[str]
    bank_verified_at:    Optional[str]
 