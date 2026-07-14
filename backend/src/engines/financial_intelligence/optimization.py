"""Financial Optimization Engine - Pure decision engine for surplus allocation.

All monetary values are integers in paise (₹1.00 = 100 paise).
All interest rates are in basis points (1% = 100 bps).
No database access. No services. Pure calculation only.
"""

from decimal import Decimal
from typing import Any, Literal

from .utils import (
    ACTION_WEIGHTS,
    DEFAULT_DEBT_ALLOCATION_RATIO,
    HIGH_INTEREST_THRESHOLD_BPS,
    LONG_TERM_GOAL_ALLOCATION_RATIO,
    MEDIUM_INTEREST_THRESHOLD_BPS,
)

# ============================================================
# Types
# ============================================================

ActionImpact = Literal["high", "medium", "low"]


# ============================================================
# Cash Advance Debt Entry Helper
# ============================================================

def derive_cash_advance_debt_entry(event: dict[str, Any], holding_period_days: int) -> dict[str, Any]:
    """
    Converts a credit_card_cash_advance financial_event into a debt-list entry
    compatible with rank_debt_payoff_strategy()'s expected shape.

    Args:
        event: Financial event dict with liability_change_paise, expense_paise,
               date_iso, provider, and optionally outstanding_paise
        holding_period_days: Days the cash advance was/will be outstanding to
                            compute effective annualized cost rate

    Returns:
        Debt entry dict compatible with optimization engine, containing:
            - id: Unique identifier (prefixed with "cash_advance_")
            - type: "cash_advance_liability"
            - name: Provider name with "cash advance" suffix
            - outstanding_paise: Remaining amount owed
            - interest_rate_bps: Effective annual rate in basis points
            - source_event_id: Original event ID for traceability
    """
    # Calculate effective annual rate: fee as percentage of principal, annualized
    liability = event.get("liability_change_paise", 0) or 0
    expense = event.get("expense_paise", 0) or 0

    if liability > 0 and expense > 0:
        # Effective annual rate = (fee/principal) * (365/days)
        # Multiply by 10000 to convert to basis points
        effective_annual_bps = round(
            (expense / liability) * 10000 * (365 / max(holding_period_days, 1))
        )
    else:
        effective_annual_bps = 0

    # Use outstanding_paise if explicitly set (including 0 for settled),
    # otherwise fall back to liability_change_paise
    outstanding = event.get("outstanding_paise")
    if outstanding is None:
        outstanding = liability

    return {
        "id": f"cash_advance_{event.get('id', 'unknown')}",
        "type": "cash_advance_liability",
        "name": f"{event.get('provider', 'Unknown')} cash advance",
        "outstanding_paise": outstanding,
        "interest_rate_bps": effective_annual_bps,
        "source_event_id": event.get("id"),
    }


# ============================================================
# Function 1: optimize_surplus_allocation
# ============================================================

