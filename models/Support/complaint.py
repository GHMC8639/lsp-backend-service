from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from core.database import Base
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import relationship


class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    complaint_number = Column(String, unique=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, nullable=False)

    status = Column(String, default="Open")  
    # Open, In Progress, Resolved, Closed

    sla_deadline = Column(DateTime)
    escalated = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="complaints") 


   