from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class LoanStatusHistory(Base):
    __tablename__ = "loan_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # MUST match LoanApplication table + PK type exactly
    loan_application_id = Column(
        Integer,
        ForeignKey("loan_application.id"),
        nullable=False
    )

    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    source = Column(String, nullable=False)
    status_metadata = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationship
    application = relationship(
        "LoanApplication",
        back_populates="status_history"
    )
    
    application = relationship(
        "LoanApplication",
        back_populates="status_history"
    )