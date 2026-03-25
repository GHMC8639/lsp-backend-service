from sqlalchemy.orm import Session
from app.models.complaint import Complaint


class ComplaintRepository:

    def create(self, db: Session, complaint: Complaint):
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        return complaint

    def get_all(self, db: Session):
        return db.query(Complaint).all()

    def get_by_id(self, db: Session, complaint_id: int):
        return db.query(Complaint).filter(Complaint.id == complaint_id).first()

    def update(self, db: Session, complaint: Complaint):
        db.commit()
        db.refresh(complaint)
        return complaint