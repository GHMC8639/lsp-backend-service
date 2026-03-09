from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.session import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from services.Loan_application.loan_application_summary_service import (
    LoanApplicationSummaryService,
)
from schemas.Loan_application.loan_application_summary import (
    LoanApplicationSummaryResponseSchema,
)

router = APIRouter(
    prefix="/loan/application",
    tags=["Loan Application Summary"],
)


@router.get(
    "/summary",
    response_model=LoanApplicationSummaryResponseSchema,
    responses={
        400: {
            "description": "Pending steps not completed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "pending_step": "DECLARATION",
                            "message": "Declaration not completed"
                        }
                    }
                }
            },
        },
        404: {
            "description": "No active draft found"
        }
    }
)
def get_application_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    """
    Rules:
    - All mandatory steps must be completed
    - If any step is pending, API returns which step is missing
    - Summary is shown only after DECLARATION is completed
    - Application is auto-detected for logged-in user
    """
    return LoanApplicationSummaryService.get_summary_by_user(
        db=db,
        user_id=current_user.id
    )