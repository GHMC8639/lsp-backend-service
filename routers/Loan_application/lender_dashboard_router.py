from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Literal

from core.database import get_db
from core.dependencies import require_roles
from core.logger import logger

from models.Auth.user import User
from models.Loan_application.loan_application import LoanApplication

from services.Loan_application.lender_service import LenderService
from services.Loan_application.loan_disbursement_service import LoanDisbursementService
from services.Loan_application.pre_disbursement_service import PreDisbursementService

from schemas.Loan_application.lender import LenderApplicationListResponse
from schemas.Loan_application.loan_disbursement_schema import (
    DisbursementRequestSchema,
    DisbursementResponseSchema
)
from schemas.Loan_application.loan_predisbursement_schema import (
    PreDisbursementResponseSchema
)
from schemas.Loan_application.rejection_schema import RejectRequestSchema


router = APIRouter(
    prefix="/lender-dashboard",
    tags=["Lender Dashboard"]
)


# -----------------------------------------------------
# 🔐 COMMON OWNERSHIP CHECK
# -----------------------------------------------------
def validate_lender_access(db: Session, application_id: int, lender_id: int):
    application = db.query(LoanApplication).options(
        joinedload(LoanApplication.user_profile)
    ).filter(
        LoanApplication.id == application_id
    ).first()

    if not application:
        raise HTTPException(404, "Application not found")

    if application.lender_id != lender_id:
        logger.warning(f"[UNAUTHORIZED ACCESS] lender={lender_id}, app={application_id}")
        raise HTTPException(403, "Access denied")

    return application


# =====================================================
# VIEW APPLICATIONS
# =====================================================
@router.get(
    "/my-applications",
    response_model=List[LenderApplicationListResponse],
    operation_id="lender_view_applications"
)
def view_lender_applications(
    status: Optional[Literal["SUBMITTED", "APPROVED", "REJECTED"]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    try:
        return LenderService.get_lender_applications(
            db=db,
            user_id=current_user.id,
            status=status
        )

    except Exception as e:
        logger.error(f"[VIEW ERROR] lender={current_user.id}, error={str(e)}")
        raise HTTPException(500, "Failed to fetch applications")


# =====================================================
# APPROVE APPLICATION
# =====================================================
@router.post("/approve/{application_id}", operation_id="lender_approve_application")
def approve_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    try:
        validate_lender_access(db, application_id, current_user.id)

        return LenderService.approve_application(
            db,
            application_id,
            current_user.id
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[APPROVE ERROR] lender={current_user.id}, app={application_id}, error={str(e)}")
        raise HTTPException(400, "Approval failed")


# =====================================================
# REJECT APPLICATION
# =====================================================
@router.post("/reject/{application_id}", operation_id="lender_reject_application")
def reject_application(
    application_id: int,
    request: RejectRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    try:
        validate_lender_access(db, application_id, current_user.id)

        return LenderService.reject_application(
            db,
            application_id,
            current_user.id,
            request.rejection_reason
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[REJECT ERROR] lender={current_user.id}, app={application_id}, error={str(e)}")
        raise HTTPException(400, "Rejection failed")


# =====================================================
# PRE-DISBURSEMENT PREVIEW
# =====================================================
@router.get(
    "/disbursement/preview/{application_id}",
    response_model=PreDisbursementResponseSchema,
    operation_id="lender_pre_disbursement_preview"
)
def preview_pre_disbursement_lender(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    try:
        validate_lender_access(db, application_id, current_user.id)

        return PreDisbursementService.get_preview(
            db=db,
            application_id=application_id
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[PREVIEW ERROR] lender={current_user.id}, app={application_id}, error={str(e)}")
        raise HTTPException(400, "Preview failed")


# =====================================================
# DISBURSE LOAN (WITH BACKGROUND EMAIL)
# =====================================================
@router.post(
    "/disbursement/{application_id}",
    response_model=DisbursementResponseSchema,
    operation_id="lender_disburse_loan"
)
def disburse_loan(
    application_id: int,
    request: DisbursementRequestSchema,
    background_tasks: BackgroundTasks,   # ✅ added
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    try:
        validate_lender_access(db, application_id, current_user.id)

        return LoanDisbursementService.disburse_loan(
            db=db,
            application_id=application_id,
            payment_mode=request.payment_mode,
            background_tasks=background_tasks   # ✅ passed
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[DISBURSE ERROR] lender={current_user.id}, app={application_id}, error={str(e)}")
        raise HTTPException(400, "Disbursement failed")