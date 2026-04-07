from sqlalchemy import Column, Integer, String, ForeignKey, DateTime,Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class Lender(Base):
    __tablename__ = "lenders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)   
    is_verified = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    company_name = Column(String, nullable=False)
    gst_number = Column(String, nullable=True,unique=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
   
    user = relationship("User")

    loan_applications = relationship(
        "LoanApplication",
        back_populates="lender")
