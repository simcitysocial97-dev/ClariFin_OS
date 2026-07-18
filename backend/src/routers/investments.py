"""Investment portfolio management endpoints."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from src.errors import NotFoundError
from src.models.explanation import (
    CalculationStep,
    Confidence,
    Evidence,
    Explanation,
    InvestmentSummary,
    InvestmentsResponse,
    SourceReference,
)
from src.repositories.investment_repository import InvestmentRepository

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
    repo = InvestmentRepository()
    investments = repo.get_all()

    # Build evidence and sources for each investment
    investment_evidence: list[Evidence] = []
    investment_sources: list[SourceReference] = []
    investment_summaries: list[InvestmentSummary] = []

    for inv in investments:
        inv_id = inv.get("id", "unknown")
        invested = inv.get("invested_paise", 0) or 0
        current = inv.get("current_value_paise", 0) or 0
        gain = current - invested
        gain_percent = (gain / invested * 100) if invested > 0 else 0

        # Evidence for invested amount
        if invested > 0:
            investment_evidence.append(Evidence(
                id=f"investment-{inv_id}-invested",
                type="data",
                description=f"Invested amount for {inv.get('name', inv_id)}",
                value=invested,
                sourceId=str(inv_id),
            ))

        # Evidence for current value
        if current > 0:
            investment_evidence.append(Evidence(
                id=f"investment-{inv_id}-current",
                type="data",
                description=f"Current value for {inv.get('name', inv_id)}",
                value=current,
                sourceId=str(inv_id),
            ))

        # Evidence for gain
        if gain != 0:
            investment_evidence.append(Evidence(
                id=f"investment-{inv_id}-gain",
                type="data",
                description=f"Gain/Loss for {inv.get('name', inv_id)}",
                value=gain,
                sourceId=str(inv_id),
            ))

        # Source reference
        investment_sources.append(SourceReference(
            type="investment",
            id=str(inv_id),
            name=inv.get("name", f"Investment {inv_id}"),
            date=inv.get("as_of_date"),
        ))

        # Build investment summary
        investment_summaries.append(InvestmentSummary(
            id=inv_id,
            name=inv.get("name", f"Investment {inv_id}"),
            type=inv.get("investment_type", "unknown"),
            invested_paise=invested,
            current_value_paise=current,
            gain_paise=gain,
            gain_percent=round(gain_percent, 2),
            is_active=bool(inv.get("is_active", True)),
        ))

    # Calculate totals
    total_invested = sum(
        int(e.value) for e in investment_evidence
        if isinstance(e.value, int) and "invested" in e.id
    )
    total_current = sum(
        int(e.value) for e in investment_evidence
        if isinstance(e.value, int) and "current" in e.id
    )
    total_gain = total_current - total_invested

    # Calculate confidence
    confidence_bps = 10000
    confidence_reasons: list[str] = []

    if len(investment_evidence) == 0:
        confidence_bps -= 2000
        confidence_reasons.append("No investment data available")

    # Build calculation steps
    calculation_steps: list[CalculationStep] = [
        CalculationStep(
            stepId="sum-invested",
            description="Sum all invested amounts",
            operation="ADD",
            inputIds=[e.id for e in investment_evidence if "invested" in e.id],
            outputId="total-invested",
            order=1,
        ),
        CalculationStep(
            stepId="sum-current",
            description="Sum all current values",
            operation="ADD",
            inputIds=[e.id for e in investment_evidence if "current" in e.id],
            outputId="total-current",
            order=2,
        ),
        CalculationStep(
            stepId="compute-gain",
            description="Compute total gain/loss",
            operation="SUBTRACT",
            inputIds=["total-current", "total-invested"],
            outputId="total-gain",
            order=3,
        ),
    ]

    # Build explanation
    explanation = Explanation(
        metric="investments",
        value=total_current,
        confidence=Confidence(
            value=confidence_bps,
            reason=", ".join(confidence_reasons) if confidence_reasons else "Complete investment data available",
        ),
        evidence=investment_evidence,
        sources=investment_sources,
        calculationSteps=calculation_steps,
    )

    return InvestmentsResponse(
        investments=investment_summaries,
        total_invested_paise=total_invested,
        total_current_value_paise=total_current,
        total_gain_paise=total_gain,
        is_partial=len(investment_evidence) == 0,
        partial_reason="No investment data available" if len(investment_evidence) == 0 else None,
        last_updated=datetime.now().isoformat(),
        explanation=explanation,
    )


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