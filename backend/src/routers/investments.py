"""Investment portfolio management endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from src.core.dtos.investments_dto import InvestmentsDTO
from src.services.investment_service import InvestmentService

router = APIRouter(prefix="/api", tags=["investments"])


class InvestmentCreate(BaseModel):
    """Investment creation request."""

    name: str
    investment_type: str
    invested_paise: int
    current_value_paise: int
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


@router.get("/investments", response_model=InvestmentsDTO)
def get_investments() -> InvestmentsDTO:
    """Get all investments with calculated returns."""
    service = InvestmentService()
    return service.get_portfolio()


@router.post("/investments")
def create_investment(investment: InvestmentCreate) -> dict[str, Any]:
    """Create a new investment."""
    service = InvestmentService()
    return service.create_investment(
        name=investment.name,
        investment_type=investment.investment_type,
        invested_paise=investment.invested_paise,
        current_value_paise=investment.current_value_paise,
        units=investment.units,
        buy_price_paise=investment.buy_price_paise,
        notes=investment.notes,
    )


@router.put("/investments/{investment_id}")
def update_investment(
    investment_id: str, investment: InvestmentUpdate
) -> dict[str, Any]:
    """Update an investment."""
    from fastapi import HTTPException

    service = InvestmentService()
    result = service.update_investment(
        investment_id,
        units=investment.units,
        current_price_paise=investment.current_price_paise,
        current_value_paise=investment.current_value_paise,
        as_of_date=investment.as_of_date,
        notes=investment.notes,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Investment not found")
    return result


@router.delete("/investments/{investment_id}")
def delete_investment(investment_id: str) -> dict[str, Any]:
    """Delete an investment."""
    service = InvestmentService()
    success = service.delete_investment(investment_id)
    return {"success": success}
