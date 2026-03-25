from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.Support.grievance import Grievance
from schemas.Support.grievance_schema import GrievanceCreate

router = APIRouter(
    prefix="/support/grievance",
    tags=["Grievance Officer"]
)


@router.post("/", status_code=201)
def create_grievance(data: GrievanceCreate, db: Session = Depends(get_db)):
    grievance = Grievance(**data.dict())
    db.add(grievance)
    db.commit()
    db.refresh(grievance)
    return grievance


@router.get("/")
def list_grievances(db: Session = Depends(get_db)):
    return db.query(Grievance).all()

