from typing import Optional
from pydantic import BaseModel


class DocumentReuploadRequest(BaseModel):
    document_type: str
    reason: Optional[str] = None
    comments: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentReuploadResponse(BaseModel):
    success: bool
    message: str
    next_status: Optional[str] = None

    class Config:
        from_attributes = True


class FileUploadResult(BaseModel):
    file_name: str
    file_url: str

    class Config:
        from_attributes = True
