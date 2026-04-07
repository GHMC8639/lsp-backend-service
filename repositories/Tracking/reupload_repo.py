# app/repositories/document_reupload_repo.py

from sqlalchemy.orm import Session
from models.Tracking.document_reupload import DocumentReupload


class DocumentReuploadRepository:

    @staticmethod
    def create(db: Session, data: dict):
        doc = DocumentReupload(**data)
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_by_application(db: Session, app_id: int):
        return db.query(DocumentReupload).filter(
            DocumentReupload.application_id == app_id
        ).all()

    @staticmethod
    def update_status(db: Session, doc_id: int, new_status: str):
        doc = db.query(DocumentReupload).filter(
            DocumentReupload.id == doc_id
        ).first()

        if not doc:
            return None

        doc.status = new_status
        db.commit()
        db.refresh(doc)
        return doc