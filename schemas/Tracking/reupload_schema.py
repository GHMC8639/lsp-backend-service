# app/schemas/reupload_schema.py

from pydantic import BaseModel
from typing import Optional

class DocumentReuploadRequest(BaseModel):
    document_type: str
    new_document_url: str
    rejection_reason: Optional[str] = None


class DocumentReuploadResponse(BaseModel):
    id: int
    application_id: int
    document_type: str
    new_document_url: str
    reason: Optional[str]
    status: str

    class Config:
        from_attributes = True