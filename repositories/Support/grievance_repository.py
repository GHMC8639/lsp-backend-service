from sqlalchemy.orm import Session
from app.models.grievance import Grievance


class GrievanceRepository:

    def create(self, db: Session, grievance: Grievance):
        db.add(grievance)
        db.commit()
        db.refresh(grievance)
        return grievance

    def get_all(self, db: Session):
        return db.query(Grievance).all()