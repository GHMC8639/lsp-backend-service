from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer
from core.database import Base
from datetime import datetime

class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(BigInteger, primary_key=True)
    mobile_number = Column(String(25), nullable=False)
    username = Column(String(50))
    email = Column(String(255))
    password_hash = Column(String(255))
    otp_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    resend_attempts = Column(Integer, default=0)
    otp_status = Column(String(20), default="SENT") 
    device_id = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    blocked_until = Column(DateTime, nullable=True)
   
  
   
    