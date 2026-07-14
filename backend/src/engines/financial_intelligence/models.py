"""Financial Intelligence Engine Models.

TypedDict contracts for scenario simulation and comparison.
No database access. All monetary values are integers in paise.
"""

from decimal import Decimal
from typing import Any, TypedDict


class ScenarioResult(TypedDict, total=False):
    """Generic scenario simulation result."""
    monthly_surplus_paise: int
    cumulative_benefit_paise: int
    monthly_savings_created_paise: int
    income_change_paise: int
    cumulative_income_change_paise: int
    revised_surplus_forecast: list[dict[str, Any]]
    estimated_months_saved: int
    interest_saved_paise: int | None
    revised_payoff_projection: list[dict[str, Any]]
    monthly_emi_paise: int
    surplus_impact_paise: int
    foir: Decimal
    affordability: str  # "safe" | "warning" | "unsafe"
    projected_dependency_ratio: Decimal
    risk_change: str  # "improved" | "unchanged"
    requires_rate_input: bool
    forecast: list[dict[str, Any]]


class ScenarioComparison(TypedDict):
    """Comparison between baseline and scenario."""
    improvements: list[str]
    risks: list[str]
    delta: dict[str, Any]


class LoanScenario(TypedDict):
    """Input for new loan simulation."""
    principal_paise: int
    annual_rate_bps: int
    tenure_months: int
    current_surplus_paise: int


class DebtScenario(TypedDict):
    """Input for debt prepayment simulation."""
    debt_accounts: list[dict[str, Any]]
    extra_payment_paise: int
    monthly_surplus_paise: int


# Metrics to compare in scenario comparison
COMPARE_METRICS = [
    "monthly_surplus_paise",
    "cumulative_benefit_paise",
    "months_to_goal",
    "months_to_debt_free",
    "interest_saved_paise",
    "foir",
]
