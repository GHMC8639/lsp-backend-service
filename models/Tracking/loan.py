from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)

    loan_application_id = Column(
        Integer,
        ForeignKey("loan_application.id"),
        unique=True,
        nullable=False
    )

    principal = Column(Numeric, nullable=False)
    interest_rate = Column(Numeric, nullable=False)
    emi_amount = Column(Numeric, nullable=True)

    status = Column(String, nullable=False)

    disbursed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship(
        "LoanApplication",
        back_populates="loans"
    )