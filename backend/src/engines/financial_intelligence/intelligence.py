"""Financial Intelligence Aggregator Engine.

Pure composition functions that combine outputs from:
- Behaviour Engine (wellness, credit dependency)
- Cashflow Engine (monthly analysis)
- Forecasting Engine (cashflow, liquidity, credit forecasts)
- Optimization Engine (allocation, action scores)
- Goal Planner (projections, health)

No database access. No LLM calls. No prompt generation.
All monetary values are integers in paise (₹1.00 = 100 paise).
"""

from decimal import Decimal
from typing import Any

from .models import (
    ConfidenceMetadata,
    FinancialSnapshot,
    IntelligenceReport,
)

# ============================================================
# Function 1: build_financial_snapshot
# ============================================================

def build_financial_snapshot(
    cashflow: dict[str, Any],
    liquidity: dict[str, Any],
    debts: list[dict[str, Any]],
    goals: list[dict[str, Any]],
    behaviour: dict[str, Any],
    forecasts: dict[str, Any],
    optimization: dict[str, Any],
) -> FinancialSnapshot:
    """
    Create a normalized financial state from domain-specific inputs.

    This function takes pre-computed data from each domain engine and
    normalizes it into a consistent internal contract.

    Args:
        cashflow: Cashflow data with income_paise, expense_paise, surplus_paise
        liquidity: Liquidity forecast data (months_until_stress, risk_level, etc.)
        debts: List of debt obligations (loans + credit cards)
        goals: List of financial goals
        behaviour: Behaviour metrics (wellness_score, credit_revolver_ratio, etc.)
        forecasts: Forecast outputs (cashflow, liquidity, credit)
        optimization: Optimization outputs (allocation_plan, recommended_actions)

    Returns:
        FinancialSnapshot TypedDict with normalized structure
    """
    return FinancialSnapshot(
        cashflow=cashflow,
        liquidity=liquidity,
        debts=debts,
        goals=goals,
        behaviour=behaviour,
        forecasts=forecasts,
        optimization=optimization,
    )


# ============================================================
# Function 2: generate_financial_priorities
# ============================================================

