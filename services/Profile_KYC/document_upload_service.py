import os
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile,Form
from models.Profile_KYC.document_upload import DocumentUpload, DocumentType, DocumentStatus
from repositories.Profile_KYC.user_repository import UserRepository
from repositories.Profile_KYC.document_upload_repository import DocumentUploadRepository
from typing import Optional
from core.config import settings

IMAGE_MAX_BYTES  = 2 * 1024 * 1024   # 2 MB — PAN / Aadhaar
INCOME_MAX_BYTES = 3 * 1024 * 1024   # 3 MB — Salary slip / Bank statement

REQUIRED_DOCS     = [DocumentType.AADHAAR_FRONT, DocumentType.AADHAAR_BACK, DocumentType.PAN_CARD]
INCOME_PROOF_DOCS = [DocumentType.SALARY_SLIP, DocumentType.BANK_STATEMENT]


class DocumentUploadService:

    REQUIRED_DOCS     = [DocumentType.AADHAAR_FRONT, DocumentType.AADHAAR_BACK, DocumentType.PAN_CARD]
    INCOME_PROOF_DOCS = [DocumentType.SALARY_SLIP, DocumentType.BANK_STATEMENT]

    # ── Bulk upload ───────────────────────────────────────────────────────────

    @staticmethod
    def bulk_upload_documents(
        db:            Session,
        user_id:       int,          # ✅ changed from email to user_id
        pan_card:      Optional[UploadFile],
        aadhaar_front: Optional[UploadFile],
        aadhaar_back:  Optional[UploadFile],
        income_proof:  Optional[UploadFile],
        income_type:   Optional[str]= Form(None, description="SALARY_SLIP or BANK_STATEMENT", examples=["SALARY_SLIP"]),
    ) -> dict:
        user = UserRepository.get_by_user_id(db, user_id)  # ✅ changed from get_by_email
        if not user:
            raise HTTPException(404, "User not found")

        if user.pan_status != "VERIFIED" or user.aadhaar_status != "VERIFIED":
            raise HTTPException(400, "Please complete identity verification (PAN + Aadhaar) before uploading documents")
        if user.bank_status != "VERIFIED":
            raise HTTPException(400, "Please complete bank verification before uploading documents")

        file_map: list[tuple[Optional[UploadFile], DocumentType]] = [
            (pan_card,      DocumentType.PAN_CARD),
            (aadhaar_front, DocumentType.AADHAAR_FRONT),
            (aadhaar_back,  DocumentType.AADHAAR_BACK),
        ]

        if income_proof and income_proof.filename:
            valid_income = [DocumentType.SALARY_SLIP.value, DocumentType.BANK_STATEMENT.value]
            if not income_type or income_type.upper() not in valid_income:
                raise HTTPException(
                    400,
                    {
                        "error":        "income_type is required when income_proof is provided",
                        "valid_values": valid_income,
                        "message":      "Set income_type to SALARY_SLIP or BANK_STATEMENT",
                    },
                )
            file_map.append((income_proof, DocumentType(income_type.upper())))

        uploaded_results = []
        skipped          = []

        for file, doc_type in file_map:
            if not file or not file.filename:
                skipped.append(doc_type.value)
                continue
            result = DocumentUploadService._process_single_document(
                db=db, user=user, doc_type=doc_type, file=file
            )
            uploaded_results.append(result)

        if uploaded_results:
            user.document_status = "UPLOADED"
            UserRepository.update_user(db, user)  # ✅ changed from UserRepository.save(db)

        all_docs       = DocumentUploadRepository.get_by_user_id(db, user.user_id)
        uploaded_types = [d.document_type for d in all_docs]
        missing        = []

        for req in DocumentUploadService.REQUIRED_DOCS:
            if req not in uploaded_types:
                missing.append(req.value)
        if not any(t in uploaded_types for t in DocumentUploadService.INCOME_PROOF_DOCS):
            missing.append("SALARY_SLIP or BANK_STATEMENT")

        all_required_uploaded = len(missing) == 0

        return {
            "user_id":               user.user_id,
            "email":                 user.email,
            "uploaded_documents":    uploaded_results,
            "total_uploaded":        len(uploaded_results),
            "skipped_documents":     skipped,
            "missing_documents":     missing,
            "all_required_uploaded": all_required_uploaded,
            "message": (
                "All required documents uploaded successfully."
                if all_required_uploaded
                else f"Documents uploaded. Still missing: {', '.join(missing)}"
            ),
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _process_single_document(
        db, user, doc_type: DocumentType, file: UploadFile  # ✅ removed unused email param
    ) -> dict:
        existing = DocumentUploadRepository.get_by_user_and_type(db, user.user_id, doc_type)

        if existing and existing.status == DocumentStatus.APPROVED:
            raise HTTPException(400, f"{doc_type.value} is already approved and cannot be re-uploaded.")

        DocumentUploadService._validate_file(file, doc_type)
        file_path = DocumentUploadService._save_file(user.user_id, doc_type, file)

        if existing:
            if os.path.exists(existing.file_path):
                try:
                    os.remove(existing.file_path)
                except Exception:
                    pass
            DocumentUploadRepository.delete_document(db, existing)

        document = DocumentUpload(
            user_id       = user.user_id,
            email         = user.email,  # ✅ get email from user object
            document_type = doc_type,
            file_name     = file.filename,
            file_path     = file_path,
            file_size     = file.size,
            mime_type     = file.content_type,
            status        = DocumentStatus.UPLOADED,
            uploaded_at   = datetime.now(timezone.utc),  # ✅ timezone now properly imported
        )
        document = DocumentUploadRepository.create_document(db, document)

        return {
            "document_type": doc_type.value,
            "file_name":     document.file_name,
            "file_size":     document.file_size,
            "status":        document.status.value,
            "uploaded_at":   document.uploaded_at.isoformat(),
            "message":       f"{doc_type.value} uploaded successfully",
        }

    @staticmethod
    def _validate_file(file: UploadFile, doc_type: DocumentType):
        max_bytes = (
            INCOME_MAX_BYTES
            if doc_type in DocumentUploadService.INCOME_PROOF_DOCS
            else IMAGE_MAX_BYTES
        )
        if file.size and file.size > max_bytes:
            max_mb    = max_bytes / (1024 * 1024)
            actual_mb = round(file.size / (1024 * 1024), 2)
            raise HTTPException(
                400,
                {
                    "error":          "File too large",
                    "document_type":  doc_type.value,
                    "file_size_mb":   actual_mb,
                    "max_allowed_mb": max_mb,
                    "message":        f"{doc_type.value}: {actual_mb} MB exceeds the {max_mb} MB limit.",
                },
            )

        file_ext = os.path.splitext(file.filename)[1].lower()

        if doc_type in [DocumentType.PAN_CARD, DocumentType.AADHAAR_FRONT, DocumentType.AADHAAR_BACK]:
            if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
                raise HTTPException(
                    400,
                    f"{doc_type.value} requires JPG or PNG. "
                    f"Got: {file_ext}. Allowed: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}",
                )
        elif doc_type in DocumentUploadService.INCOME_PROOF_DOCS:
            if file_ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
                raise HTTPException(
                    400,
                    f"{doc_type.value} requires PDF. "
                    f"Got: {file_ext}. Allowed: {', '.join(settings.ALLOWED_DOCUMENT_EXTENSIONS)}",
                )

    @staticmethod
    def _save_file(user_id: int, doc_type: DocumentType, file: UploadFile) -> str:
        folder_map = {
            DocumentType.AADHAAR_FRONT:  "aadhaar",
            DocumentType.AADHAAR_BACK:   "aadhaar",
            DocumentType.PAN_CARD:       "pan",
            DocumentType.SALARY_SLIP:    "salary_slips",
            DocumentType.BANK_STATEMENT: "bank_statements",
        }
        upload_dir = os.path.join(settings.UPLOAD_BASE_PATH, folder_map[doc_type])
        os.makedirs(upload_dir, exist_ok=True)

        ext         = os.path.splitext(file.filename)[1]
        unique_name = f"{user_id}_{doc_type.value}_{uuid.uuid4().hex[:8]}{ext}"
        file_path   = os.path.join(upload_dir, unique_name)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        return file_path

    # ── List documents ────────────────────────────────────────────────────────

    @staticmethod
    def list_documents(db: Session, user_id: int) -> dict:  # ✅ changed from email to user_id
        user = UserRepository.get_by_user_id(db, user_id)   # ✅ changed from get_by_email
        if not user:
            raise HTTPException(404, "User not found")

        documents = DocumentUploadRepository.get_by_user_id(db, user.user_id)

        doc_list = [
            {
                "id":            doc.id,
                "document_type": doc.document_type.value,
                "file_name":     doc.file_name,
                "file_size":     doc.file_size,
                "status":        doc.status.value,
                "uploaded_at":   doc.uploaded_at.isoformat(),
                "reviewed_at":   doc.reviewed_at.isoformat() if doc.reviewed_at else None,
                "admin_remarks": doc.admin_remarks,
            }
            for doc in documents
        ]

        uploaded_types = [doc.document_type for doc in documents]
        missing = []
        for req in DocumentUploadService.REQUIRED_DOCS:
            if req not in uploaded_types:
                missing.append(req.value)
        if not any(t in uploaded_types for t in DocumentUploadService.INCOME_PROOF_DOCS):
            missing.append("SALARY_SLIP or BANK_STATEMENT")

        required_types = set(DocumentUploadService.REQUIRED_DOCS)
        income_types   = set(DocumentUploadService.INCOME_PROOF_DOCS)
        approved_types = {doc.document_type for doc in documents if doc.status == DocumentStatus.APPROVED}

        all_approved = (
            required_types.issubset(approved_types)
            and bool(approved_types & income_types)
        )

        if all_approved:
            user.document_status = "APPROVED"
            if (
                user.pan_status         == "VERIFIED"
                and user.aadhaar_status == "VERIFIED"
                and user.bank_status    == "VERIFIED"
            ):
                user.kyc_status = "COMPLETED"
            UserRepository.update_user(db, user)  # ✅ changed from UserRepository.save(db)

        return {
            "user_id":            user.user_id,
            "email":              user.email,
            "documents":          doc_list,
            "total_documents":    len(doc_list),
            "required_documents": ["AADHAAR_FRONT", "AADHAAR_BACK", "PAN_CARD", "SALARY_SLIP or BANK_STATEMENT"],
            "missing_documents":  missing,
            "all_approved":       all_approved,
        }

    # ── Delete document ───────────────────────────────────────────────────────

    @staticmethod
    def delete_document(db: Session, document_id: int, user_id: int) -> dict:  # ✅ changed from email to user_id
        document = DocumentUploadRepository.get_by_id(db, document_id)
        if not document:
            raise HTTPException(404, "Document not found")
        if document.user_id != user_id:  # ✅ compare user_id instead of email
            raise HTTPException(403, "Unauthorised: this document does not belong to you")
        if document.status == DocumentStatus.APPROVED:
            raise HTTPException(400, "Cannot delete an approved document")

        doc_type   = document.document_type.value
        doc_name   = document.file_name
        doc_status = document.status.value

        if os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except Exception:
                pass

        DocumentUploadRepository.delete_document(db, document)

        return {
            "message":         "Document deleted successfully",
            "document_id":     document_id,
            "document_type":   doc_type,
            "file_name":       doc_name,
            "previous_status": doc_status,
        }