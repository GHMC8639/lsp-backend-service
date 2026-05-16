from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.Support.grievance_schema import GrievanceOfficerCreate, GrievanceOfficerResponse
from services.Support.grievance_service import fetch_grievance_officer, add_grievance_officer

router = APIRouter()

@router.get("/grievance", response_model=GrievanceOfficerResponse)
def get_grievance(db: Session = Depends(get_db)):
    return fetch_grievance_officer(db)


@router.post("/grievance", response_model=GrievanceOfficerResponse)
def create_grievance(data: GrievanceOfficerCreate, db: Session = Depends(get_db)):
    return add_grievance_officer(db, data)