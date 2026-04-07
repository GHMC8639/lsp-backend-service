from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(Integer, ForeignKey("loan_application.id"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user_profiles.user_id"), nullable=False)

    principal = Column(Numeric(12, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    tenure_months = Column(Integer, nullable=False)
    emi_amount = Column(Numeric(12, 2), nullable=False)

    status = Column(String, default="ACTIVE")
    disbursed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("LoanApplication", back_populates="loans")