
from sqlalchemy import Column, BigInteger, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime


class Disbursement(Base):
    __tablename__ = "disbursements"

    id = Column(BigInteger, primary_key=True)

    loan_id = Column(
        BigInteger,
        nullable=False,
        index=True
    )

    status = Column(String, default="PENDING")

    amount = Column(Float, nullable=True)
    utr_number = Column(String, nullable=True)
    bank_account = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)