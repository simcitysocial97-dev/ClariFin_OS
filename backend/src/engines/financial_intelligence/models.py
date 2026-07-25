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


# Metrics to compare in scenario comparison
COMPARE_METRICS = [
    "monthly_surplus_paise",
    "cumulative_benefit_paise",
    "months_to_goal",
    "months_to_debt_free",
    "interest_saved_paise",
    "foir",
]


# ============================================================
# Intelligence Aggregation Models (Phase 9.5)
# ============================================================


class FinancialSnapshot(TypedDict, total=False):
    """Normalized financial state combining all domain data.

    This is the canonical input contract for the intelligence layer.
    All values are pre-computed from respective engines/repositories.
    """

    # Cashflow data (from cashflow_service)
    cashflow: dict[str, Any]  # Contains income_paise, expense_paise, surplus_paise

    # Liquidity forecast (from forecasting engine)
    liquidity: dict[
        str, Any
    ]  # Contains months_until_stress, risk_level, projected_min_balance_paise

    # Debt obligations (from loan_service + credit_card_service)
    debts: list[
        dict[str, Any]
    ]  # List of loans and credit cards with outstanding_paise, interest_rate_bps

    # Financial goals (from financial_goal_repository)
    goals: list[
        dict[str, Any]
    ]  # Active goals with goal_type, target_amount_paise, etc.

    # Behaviour metrics (from behaviour_service)
    behaviour: dict[
        str, Any
    ]  # Contains wellness_score, credit_revolver_ratio, debt_cycle_score, etc.

    # Forecast outputs (from forecasting engine)
    forecasts: dict[str, Any]  # Contains cashflow_forecast, credit_forecast dicts

    # Optimization outputs (from optimization engine)
    optimization: dict[
        str, Any
    ]  # Contains allocation_plan, recommended_actions, warnings


class IntelligenceReport(TypedDict):
    """Master intelligence report output.

    Composed from snapshot, priorities, confidence, and risk signals.
    """

    snapshot: FinancialSnapshot
    health_score: Decimal  # Composite score 0-100
    priorities: list[dict[str, Any]]  # Ranked actions based on optimization + behaviour
    risks: list[dict[str, Any]]  # Risk flags aggregated from all sources
    opportunities: list[dict[str, Any]]  # Identified opportunities
    confidence: dict[str, Any]  # Data quality and confidence metadata


# Priority action contract
class PriorityAction(TypedDict):
    """A single ranked priority action."""

    rank: int
    action: str
    reason: str
    impact: str  # "high", "medium", "low"


# Confidence metadata contract
class ConfidenceMetadata(TypedDict):
    """Data quality and confidence metrics."""

    confidence: Decimal  # Score 0-1
    data_quality: str  # "excellent", "good", "fair", "poor"
    factors: dict[str, Any]  # Detailed factor breakdown


# Risk flag contract
class RiskFlag(TypedDict):
    type: str
    severity: str
    source: str
    details: dict[str, Any]


# Opportunity contract
class Opportunity(TypedDict):
    type: str
    description: str
    potential_benefit_paise: int
    confidence: str
