from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class EsignAuditLog(Base):
    __tablename__ = "esign_audit_logs"

    id = Column(BigInteger, primary_key=True, index=True)

    session_id = Column(
        BigInteger,
        ForeignKey("esign_sessions.id"),
        nullable=False,
        index=True
    )

    event_type = Column(String, nullable=False, index=True)
    event_description = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("EsignSession", back_populates="audit_logs")