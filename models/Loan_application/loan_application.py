from sqlalchemy import (
    Column, Integer, Numeric, String, Boolean,
    TIMESTAMP, Enum, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base
from core.enums import LoanApplicationStatus


class LoanApplication(Base):
    __tablename__ = "loan_application"

    # ======================
    # Primary Key
    # ======================
    id = Column(Integer, primary_key=True, index=True)

    # ======================
    # Foreign Keys
    # ======================
    user_profile_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    eligibility_id = Column(
        Integer,
        ForeignKey("loan_eligibility.id"),
        nullable=False
    )

    lender_id = Column(
        Integer,
        ForeignKey("lenders.id"),
        nullable=True
    )

    # ======================
    # Core Loan Fields
    # ======================
    reference_number = Column(String(8), unique=True, index=True)

    approved_amount = Column(Numeric(12, 2), nullable=False)
    requested_tenure_months = Column(Integer, nullable=False)

    interest_rate = Column(Numeric(5, 2), nullable=True)
    monthly_emi = Column(Numeric(12, 2), nullable=True)

    processing_fee = Column(Numeric(10, 2), nullable=True)
    gst_amount = Column(Numeric(10, 2), nullable=True)
    total_repayment = Column(Numeric(14, 2), nullable=True)

    current_step = Column(String(50), nullable=False, default="OPENED")

    application_status = Column(
        Enum(LoanApplicationStatus, name="loan_application_status_enum"),
        default=LoanApplicationStatus.DRAFT,
        nullable=False
    )

    is_submitted = Column(Boolean, nullable=False, default=False)
    rejection_reason = Column(String(255), nullable=True)

    # ======================
    # Audit Fields
    # ======================
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    submitted_at = Column(TIMESTAMP, nullable=True)
    reviewed_at = Column(TIMESTAMP, nullable=True)
    approved_at = Column(TIMESTAMP, nullable=True)
    rejected_at = Column(TIMESTAMP, nullable=True)
    disbursed_at = Column(TIMESTAMP, nullable=True)

    ip_address = Column(String, nullable=True)

    # ======================
    # Relationships
    # ======================

    user = relationship(
        "User",
        back_populates="loan_applications"
    )

    purpose = relationship(
        "LoanApplicationPurpose",
        back_populates="loan_application",
        uselist=False,
        cascade="all, delete-orphan"
    )

    references = relationship(
        "LoanApplicationReference",
        back_populates="loan_application",
        cascade="all, delete-orphan"
    )

    declaration = relationship(
        "LoanApplicationDeclaration",
        back_populates="application",
        uselist=False,
        cascade="all, delete-orphan"
    )

    step_tracker = relationship(
        "LoanApplicationStepTracker",
        back_populates="loan_application",
        uselist=False,
        cascade="all, delete-orphan"
    )

    eligibility = relationship(
        "LoanEligibility",
        back_populates="loan_applications"
    )

    lender = relationship(
        "Lender",
        back_populates="loan_applications"
    )

    disbursements = relationship(
        "LoanDisbursement",
        back_populates="application",
        cascade="all, delete-orphan"
    )
    status_history = relationship("LoanStatusHistory",back_populates="application",cascade="all, delete-orphan")
    loans = relationship("Loan",back_populates="application",cascade="all, delete-orphan")