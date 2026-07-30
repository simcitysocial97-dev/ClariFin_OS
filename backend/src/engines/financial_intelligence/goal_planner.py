"""Goal Planning Engine - Pure calculation library.

Deterministic goal projection and health scoring functions.
All monetary values are integers in paise (₹1.00 = 100 paise).

Consumes outputs from:
- Financial Forecasting (monthly surplus forecasts)
- Cashflow Engine (monthly surplus data)
- Behaviour Engine (credit dependency patterns)
- Loan Engine (EMI obligations - via existing outputs, no direct calls)

Uses configurable allocation percentage to determine available funds.
Does NOT recalculate income, expenses, debt schedules, or interest.
"""

from decimal import Decimal
from typing import Any

# Default allocation percentage of surplus to goals
DEFAULT_GOAL_ALLOCATION_RATIO = Decimal("0.50")

# Default months of expenses for emergency fund
DEFAULT_EMERGENCY_MONTHS = 6


# ============================================================
# Goal Projection
# ============================================================


def calculate_goal_projection(
    target_amount_paise: int,
    current_amount_paise: int,
    monthly_surplus_forecast: list[dict[str, Any]],
    allocation_ratio: Decimal = DEFAULT_GOAL_ALLOCATION_RATIO,
) -> dict[str, Any]:
    """
    Project goal achievement timeline based on available monthly surplus.

    Uses available monthly surplus with configurable allocation percentage.
    Does NOT assume all surplus is allocated - respects allocation_ratio.

    Args:
        target_amount_paise: Target amount in paise
        current_amount_paise: Current saved amount in paise
        monthly_surplus_forecast: List of forecast dicts with expected_surplus_paise
        allocation_ratio: Fraction of surplus allocated to goal (default: 0.50)

    Returns:
        Dict with:
            - achieved: bool indicating if goal is already achieved
            - projected_completion_month: YYYY-MM of completion (or None)
            - months_required: int number of months (or None)
            - confidence: Decimal confidence score (0-1) based on forecast confidence
    """
    # Check if already achieved
    if current_amount_paise >= target_amount_paise:
        return {
            "achieved": True,
            "projected_completion_month": None,
            "months_required": 0,
            "confidence": Decimal("1.0"),
        }

    # Calculate remaining amount needed
    remaining = target_amount_paise - current_amount_paise

    if remaining <= 0:
        return {
            "achieved": True,
            "projected_completion_month": None,
            "months_required": 0,
            "confidence": Decimal("1.0"),
        }

    # No forecast data - cannot project
    if not monthly_surplus_forecast:
        return {
            "achieved": False,
            "projected_completion_month": None,
            "months_required": None,
            "confidence": Decimal("0.0"),
        }

    # Calculate cumulative progress month by month
    cumulative_saved = 0
    months_count = 0

    # Determine confidence from forecast (use first forecast's confidence or neutral)
    confidence = Decimal("0.5")
    for forecast in monthly_surplus_forecast:
        if "confidence" in forecast:
            try:
                confidence = Decimal(str(forecast["confidence"]))
                break
            except (ValueError, TypeError):
                pass

    for months_count, month_data in enumerate(monthly_surplus_forecast, 1):
        expected_surplus = int(month_data.get("expected_surplus_paise", 0) or 0)

        # Only positive surplus contributes to goal
        if expected_surplus > 0:
            monthly_allocation = int(expected_surplus * allocation_ratio)
            cumulative_saved += monthly_allocation

        if cumulative_saved >= remaining:
            # Goal achieved in this month
            completion_month = month_data.get("month", "")
            return {
                "achieved": True,
                "projected_completion_month": completion_month,
                "months_required": months_count,
                "confidence": confidence,
            }

    # Goal not achieved within forecast horizon
    return {
        "achieved": False,
        "projected_completion_month": None,
        "months_required": None,
        "confidence": confidence,
    }


# ============================================================
# Emergency Fund Target Calculation
# ============================================================


def calculate_emergency_fund_target(
    monthly_expenses_paise: int,
    months_of_cover: int = DEFAULT_EMERGENCY_MONTHS,
) -> dict[str, Any]:
    """
    Calculate recommended emergency fund target.

    Formula: monthly_expenses * months_of_cover

    Args:
        monthly_expenses_paise: Average monthly expenses in paise
        months_of_cover: Number of months to cover (default: 6, configurable)

    Returns:
        Dict with:
            - recommended_target_paise: Target amount in paise
            - months_of_cover: The input months of cover
    """
    if monthly_expenses_paise <= 0:
        return {
            "recommended_target_paise": 0,
            "months_of_cover": months_of_cover,
        }

    recommended_target = monthly_expenses_paise * months_of_cover

    return {
        "recommended_target_paise": recommended_target,
        "months_of_cover": months_of_cover,
    }


