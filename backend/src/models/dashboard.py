"""Dashboard domain model."""

from typing import Any

from pydantic import ConfigDict

from src.models.base import DomainModel, Money


class DashboardSummary(DomainModel):
    """Dashboard summary response."""

    behavior_score: float
    spending_this_month: Money
    top_category: str
    insights: list[str]
    nudges: list[str]
    reconciliation_pending: int
    large_transactions: list[dict[str, Any]]

    model_config = ConfigDict(from_attributes=True, validate_assignment=True)
