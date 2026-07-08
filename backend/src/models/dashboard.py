"""Dashboard domain model."""

from typing import Any

from src.models.base import DomainModel, Money


class DashboardSummary(DomainModel):
    """Dashboard summary with key financial metrics."""

    net_cash_flow: Money
    savings_rate: float
    emi_ratio: float
    buffer_days: int
    financial_health_score: int
    seven_day_trend: float
    category_drift_alert: str | None
    recent_transactions: list[dict[str, Any]]

    model_config = {"from_attributes": True, "validate_assignment": True}