# ============================================================
# Debt Payoff Projection
# ============================================================


def _months_to_payoff(
    outstanding_paise: int,
    monthly_payment_paise: int,
) -> int | None:
    """
    Calculate months to payoff given monthly payment.

    Returns None if payment is zero or negative.
    """
    if monthly_payment_paise <= 0:
        return None
    return (outstanding_paise + monthly_payment_paise - 1) // monthly_payment_paise


def calculate_debt_payoff_projection(
    loans: list[dict[str, Any]],
    credit_cards: list[dict[str, Any]],
    monthly_surplus_paise: int,
    allocation_ratio: Decimal = DEFAULT_GOAL_ALLOCATION_RATIO,
) -> dict[str, Any]:
    """
    Project debt payoff timeline using debt avalanche strategy.

    Priority order: Highest interest rate first.
    Uses existing loan/credit card data - does NOT recalculate amortization.

    Args:
        loans: List of loan dicts with outstanding_paise, interest_rate_bps
        credit_cards: List of credit card dicts with outstanding_paise, interest_rate_bps
        monthly_surplus_paise: Available monthly surplus in paise
        allocation_ratio: Fraction of surplus allocated to debt payoff

    Returns:
        Dict with:
            - estimated_months: Total months to payoff all debt
            - interest_saved_paise: Estimated interest avoided by payoff
            - payoff_order: List of debt items in recommended payoff order
            - monthly_allocation_paise: Monthly amount allocated to debt
    """
    if monthly_surplus_paise <= 0 and not loans and not credit_cards:
        return {
            "estimated_months": 0,
            "interest_saved_paise": 0,
            "payoff_order": [],
            "monthly_allocation_paise": 0,
        }

    # Combine all debts
    all_debts = []

    for loan in loans:
        outstanding = int(loan.get("outstanding_paise", 0) or 0)
        if outstanding > 0:
            all_debts.append(
                {
                    "id": loan.get("id"),
                    "type": "loan",
                    "name": loan.get("name", "Unknown Loan"),
                    "outstanding_paise": outstanding,
                    "interest_rate_bps": int(loan.get("interest_rate_bps", 0) or 0),
                    "emi_paise": int(loan.get("emi_paise", 0) or 0),
                }
            )

    for card in credit_cards:
        outstanding = int(card.get("outstanding_paise", 0) or 0)
        if outstanding > 0:
            all_debts.append(
                {
                    "id": card.get("id"),
                    "type": "credit_card",
                    "name": card.get("name", "Unknown Card"),
                    "outstanding_paise": outstanding,
                    "interest_rate_bps": int(card.get("interest_rate_bps", 0) or 0),
                    "minimum_due_paise": int(card.get("minimum_due_paise", 0) or 0),
                }
            )

    if not all_debts:
        return {
            "estimated_months": 0,
            "interest_saved_paise": 0,
            "payoff_order": [],
            "monthly_allocation_paise": 0,
        }

    # Sort by interest rate (debt avalanche - highest rate first)
    payoff_order = sorted(
        all_debts, key=lambda d: d.get("interest_rate_bps", 0), reverse=True
    )

    # Calculate available monthly allocation
    monthly_allocation = (
        int(monthly_surplus_paise * allocation_ratio)
        if monthly_surplus_paise > 0
        else 0
    )

    # Simple estimate: sum of months to payoff each debt
    total_months = 0
    for debt in payoff_order:
        months = _months_to_payoff(debt["outstanding_paise"], monthly_allocation)
        if months is not None:
            total_months += months

    # Estimate interest saved (simplified - assumes payoff vs minimum payments)
    interest_saved = 0
    for debt in all_debts:
        # Rough estimate: 10% annual interest on outstanding
        rate = debt["interest_rate_bps"] or 300
        annual_interest = debt["outstanding_paise"] * int(rate / 100) / 100
        interest_saved += annual_interest

    return {
        "estimated_months": total_months if total_months > 0 else None,
        "interest_saved_paise": int(interest_saved),
        "payoff_order": [
            {
                "id": d["id"],
                "type": d["type"],
                "name": d["name"],
                "outstanding_paise": d["outstanding_paise"],
                "interest_rate_bps": d["interest_rate_bps"],
            }
            for d in payoff_order
        ],
        "monthly_allocation_paise": monthly_allocation,
    }


# ============================================================
# Goal Health Scoring
# ============================================================


