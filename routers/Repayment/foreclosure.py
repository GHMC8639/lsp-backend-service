from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from services.Repayment.foreclosure import create_foreclosure_request


router = APIRouter(
    prefix="/foreclosure",
    tags=["Foreclosure"]
)


@router.post("/request")
def create_foreclosure(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    """
    Create foreclosure request for current user's ACTIVE loan.
    This only calculates and stores foreclosure amount.
    Payment will be handled separately via payment APIs.
    """

    try:
        result = create_foreclosure_request(
            db=db,
            user_id=current_user.id
        )

        return {
            "success": True,
            "message": "Foreclosure request created successfully",
            "data": result
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))