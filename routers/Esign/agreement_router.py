from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from services.Esign.agreement_service import AgreementService
from services.Esign.pdf_generator import PDFGenerator

from schemas.Esign.agreement_schema import AgreementResponse


router = APIRouter(
    prefix="/loan/agreement",
    tags=["Agreement"]
)


# =====================================================
# DEPENDENCY
# =====================================================
def get_agreement_service() -> AgreementService:
    return AgreementService(pdf=PDFGenerator())


# =====================================================
# GENERATE / FETCH AGREEMENT
# =====================================================
@router.post("", response_model=AgreementResponse, operation_id="generate_agreement")
def generate_agreement(
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        return service.fetch_agreement_for_user(
            user_id=current_user.id,
            db=db
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Agreement generation failed"
        )


# =====================================================
# DOWNLOAD AGREEMENT (SMART)
# =====================================================
@router.get("/download", operation_id="download_agreement")
def download_agreement(
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        agreement = service.get_existing_agreement(
            user_id=current_user.id,
            db=db
        )

        if not agreement:
            raise HTTPException(404, "Agreement not generated yet")

        if agreement.user_id != current_user.id:
            raise HTTPException(403, "Unauthorized access")

        # 🔥 SMART FILE SELECTION
        if agreement.esign_status == "SIGNED" and agreement.signed_pdf_path:
            file_path = agreement.signed_pdf_path
        else:
            file_path = agreement.agreement_pdf_path

        if not file_path:
            raise HTTPException(404, "Agreement file not found")

        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            raise HTTPException(404, "File missing on server")

        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=f"agreement_{agreement.application_id}.pdf"
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to download agreement"
        )


# =====================================================
# VERIFY HASH (ADMIN ONLY)
# =====================================================
@router.post("/verify-hash", operation_id="verify_agreement_hash")
def verify_hash(
    file_hash: str,
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),
    current_user: User = Depends(require_roles("ADMIN", "SUPER_ADMIN"))
):
    try:
        return service.verify_hash(file_hash=file_hash, db=db)

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Hash verification failed"
        )