def generate_financial_priorities(
    optimization_plan: dict[str, Any],
    behaviour: dict[str, Any],
    liquidity_forecast: dict[str, Any],
    goals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert optimization + behaviour signals into ranked actions.

    This function aggregates priorities from existing outputs without
    duplicating recommendation logic. It respects the priority order
    from optimization and the risk signals from behaviour.

    Args:
        optimization_plan: Output from generate_optimization_plan() in optimization engine
        behaviour: Behaviour metrics including credit_revolver_ratio, debt_cycle_score
        liquidity_forecast: Liquidity forecast data with months_until_stress, risk_level
        goals: List of active goals

    Returns:
        List of priority actions with rank, action, reason, impact
    """
    priorities: list[dict[str, Any]] = []
    rank = 1

    recommended_actions = optimization_plan.get("recommended_actions", [])

    # Process recommended actions from optimization (these are already ranked by score)
    for action in recommended_actions:
        action_name = action.get("action", "")
        reason = _get_action_reason(action_name, optimisation=optimization_plan, behaviour=behaviour)
        impact = action.get("impact", "medium")

        priorities.append({
            "rank": rank,
            "action": action_name,
            "reason": reason,
            "impact": impact,
        })
        rank += 1

    # Add priority for emergency fund shortage (from liquidity forecast)
    liquidity_months = _extract_liquidity_months(liquidity_forecast)
    if liquidity_months < 3:
        # Only add if not already covered by optimization priorities
        emergency_exists = any(p["action"] == "increase_emergency_fund" for p in priorities)
        if not emergency_exists and rank <= 3:
            priorities.append({
                "rank": rank,
                "action": "increase_emergency_fund",
                "reason": "emergency_fund_below_target",
                "impact": "high" if liquidity_months < 1 else "medium",
            })
            rank += 1

    # Add priority for high credit dependency (behaviour signal)
    credit_revolver_ratio = Decimal(str(behaviour.get("credit_revolver_ratio", 0) or 0))
    if credit_revolver_ratio > Decimal("0.5"):
        credit_priority_exists = any(
            p["action"] == "pay_credit_card" or p["reason"] == "high_revolving_dependency"
            for p in priorities
        )
        if not credit_priority_exists and rank <= 3:
            priorities.append({
                "rank": rank,
                "action": "pay_credit_card",
                "reason": "high_revolving_dependency",
                "impact": "high",
            })
            rank += 1

    # Sort by rank and return
    priorities.sort(key=lambda p: p["rank"])
    return priorities[:5]


def _get_action_reason(
    action: str,
    optimisation: dict[str, Any],
    behaviour: dict[str, Any],
) -> str:
    """Map action names to human-readable reasons."""
    credit_revolver_ratio = Decimal(str(behaviour.get("credit_revolver_ratio", 0) or 0))
    reason_map = {
        "pay_credit_card": "high_revolving_dependency" if credit_revolver_ratio > Decimal("0.5") else "optimizing_debt",
        "increase_emergency_fund": "emergency_fund_below_target",
        "reduce_expenses": "negative_surplus_detected",
        "increase_investment": "surplus_available_for_investing",
    }
    return reason_map.get(action, "financial_optimization_identified")


def _extract_liquidity_months(liquidity_forecast: dict[str, Any]) -> int:
    """Extract approximate liquidity months from forecast data."""
    projected_min = int(liquidity_forecast.get("projected_min_balance_paise", 0) or 0)
    return max(0, projected_min // 100000)


# ============================================================
# Function 3: calculate_intelligence_confidence
# ============================================================

def calculate_intelligence_confidence(
    cashflow_history_months: int,
    transaction_completeness: Decimal,
    account_coverage: Decimal,
    forecast_variance: Decimal,
) -> ConfidenceMetadata:
    """
    Measure reliability of intelligence recommendations.

    Factors (equal weight 0.25 each):
    - Available data months (3+ months = full score)
    - Transaction completeness (percentage of expected data)
    - Account coverage (percentage of financial accounts included)
    - Forecast variance (lower variance = higher confidence)

    Args:
        cashflow_history_months: Number of months of cashflow data available
        transaction_completeness: Ratio of transactions present (0-1)
        account_coverage: Ratio of accounts covered (0-1)
        forecast_variance: Normalized variance of surplus values (0+; lower = better)

    Returns:
        ConfidenceMetadata with confidence score, quality label, and factor breakdown
    """
    months_score = min(Decimal("1"), Decimal(str(cashflow_history_months)) / Decimal("3"))
    completeness_score = max(Decimal("0"), min(Decimal("1"), transaction_completeness))
    coverage_score = max(Decimal("0"), min(Decimal("1"), account_coverage))

    # Variance normalization: lower variance = higher confidence
    max_variance = Decimal("1e12")
    variance_score = Decimal("1") / (Decimal("1") + forecast_variance / max_variance)
    variance_score = max(Decimal("0"), min(Decimal("1"), variance_score))

    confidence = (
        Decimal("0.25") * months_score +
        Decimal("0.25") * completeness_score +
        Decimal("0.25") * coverage_score +
        Decimal("0.25") * variance_score
    )

    if confidence >= Decimal("0.8"):
        data_quality = "excellent"
    elif confidence >= Decimal("0.6"):
        data_quality = "good"
    elif confidence >= Decimal("0.4"):
        data_quality = "fair"
    else:
        data_quality = "poor"

    return ConfidenceMetadata(
        confidence=confidence,
        data_quality=data_quality,
        factors={
            "data_months": cashflow_history_months,
            "transaction_completeness": transaction_completeness,
            "account_coverage": account_coverage,
            "forecast_variance": forecast_variance,
        },
    )


# ============================================================
# Function 4: generate_financial_intelligence_report
# ============================================================

def generate_financial_intelligence_report(
    financial_state: dict[str, Any],
) -> IntelligenceReport:
    """
    Master composition function.

    Aggregates snapshot, priorities, risks, opportunities, and confidence
    into a unified financial intelligence report.

    Args:
        financial_state: Input dict with keys:
            - cashflow: Cashflow data
            - liquidity: Liquidity forecast
            - debts: List of debt obligations
            - goals: List of financial goals
            - behaviour: Behaviour metrics
            - forecasts: Forecast outputs
            - optimization: Optimization outputs

    Returns:
        IntelligenceReport with all composed data
    """
    cashflow = financial_state.get("cashflow", {})
    liquidity = financial_state.get("liquidity", {})
    debts = financial_state.get("debts", [])
    goals = financial_state.get("goals", [])
    behaviour = financial_state.get("behaviour", {})
    forecasts = financial_state.get("forecasts", {})
    optimization = financial_state.get("optimization", {})

    snapshot = build_financial_snapshot(
        cashflow=cashflow,
        liquidity=liquidity,
        debts=debts,
        goals=goals,
        behaviour=behaviour,
        forecasts=forecasts,
        optimization=optimization,
    )

    priorities = generate_financial_priorities(
        optimization_plan=optimization,
        behaviour=behaviour,
        liquidity_forecast=liquidity,
        goals=goals,
    )

    risks = _aggregate_risks(
        liquidity=liquidity,
        credit_forecast=forecasts.get("credit", {}),
        optimisation=optimization,
        behaviour=behaviour,
    )

    opportunities = _identify_opportunities(
        cashflow=cashflow,
        optimisation=optimization,
        goals=goals,
    )

    health_score = _compute_health_score(behaviour)

    confidence = calculate_intelligence_confidence(
        cashflow_history_months=len(forecasts.get("cashflow", {}).get("forecast", [])),
        transaction_completeness=Decimal(str(behaviour.get("transaction_completeness", 0.8) or 0.8)),
        account_coverage=Decimal(str(behaviour.get("account_coverage", 0.9) or 0.9)),
        forecast_variance=Decimal(str(forecasts.get("cashflow", {}).get("confidence", 0.5) or 0.5)),
    )

    return IntelligenceReport(
        snapshot=snapshot,
        health_score=health_score,
        priorities=priorities,
        risks=risks,
        opportunities=opportunities,
        confidence={
            "confidence": confidence["confidence"],
            "data_quality": confidence["data_quality"],
        },
    )


def _aggregate_risks(
    liquidity: dict[str, Any],
    credit_forecast: dict[str, Any],
    optimisation: dict[str, Any],
    behaviour: dict[str, Any],
) -> list[dict[str, Any]]:
    """Aggregate risk flags from multiple sources."""
    risks: list[dict[str, Any]] = []

    risk_level = liquidity.get("risk_level", "low")
    if risk_level == "high":
        risks.append({
            "type": "liquidity_stress",
            "severity": "critical",
            "source": "forecasting_engine",
            "details": {
                "months_until_stress": liquidity.get("months_until_stress"),
                "projected_min_balance_paise": liquidity.get("projected_min_balance_paise"),
            },
        })
    elif risk_level == "medium":
        risks.append({
            "type": "liquidity_stress",
            "severity": "warning",
            "source": "forecasting_engine",
            "details": {
                "months_until_stress": liquidity.get("months_until_stress"),
            },
        })

    trend = credit_forecast.get("trend", "stable")
    dependency_ratio = credit_forecast.get("current_dependency_ratio", Decimal("0"))
    if trend == "worsening" or (isinstance(dependency_ratio, Decimal) and dependency_ratio > Decimal("0.3")):
        risks.append({
            "type": "credit_dependency",
            "severity": "warning",
            "source": "forecasting_engine",
            "details": {
                "trend": trend,
                "dependency_ratio": str(dependency_ratio),
            },
        })

    debt_cycle_score = int(behaviour.get("debt_cycle_score", 0) or 0)
    if debt_cycle_score > 70:
        risks.append({
            "type": "debt_cycle",
            "severity": "warning",
            "source": "behaviour_engine",
            "details": {
                "debt_cycle_score": debt_cycle_score,
            },
        })

    for warning in optimisation.get("warnings", []):
        risks.append({
            "type": "optimization_warning",
            "severity": "warning",
            "source": "optimization_engine",
            "details": {"message": warning},
        })

    return risks


def _identify_opportunities(
    cashflow: dict[str, Any],
    optimisation: dict[str, Any],
    goals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Identify financial opportunities from surplus and goal data."""
    opportunities: list[dict[str, Any]] = []

    monthly_surplus = int(cashflow.get("monthly_surplus_paise", 0) or 0)

    if monthly_surplus > 500000:
        opportunities.append({
            "type": "surplus_investment",
            "description": "Positive monthly surplus available for investment",
            "potential_benefit_paise": monthly_surplus * 12,
            "confidence": "high",
        })

    for goal in goals:
        if goal.get("goal_type") == "emergency_fund" and goal.get("status") == "active":
            target = goal.get("target_amount_paise", 0)
            current = goal.get("current_amount_paise", 0)
            remaining = target - current
            if remaining > 0 and monthly_surplus > 0:
                opportunities.append({
                    "type": "goal_proximity",
                    "description": "Emergency fund target within reach",
                    "potential_benefit_paise": remaining,
                    "confidence": "high",
                })

    return opportunities


def _compute_health_score(behaviour: dict[str, Any]) -> Decimal:
    """Compute composite health score from behaviour metrics or defaults."""
    wellness = behaviour.get("wellness_score")
    if wellness is not None:
        try:
            return Decimal(str(wellness))
        except (ValueError, TypeError):
            pass

    debt_cycle = Decimal(str(behaviour.get("debt_cycle_score", 50) or 50))
    credit_revolver = Decimal(str(behaviour.get("credit_revolver_ratio", 0) or 0))
    cashflow_stability = Decimal(str(behaviour.get("cashflow_stability", 0.5) or 0.5))

    health = (
        Decimal("0.4") * (Decimal("1") - debt_cycle / Decimal("100")) +
        Decimal("0.4") * (Decimal("1") - credit_revolver) +
        Decimal("0.2") * cashflow_stability
    ) * Decimal("100")

    return max(Decimal("0"), min(Decimal("100"), health))