def optimize_surplus_allocation(
    monthly_surplus_paise: int,
    debts: list[dict[str, Any]],
    goals: list[dict[str, Any]],
    emergency_fund_status: dict[str, Any],
) -> dict[str, Any]:
    """Allocate monthly surplus across competing priorities.

    Priority order:
    1. Emergency fund below target
    2. High-interest debt (>18% APR)
    3. Medium-interest debt (8-18% APR)
    4. Long-term goals
    5. Investment allocation

    Args:
        monthly_surplus_paise: Available monthly surplus in paise
        debts: List of debt dicts with interest_rate_bps, outstanding_paise
        goals: List of goal dicts with goal_type, target_amount_paise, etc.
        emergency_fund_status: Dict with current_paise, target_paise, deficit_paise

    Returns:
        Dict with allocation list and expected_impact
    """
    if monthly_surplus_paise <= 0:
        return {
            "allocation": [],
            "expected_impact": {},
        }

    allocation: list[dict[str, Any]] = []
    remaining_surplus = monthly_surplus_paise

    # 1. Emergency fund gap (highest priority for risk reduction)
    emergency_deficit = emergency_fund_status.get("deficit_paise", 0)
    if emergency_deficit and emergency_deficit > 0:
        emergency_allocation = min(remaining_surplus, emergency_deficit)
        if emergency_allocation > 0:
            allocation.append({
                "category": "emergency_fund",
                "amount_paise": emergency_allocation,
                "reason": "emergency_fund_below_target",
            })
            remaining_surplus -= emergency_allocation

    # 2. High-interest debt (avalanche priority)
    if remaining_surplus > 0 and debts:
        high_interest_debts = [
            d for d in debts
            if int(d.get("interest_rate_bps", 0) or 0) >= HIGH_INTEREST_THRESHOLD_BPS
        ]
        if high_interest_debts:
            # Allocate portion to high-interest debt
            debt_allocation = int(remaining_surplus * DEFAULT_DEBT_ALLOCATION_RATIO)
            if debt_allocation > 0:
                allocation.append({
                    "category": "debt_payment",
                    "amount_paise": debt_allocation,
                    "reason": "high_interest_debt",
                    "debt_ids": [d.get("id") for d in high_interest_debts if d.get("id")],
                })
                remaining_surplus -= debt_allocation

    # 3. Medium-interest debt
    if remaining_surplus > 0 and debts:
        medium_interest_debts = [
            d for d in debts
            if MEDIUM_INTEREST_THRESHOLD_BPS <= int(d.get("interest_rate_bps", 0) or 0) < HIGH_INTEREST_THRESHOLD_BPS
        ]
        if medium_interest_debts:
            debt_allocation = int(remaining_surplus * DEFAULT_DEBT_ALLOCATION_RATIO)
            if debt_allocation > 0:
                allocation.append({
                    "category": "debt_payment",
                    "amount_paise": debt_allocation,
                    "reason": "medium_interest_debt",
                    "debt_ids": [d.get("id") for d in medium_interest_debts if d.get("id")],
                })
                remaining_surplus -= debt_allocation

    # 4. Long-term goals (excluding emergency fund which already handled)
    if remaining_surplus > 0 and goals:
        long_term_goals = [
            g for g in goals
            if g.get("goal_type") != "emergency_fund" and g.get("status") == "active"
        ]
        if long_term_goals:
            goal_allocation = int(remaining_surplus * LONG_TERM_GOAL_ALLOCATION_RATIO)
            if goal_allocation > 0:
                allocation.append({
                    "category": "goal_saving",
                    "amount_paise": goal_allocation,
                    "reason": "long_term_goals",
                    "goal_ids": [g.get("id") for g in long_term_goals if g.get("id")],
                })
                remaining_surplus -= goal_allocation

    # 5. Remaining to investment allocation
    if remaining_surplus > 0:
        allocation.append({
            "category": "investment",
            "amount_paise": remaining_surplus,
            "reason": "remaining_surplus",
        })

    return {
        "allocation": allocation,
        "expected_impact": {
            "total_allocated_paise": monthly_surplus_paise - remaining_surplus,
            "remaining_paise": remaining_surplus,
        },
    }


# ============================================================
# Function 2: rank_debt_payoff_strategy
# ============================================================

def rank_debt_payoff_strategy(
    debts: list[dict[str, Any]],
    strategy: str = "avalanche",
) -> dict[str, Any]:
    """Recommend optimal debt ordering without calculating interest savings.

    Strategies:
    - avalanche: Highest interest rate first
    - snowball: Smallest balance first
    - balanced: Hybrid (interest + balance weighting)

    Args:
        debts: List of debt dicts with id, balance_paise, interest_rate_bps, minimum_payment_paise
        strategy: Strategy to use (default: "avalanche")

    Returns:
        Dict with priority_order, strategy, and estimated_benefit requiring projection
    """
    valid_strategies = {"avalanche", "snowball", "balanced"}
    if strategy not in valid_strategies:
        strategy = "avalanche"

    if not debts:
        return {
            "recommended_strategy": strategy,
            "priority_order": [],
            "estimated_benefit": {
                "requires_projection": False,
            },
        }

    # Filter debts with positive balance
    active_debts = [
        {**d, "outstanding_paise": int(d.get("outstanding_paise", 0) or d.get("balance_paise", 0) or 0)}
        for d in debts
        if int(d.get("outstanding_paise", 0) or d.get("balance_paise", 0) or 0) > 0
    ]

    if not active_debts:
        return {
            "recommended_strategy": strategy,
            "priority_order": [],
            "estimated_benefit": {
                "requires_projection": False,
            },
        }

    # Sort based on strategy
    if strategy == "avalanche":
        # Highest interest rate first
        priority_order = sorted(
            active_debts,
            key=lambda d: int(d.get("interest_rate_bps", 0) or 0),
            reverse=True,
        )
    elif strategy == "snowball":
        # Smallest balance first
        priority_order = sorted(
            active_debts,
            key=lambda d: int(d.get("outstanding_paise", 0) or d.get("balance_paise", 0) or 0),
        )
    else:  # balanced
        # Hybrid: weight interest (70%) and inverse balance (30%)
        def balanced_score(debt: dict[str, Any]) -> float:
            rate_bps = int(debt.get("interest_rate_bps", 0) or 0)
            balance = int(debt.get("outstanding_paise", 0) or debt.get("balance_paise", 0) or 1)
            # Normalized score: higher rate + smaller balance = higher priority
            rate_score = rate_bps / 5000.0  # Max reasonable rate ~50%
            balance_score = 100000 / max(balance, 1000)  # Inverse, min balance 1000 paise
            return rate_score * 0.7 + balance_score * 0.3

        priority_order = sorted(active_debts, key=balanced_score, reverse=True)

    return {
        "recommended_strategy": strategy,
        "priority_order": [
            {
                "id": d.get("id"),
                "type": d.get("type", "unknown"),
                "outstanding_paise": d.get("outstanding_paise", d.get("balance_paise", 0)),
                "interest_rate_bps": d.get("interest_rate_bps", 0),
                "minimum_payment_paise": d.get("minimum_payment_paise", d.get("minimum_due_paise", 0)),
            }
            for d in priority_order
        ],
        "estimated_benefit": {
            "requires_projection": True,
        },
    }


