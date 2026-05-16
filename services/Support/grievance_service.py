from fastapi import HTTPException
from sqlalchemy.orm import Session
from  repositories.Support.grievance_repository import get_grievance_officer, create_grievance_officer
from  schemas.Support.grievance_schema import GrievanceOfficerCreate


def fetch_grievance_officer(db: Session):
    officer = get_grievance_officer(db)
    if not officer:
        raise HTTPException(status_code=404, detail="Grievance officer details not found")
    return officer


def add_grievance_officer(db: Session, data: GrievanceOfficerCreate):
    return create_grievance_officer(db, data)