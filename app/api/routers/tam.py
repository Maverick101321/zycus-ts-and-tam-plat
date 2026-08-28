from fastapi import APIRouter, HTTPException
from app.tam.agent import generate_account_brief
from app.tam.schemas import AccountBrief

router = APIRouter(prefix="/tam", tags=["TAM"])


@router.get(
    "/account/{account_id}/brief",
    response_model=AccountBrief,
    summary="Generate executive account brief",
)
def get_account_brief(account_id: str) -> AccountBrief:
    """Generate a grounded executive health brief for a given customer account."""
    try:
        return generate_account_brief(account_id)
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