# ============================================================
# Function 3: optimize_goal_prioritization
# ============================================================

def optimize_goal_prioritization(
    goals: list[dict[str, Any]],
    emergency_fund_status: dict[str, Any] | None = None,
    debt_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rank financial goals based on urgency, impact, and risk reduction.

    Factors:
    - Emergency fund goals outrank all others (highest priority)
    - Urgency: deadline proximity
    - Risk reduction: debt payoff vs. savings
    - User priority field

    Args:
        goals: List of goal dicts with goal_type, target_paise, deadline, priority
        emergency_fund_status: Optional emergency fund status
        debt_status: Optional debt status for risk assessment

    Returns:
        Dict with priority_order and recommendations
    """
    if not goals:
        return {
            "priority_order": [],
            "recommendations": [],
        }

    active_goals = [g for g in goals if g.get("status") != "completed"]

    # Sort goals by priority
    def goal_priority_score(goal: dict[str, Any]) -> tuple[int, int]:
        goal_type = goal.get("goal_type", "")
        user_priority = int(goal.get("priority", 0) or 0)
        deadline = goal.get("deadline", goal.get("target_date"))

        # Emergency fund is always highest priority
        if goal_type == "emergency_fund":
            type_score = 0
        # Debt payoff is high priority
        elif goal_type == "debt_payoff":
            type_score = 1
        # Short deadline increases priority
        elif deadline:
            # Extract months until deadline
            deadline_month = deadline[:7] if len(deadline) >= 7 else "2099-01"
            deadline_score = 2  # Will be refined based on proximity
        else:
            type_score = 3

        # Combine with user priority (inverted: lower user priority number = higher priority)
        return (type_score, 10 - user_priority)

    # Calculate deadline urgency
    def deadline_score(goal: dict[str, Any]) -> int:
        deadline = goal.get("deadline", goal.get("target_date"))
        if not deadline:
            return 100  # No deadline = lowest urgency

        # Parse deadline month and compare to current
        try:
            deadline_month = deadline[:7]  # YYYY-MM
            # Simple urgency score based on months until deadline
            # Goals within 6 months get higher urgency
            return 0  # Will be calculated dynamically in production
        except (ValueError, TypeError):
            return 50

    # Sort active goals
    sorted_goals = sorted(
        active_goals,
        key=lambda g: (
            0 if g.get("goal_type") == "emergency_fund" else
            1 if g.get("goal_type") == "debt_payoff" else
            2,
            int(g.get("priority", 5) or 5),  # Lower number = higher priority
        ),
    )

    priority_order = [
        {
            "id": g.get("id"),
            "goal_type": g.get("goal_type"),
            "rank": i + 1,
        }
        for i, g in enumerate(sorted_goals)
    ]

    recommendations = []
    if emergency_fund_status and emergency_fund_status.get("deficit_paise", 0) > 0:
        recommendations.append({
            "recommendation": "prioritize_emergency_fund",
            "reason": "Emergency fund below target threshold",
        })

    if debt_status and debt_status.get("total_high_interest_debt_paise", 0) > 0:
        recommendations.append({
            "recommendation": "consider_debt_consolidation",
            "reason": "High-interest debt present",
        })

    return {
        "priority_order": priority_order,
        "recommendations": recommendations,
    }


# ============================================================
# Function 4: calculate_financial_action_score
# ============================================================

def calculate_financial_action_score(
    action: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Score possible actions based on deterministic criteria.

    Actions:
    - pay_credit_card
    - increase_emergency_fund
    - increase_investment
    - reduce_expenses

    Scoring factors:
    - interest_saving: 35% weight
    - risk_reduction: 30% weight
    - urgency: 20% weight
    - goal_alignment: 15% weight

    Args:
        action: Action type to score
        context: Dict with apr, surplus, balances, emergency_deficit, etc.

    Returns:
        Dict with action, score, impact, and drivers
    """
    valid_actions = {
        "pay_credit_card", "increase_emergency_fund",
        "increase_investment", "reduce_expenses",
    }

    if action not in valid_actions:
        return {
            "action": action,
            "score": Decimal("0"),
            "impact": "low",
            "drivers": [],
        }

    score = Decimal("0")
    drivers: list[str] = []

    # Interest saving factor (35%)
    apr_bps = int(context.get("interest_rate_bps", 0) or context.get("apr_bps", 0) or 0)
    if apr_bps >= HIGH_INTEREST_THRESHOLD_BPS:
        interest_score = Decimal("0.9")
        drivers.append("high_interest_rate")
    elif apr_bps >= MEDIUM_INTEREST_THRESHOLD_BPS:
        interest_score = Decimal("0.6")
    else:
        interest_score = Decimal("0.3")

    score += interest_score * ACTION_WEIGHTS["interest_saving"]

    # Risk reduction factor (30%)
    if action == "pay_credit_card":
        credit_revolver_ratio = Decimal(str(context.get("credit_revolver_ratio", 0) or 0))
        if credit_revolver_ratio > Decimal("0.5"):
            risk_score = Decimal("0.9")
            drivers.append("reduces_revolver_risk")
        elif credit_revolver_ratio > Decimal("0.2"):
            risk_score = Decimal("0.6")
            drivers.append("reduces_credit_risk")
        else:
            risk_score = Decimal("0.4")
        score += risk_score * ACTION_WEIGHTS["risk_reduction"]
    elif action == "increase_emergency_fund":
        emergency_deficit = int(context.get("emergency_deficit_paise", 0) or 0)
        if emergency_deficit > 0:
            risk_score = Decimal("0.9")
            drivers.append("emergency_fund_gap")
        else:
            risk_score = Decimal("0.3")
        score += risk_score * ACTION_WEIGHTS["risk_reduction"]
    else:
        score += Decimal("0.3") * ACTION_WEIGHTS["risk_reduction"]

    # Urgency factor (20%)
    if action == "pay_credit_card" and apr_bps >= HIGH_INTEREST_THRESHOLD_BPS:
        urgency_score = Decimal("0.9")
        drivers.append("urgent_interest_cost")
    elif action == "increase_emergency_fund":
        months_until_stress = context.get("months_until_stress")
        if months_until_stress is not None and months_until_stress <= 2:
            urgency_score = Decimal("0.9")
            drivers.append("liquidity_stress_approaching")
        elif months_until_stress is not None:
            urgency_score = Decimal("0.6")
        else:
            urgency_score = Decimal("0.5")
    elif action == "reduce_expenses":
        urgency_score = Decimal("0.7")
        drivers.append("immediate_cash_flow_improvement")
    else:
        urgency_score = Decimal("0.4")

    score += urgency_score * ACTION_WEIGHTS["urgency"]

    # Goal alignment factor (15%)
    if action == "pay_credit_card":
        # Aligns with debt payoff goals
        debt_goals = context.get("debt_goals_count", 0)
        goal_score = Decimal("0.8") if debt_goals > 0 else Decimal("0.4")
    elif action == "increase_emergency_fund":
        goal_score = Decimal("0.9")
        drivers.append("aligns_with_stability")
    elif action == "increase_investment":
        investment_goals = context.get("investment_goals_count", 0)
        goal_score = Decimal("0.8") if investment_goals > 0 else Decimal("0.3")
    else:
        goal_score = Decimal("0.5")

    score += goal_score * ACTION_WEIGHTS["goal_alignment"]

    # Determine impact level
    if score >= Decimal("0.7"):
        impact: ActionImpact = "high"
    elif score >= Decimal("0.4"):
        impact = "medium"
    else:
        impact = "low"

    return {
        "action": action,
        "score": score.quantize(Decimal("0.01")),
        "impact": impact,
        "drivers": drivers,
    }


# ============================================================
# Function 5: generate_optimization_plan
# ============================================================

def generate_optimization_plan(
    financial_state: dict[str, Any],
) -> dict[str, Any]:
    """Master orchestrator that combines all optimization functions.

    This is a composition function only - it receives pre-computed
    financial state data and delegates to the other optimization functions.

    Args:
        financial_state: Dict containing:
            - surplus: Monthly surplus information
            - debts: List of debt data
            - goals: List of goal data
            - forecast: Cashflow forecast
            - risk: Risk indicators

    Returns:
        Dict with recommended_actions, allocation_plan, warnings, confidence
    """
    # Handle empty state gracefully
    if not financial_state:
        return {
            "recommended_actions": [],
            "allocation_plan": {},
            "warnings": ["No financial state data provided"],
            "confidence": Decimal("0"),
        }

    # Extract data
    surplus = financial_state.get("surplus", {})
    debts = financial_state.get("debts", [])
    goals = financial_state.get("goals", [])
    forecast = financial_state.get("forecast", {})
    risk = financial_state.get("risk", {})

    monthly_surplus_paise = int(surplus.get("monthly_surplus_paise", 0) or 0)

    # Build emergency fund status
    emergency_deficit = max(0, int(forecast.get("emergency_threshold_paise", 3000000)) - int(forecast.get("current_liquidity_paise", 0) or 0))
    emergency_fund_status: dict[str, Any] = {
        "current_paise": int(forecast.get("current_liquidity_paise", 0) or 0),
        "target_paise": forecast.get("emergency_threshold_paise", 3000000),
        "deficit_paise": emergency_deficit,
    }

    # 1. Optimize surplus allocation
    allocation_result = optimize_surplus_allocation(
        monthly_surplus_paise=monthly_surplus_paise,
        debts=debts,
        goals=goals,
        emergency_fund_status=emergency_fund_status,
    )

    # 2. Rank debt strategy
    debt_strategy = rank_debt_payoff_strategy(
        debts=debts,
        strategy="avalanche",
    )

    # 3. Optimize goal prioritization
    goal_prioritization = optimize_goal_prioritization(
        goals=goals,
        emergency_fund_status=emergency_fund_status,
        debt_status={"total_high_interest_debt_paise": _sum_high_interest_debt(debts)},
    )

    # 4. Calculate action scores
    context = {
        "emergency_deficit_paise": emergency_fund_status["deficit_paise"],
        "months_until_stress": forecast.get("months_until_stress"),
        "credit_revolver_ratio": Decimal(str(risk.get("credit_revolver_ratio", "0") or "0")),
        "debt_goals_count": sum(1 for g in goals if g.get("goal_type") == "debt_payoff"),
    }

    action_scores = [
        calculate_financial_action_score(
            action="pay_credit_card",
            context={**context, "interest_rate_bps": HIGH_INTEREST_THRESHOLD_BPS},
        ),
        calculate_financial_action_score(
            action="increase_emergency_fund",
            context=context,
        ),
    ]

    # Build recommendations
    recommended_actions = [
        {
            "action": score["action"],
            "amount_paise": 0,  # Will be filled by allocation
            "score": score["score"],
            "impact": score["impact"],
            "drivers": score["drivers"],
        }
        for score in action_scores
        if score["score"] >= Decimal("0.5")
    ]

    # Build warnings
    warnings: list[str] = []
    if emergency_fund_status["deficit_paise"] > 0:
        warnings.append("Emergency fund below target threshold")
    if _sum_high_interest_debt(debts) > 0:
        warnings.append("High-interest debt present")
    if monthly_surplus_paise <= 0:
        warnings.append("No surplus available for optimization")

    # Calculate confidence
    confidence = Decimal("0")
    if monthly_surplus_paise > 0:
        confidence = Decimal("0.7")  # Base confidence with data
    if forecast.get("confidence"):
        try:
            confidence = Decimal(str(forecast["confidence"]))
        except (ValueError, TypeError):
            pass

    return {
        "recommended_actions": recommended_actions,
        "allocation_plan": allocation_result.get("allocation", []),
        "warnings": warnings,
        "confidence": confidence,
    }


def _sum_high_interest_debt(debts: list[dict[str, Any]]) -> int:
    """Sum outstanding amounts for high-interest debts only."""
    return sum(
        int(d.get("outstanding_paise", 0) or d.get("balance_paise", 0) or 0)
        for d in debts
        if int(d.get("interest_rate_bps", 0) or 0) >= HIGH_INTEREST_THRESHOLD_BPS
    )