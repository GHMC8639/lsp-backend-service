from sqlalchemy import Column, BigInteger, String, DateTime, JSON, Enum as SqlEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from core.database import Base


class EsignStatus(str, Enum):
    OTP_SENT = "OTP_SENT"
    SIGNED = "SIGNED"
    FAILED = "FAILED"
    CALLBACK_RECEIVED = "CALLBACK_RECEIVED"


class EsignSession(Base):
    __tablename__ = "esign_sessions"

    id = Column(BigInteger, primary_key=True, index=True)

    loan_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)

    transaction_id = Column(String, unique=True, nullable=False, index=True)

    request_payload = Column(JSON, nullable=False)
    response_payload = Column(JSON, nullable=True)
    callback_payload = Column(JSON, nullable=True)

    status = Column(SqlEnum(EsignStatus), default=EsignStatus.OTP_SENT, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    signed_document = relationship(
        "SignedDocument",
        back_populates="session",
        uselist=False
    )

    audit_logs = relationship(
        "EsignAuditLog",
        back_populates="session",
        cascade="all, delete-orphan"
    )