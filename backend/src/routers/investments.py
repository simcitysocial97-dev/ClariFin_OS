"""Investment portfolio management endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from src.errors import NotFoundError
from src.models.explanation import InvestmentsResponse
from src.repositories.investment_repository import InvestmentRepository
from src.services.investment_service import InvestmentService

router = APIRouter(prefix="/api", tags=["investments"])


class InvestmentCreate(BaseModel):
    """Investment creation request."""
    name: str
    investment_type: str
    invested_paise: int
    current_value_paise: int
    as_of_date: str
    units: float | None = None
    buy_price_paise: int | None = None
    current_price_paise: int | None = None
    notes: str | None = None


class InvestmentUpdate(BaseModel):
    """Investment update request."""
    units: float | None = None
    current_price_paise: int | None = None
    current_value_paise: int | None = None
    as_of_date: str | None = None
    notes: str | None = None


@router.get("/investments", response_model=InvestmentsResponse)
def get_investments() -> InvestmentsResponse:
    """Get all investments with calculated returns and explanation."""
    service = InvestmentService()
    return service.calculate_with_explanation()


@router.post("/investments")
def create_investment(investment: InvestmentCreate) -> dict[str, Any]:
    """Create a new investment."""
    repo = InvestmentRepository()
    created = repo.create(
        name=investment.name,
        investment_type=investment.investment_type,
        invested_paise=investment.invested_paise,
        current_value_paise=investment.current_value_paise,
        units=investment.units,
        notes=investment.notes,
    )
    return {"success": True, "investment": created}


@router.put("/investments/{investment_id}")
def update_investment(investment_id: str, investment: InvestmentUpdate) -> dict[str, Any]:
    """Update an investment."""
    repo = InvestmentRepository()
    updated = repo.update(
        investment_id,
        **{k: v for k, v in investment.model_dump().items() if v is not None}
    )
    if not updated:
        raise NotFoundError(f"Investment {investment_id} not found")
    return {"success": True, "investment": updated}


@router.delete("/investments/{investment_id}")
def delete_investment(investment_id: str) -> dict[str, Any]:
    """Delete an investment."""
    repo = InvestmentRepository()
    success = repo.delete(investment_id)
    if not success:
        raise NotFoundError(f"Investment {investment_id} not found")
    return {"success": True}