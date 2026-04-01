from sqlalchemy import  Column, BigInteger,String, Text
from core.database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String(50),unique=True)
    mobile_number = Column(String(25), unique=True)
    password_hash = Column(String)
    device_id = Column(Text,nullable=True)
    mail = Column(String, unique=True, index=True, nullable=True)
    status = Column(String, default="active")
    role = Column(String,default="USER")

    profile = relationship("UserProfile",back_populates="user",uselist=False,cascade="all, delete-orphan")
    credit_profiles = relationship("CreditProfile", back_populates="user",cascade="all, delete-orphan")
    loan_eligibilities = relationship("LoanEligibility",back_populates="user",cascade="all, delete-orphan")
    loan_applications = relationship("LoanApplication",back_populates="user",cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")
   
    