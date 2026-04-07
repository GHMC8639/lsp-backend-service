from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from core.database import Base


class DocumentReupload(Base):
    __tablename__ = "document_reupload"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_application.id"), nullable=False)

    document_type = Column(String, nullable=False)
    rejection_reason = Column(String, nullable=True)

    old_document_url = Column(String, nullable=True)
    new_document_url = Column(String, nullable=True)

    status = Column(String, default="PENDING_REVIEW")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())