def calculate_goal_health(
    target_amount_paise: int,
    current_amount_paise: int,
    months_required: int | None,
    projected_completion_month: str | None,
    target_date: str | None,
) -> dict[str, Any]:
    """
    Calculate goal health score based on progress and timeline.

    Status determination:
        - on_track: On track to meet or beat target date
        - at_risk: Behind schedule but achievable
        - behind: Unlikely to be achieved with current trajectory

    Args:
        target_amount_paise: Target amount in paise
        current_amount_paise: Current saved amount in paise
        months_required: Months to achieve goal (from projection)
        projected_completion_month: Projected completion YYYY-MM
        target_date: Target completion date YYYY-MM-DD

    Returns:
        Dict with:
            - score: Decimal health score (0-1)
            - status: "on_track", "at_risk", or "behind"
            - explanation: Human-readable status explanation
    """
    if target_amount_paise <= 0:
        return {
            "score": Decimal("0"),
            "status": "behind",
            "explanation": "Invalid target amount",
        }

    # Calculate progress ratio
    progress_ratio = Decimal(str(current_amount_paise)) / Decimal(
        str(target_amount_paise)
    )
    progress_ratio = min(Decimal("1"), progress_ratio)  # Cap at 100%

    # Determine status based on timeline
    if months_required is not None and months_required == 0:
        # Already achieved
        return {
            "score": Decimal("1"),
            "status": "on_track",
            "explanation": "Goal already achieved",
        }

    if months_required is None:
        # Cannot project - no forecast data
        if progress_ratio >= Decimal("0.75"):
            status = "on_track"
            explanation = "75%+ complete but timeline unknown"
        elif progress_ratio >= Decimal("0.50"):
            status = "at_risk"
            explanation = "50% complete but timeline unknown"
        else:
            status = "behind"
            explanation = f"{int(progress_ratio * 100)}% complete, timeline unknown"
        return {
            "score": progress_ratio,
            "status": status,
            "explanation": explanation,
        }

    # Compare with target date if provided
    if target_date and projected_completion_month:
        # Extract target month (YYYY-MM)
        target_month = target_date[:7] if len(target_date) >= 7 else target_date

        # Simple month comparison
        try:
            target_year, target_mon = int(target_month[:4]), int(target_month[5:7])
            proj_year, proj_mon = (
                int(projected_completion_month[:4]),
                int(projected_completion_month[5:7]),
            )

            target_total = target_year * 12 + target_mon
            proj_total = proj_year * 12 + proj_mon
            months_diff = proj_total - target_total

            if months_diff <= 0:
                # Will meet or beat target date
                status = "on_track"
                explanation = "On track to meet target date"
            elif months_diff <= 3:
                # Slightly behind
                status = "at_risk"
                explanation = f"Behind schedule by {months_diff} months"
            else:
                status = "behind"
                explanation = f"Significantly behind: {months_diff} months past target"

        except (ValueError, TypeError):
            # Fall back to progress-based scoring
            if progress_ratio >= Decimal("0.5"):
                status = "on_track"
                explanation = "On track to achieve goal"
            elif progress_ratio >= Decimal("0.25"):
                status = "at_risk"
                explanation = "Goal progress slowing"
            else:
                status = "behind"
                explanation = "Goal progress needs attention"

    else:
        # No target date - use progress ratio
        if progress_ratio >= Decimal("0.5"):
            status = "on_track"
            explanation = "On track to achieve goal"
        elif progress_ratio >= Decimal("0.25"):
            status = "at_risk"
            explanation = "Goal progress slowing"
        else:
            status = "behind"
            explanation = "Goal progress needs attention"

    return {
        "score": progress_ratio,
        "status": status,
        "explanation": explanation,
    }


# ============================================================
# Goal Summary Calculation
# ============================================================


def calculate_household_goal_summary(
    goals: list[dict[str, Any]],
    projections: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate household-level goal summary.

    Args:
        goals: List of goal dicts
        projections: List of goal projection dicts (same order as goals)

    Returns:
        Dict with:
            - total_goals: int
            - completed: int count
            - on_track: int count
            - at_risk: int count
            - critical_goals: list of goal summaries
    """
    total_goals = len(goals)
    completed = 0
    on_track = 0
    at_risk = 0
    critical_goals = []

    for i, goal in enumerate(goals):
        status = goal.get("status", "active")
        if status == "completed":
            completed += 1

        projection = projections[i] if i < len(projections) else {}
        health_status = projection.get("status", "behind")

        if health_status == "on_track":
            on_track += 1
        elif health_status == "at_risk":
            at_risk += 1

        if goal.get("priority") == "critical" and status != "completed":
            critical_goals.append(
                {
                    "id": goal.get("id"),
                    "name": goal.get("name"),
                    "goal_type": goal.get("goal_type"),
                    "health": health_status,
                }
            )

    return {
        "total_goals": total_goals,
        "completed": completed,
        "on_track": on_track,
        "at_risk": at_risk,
        "critical_goals": critical_goals,
    }
