"""Financial Scenario Simulation Engine.

Pure calculation library for "What if I..." scenarios.
Never modifies financial records, never creates transactions, never persists simulations.

All monetary values are integers in paise (₹1.00 = 100 paise).
All interest rates are in basis points (1% = 100 bps).
"""

from decimal import Decimal
from typing import Any

from .goal_planner import (
    calculate_debt_payoff_projection,
)
from .models import COMPARE_METRICS, ScenarioComparison
from .utils import FOIR_SAFE_THRESHOLD, FOIR_WARNING_THRESHOLD, generate_month_sequence

# ============================================================
# Scenario Simulation Functions
# ============================================================

def simulate_expense_reduction(
    current_monthly_expense_paise: int,
    reduction_paise: int,
    monthly_surplus_forecast: list[dict[str, Any]],
    forecast_months: int = 12,
) -> dict[str, Any]:
    """Simulate expense reduction scenario.

    "What if monthly expenses reduce?"

    Args:
        current_monthly_expense_paise: Current total expenses per month
        reduction_paise: Amount to reduce expenses by (positive integer)
        monthly_surplus_forecast: Current surplus forecast with expected_surplus_paise
        forecast_months: Number of months to project

    Returns:
        Dict with monthly_savings_created_paise, projected_surplus_change_paise,
        cumulative_benefit_paise, forecast
    """
    monthly_savings_created_paise = reduction_paise

    # Project improved surplus over forecast horizon
    forecast = []
    total_benefit = 0

    months = generate_month_sequence("2026-08", forecast_months)

    for i, month in enumerate(months):
        base_surplus = int(monthly_surplus_forecast[i].get("expected_surplus_paise", 0) if i < len(monthly_surplus_forecast) else 0)
        improved_surplus = base_surplus + monthly_savings_created_paise

        forecast.append({
            "month": month,
            "projected_surplus_paise": improved_surplus,
            "monthly_savings_paise": monthly_savings_created_paise,
        })
        total_benefit += monthly_savings_created_paise

    return {
        "monthly_savings_created_paise": monthly_savings_created_paise,
        "projected_surplus_change_paise": monthly_savings_created_paise,
        "cumulative_benefit_paise": total_benefit,
        "forecast": forecast,
    }


def simulate_income_change(
    current_income_paise: int,
    change_paise: int,
    monthly_surplus_forecast: list[dict[str, Any]],
    forecast_months: int = 12,
) -> dict[str, Any]:
    """Simulate income change scenario.

    "What if salary/income changes?"

    Args:
        current_income_paise: Current monthly income
        change_paise: Income change (positive for increase, negative for decrease)
        monthly_surplus_forecast: Current surplus forecast
        forecast_months: Number of months to project

    Returns:
        Dict with income_change_paise, cumulative_income_change_paise, revised_surplus_forecast
    """
    cumulative_income_change_paise = change_paise * forecast_months

    # Project revised surplus with income change
    revised_forecast = []

    months = generate_month_sequence("2026-08", forecast_months)

    for i, month in enumerate(months):
        base_surplus = int(monthly_surplus_forecast[i].get("expected_surplus_paise", 0) if i < len(monthly_surplus_forecast) else 0)
        revised_surplus = base_surplus + change_paise

        revised_forecast.append({
            "month": month,
            "expected_surplus_paise": revised_surplus,
        })

    return {
        "income_change_paise": change_paise,
        "cumulative_income_change_paise": cumulative_income_change_paise,
        "revised_surplus_forecast": revised_forecast,
    }


def simulate_debt_prepayment(
    debt_accounts: list[dict[str, Any]],
    extra_payment_paise: int,
    monthly_surplus_paise: int,
) -> dict[str, Any]:
    """Simulate debt prepayment scenario.

    "What if I pay extra toward debt?"

    Uses existing debt payoff projection functions - does NOT recreate amortization.

    Args:
        debt_accounts: List of debt dicts with outstanding_paise, interest_rate_bps
        extra_payment_paise: Extra monthly payment amount toward debt
        monthly_surplus_paise: Current monthly surplus

    Returns:
        Dict with estimated_months_saved, interest_saved_paise, revised_payoff_projection
    """
    # Calculate current payoff timeline
    current_projection = calculate_debt_payoff_projection(
        loans=debt_accounts,
        credit_cards=[],
        monthly_surplus_paise=monthly_surplus_paise,
    )

    # Calculate revised payoff with extra payment
    revised_monthly_allocation = monthly_surplus_paise + extra_payment_paise

    revised_projection = calculate_debt_payoff_projection(
        loans=debt_accounts,
        credit_cards=[],
        monthly_surplus_paise=revised_monthly_allocation,
    )

    # Calculate months saved and interest saved
    current_months = current_projection.get("estimated_months") or 0
    revised_months = revised_projection.get("estimated_months") or 0
    months_saved = max(0, current_months - revised_months)

    # Estimate interest saved (rough: months_saved * average monthly interest)
    total_debt = sum(int(d.get("outstanding_paise", 0) or 0) for d in debt_accounts)
    avg_rate = sum(int(d.get("interest_rate_bps", 0) or 0) for d in debt_accounts)
    avg_rate = avg_rate // len(debt_accounts) if debt_accounts else 300  # Default 3%

    # Annual interest on remaining debt = debt * rate / 100
    annual_interest = total_debt * int(avg_rate / 100) // 100
    monthly_interest_saved = annual_interest // 12 * months_saved

    return {
        "estimated_months_saved": months_saved,
        "interest_saved_paise": monthly_interest_saved,
        "revised_payoff_projection": revised_projection.get("payoff_order", []),
    }


def simulate_new_loan(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
    current_surplus_paise: int,
) -> dict[str, Any]:
    """Simulate new loan scenario.

    "What if I take a new loan?"

    Uses existing loan EMI calculation - does NOT recreate formulas.

    Args:
        principal_paise: Loan principal in paise
        annual_rate_bps: Annual interest rate in basis points
        tenure_months: Loan tenure in months
        current_surplus_paise: Current monthly surplus

    Returns:
        Dict with monthly_emi_paise, surplus_impact_paise, foir, affordability
    """
    # Import loan engine to reuse existing EMI calculation
    from src.engines.loan_engine import compute_emi_fixed

    # Calculate EMI using existing loan engine
    monthly_emi_paise = compute_emi_fixed(principal_paise, annual_rate_bps, tenure_months)

    # Calculate FOIR (Financial Obligation Ratio)
    if current_surplus_paise > 0:
        foir = Decimal(str(monthly_emi_paise)) / Decimal(str(current_surplus_paise))
    else:
        foir = Decimal("1.0")  # No surplus - maximum impact

    # Determine affordability based on thresholds
    if foir < FOIR_SAFE_THRESHOLD:
        affordability = "safe"
    elif foir <= FOIR_WARNING_THRESHOLD:
        affordability = "warning"
    else:
        affordability = "unsafe"

    return {
        "monthly_emi_paise": monthly_emi_paise,
        "surplus_impact_paise": monthly_emi_paise,
        "foir": foir,
        "affordability": affordability,
    }


def simulate_credit_behaviour_change(
    current_credit_dependency_ratio: Decimal,
    current_revolver_ratio: Decimal,
    average_interest_rate_bps: int | None = None,
) -> dict[str, Any]:
    """Simulate credit behavior change scenario.

    "What if revolving behaviour stops?"

    Args:
        current_credit_dependency_ratio: Current credit dependency ratio (0-1)
        current_revolver_ratio: Current revolver ratio (0-1)
        average_interest_rate_bps: Optional average interest rate for interest calculation

    Returns:
        Dict with projected_dependency_ratio, interest_saved_paise, risk_change, requires_rate_input
    """
    # If revolver ratio is zero, no change
    if current_revolver_ratio == 0:
        return {
            "projected_dependency_ratio": current_credit_dependency_ratio,
            "interest_saved_paise": 0,
            "risk_change": "unchanged",
            "requires_rate_input": False,
        }

    # If no rate provided, indicate that rate is needed for precise calculation
    if average_interest_rate_bps is None:
        return {
            "projected_dependency_ratio": current_credit_dependency_ratio,
            "interest_saved_paise": None,
            "risk_change": "improved",
            "requires_rate_input": True,
        }

    # Calculate projected improved dependency ratio
    # Assume revolving behavior contributes proportionally to dependency
    improvement_factor = Decimal("1") - current_revolver_ratio * Decimal("0.8")
    projected_ratio = current_credit_dependency_ratio * improvement_factor

    # Estimate interest saved (requires rate for calculation)
    # Placeholder: interest_saved_paise requires actual revolving balance
    # For now, return the ratio improvement
    interest_saved_paise = 0  # Would need actual balance for precise calc

    return {
        "projected_dependency_ratio": projected_ratio,
        "interest_saved_paise": interest_saved_paise,
        "risk_change": "improved",
        "requires_rate_input": False,
    }


def compare_scenario(
    baseline: dict[str, Any],
    scenario: dict[str, Any],
) -> ScenarioComparison:
    """Compare baseline vs scenario results.

    Generic comparison function that identifies improvements and risks.

    Args:
        baseline: Baseline scenario result
        scenario: Simulated scenario result

    Returns:
        Dict with improvements (list), risks (list), delta (dict)
    """
    improvements = []
    risks = []
    delta = {}

    for metric in COMPARE_METRICS:
        baseline_val = baseline.get(metric)
        scenario_val = scenario.get(metric)

        # Skip if either value is None or not comparable
        if baseline_val is None or scenario_val is None:
            continue

        # Handle Decimal and int comparison
        if isinstance(scenario_val, Decimal):
            scenario_val = float(scenario_val)
        if isinstance(baseline_val, Decimal):
            baseline_val = float(baseline_val)

        # Calculate delta
        if isinstance(scenario_val, (int, float)) and isinstance(baseline_val, (int, float)):
            change = scenario_val - baseline_val
            delta[metric] = change

            # Positive change for surplus/benefit is improvement
            if change > 0:
                if metric == "monthly_surplus_paise":
                    improvements.append(f"Monthly surplus increased by ₹{change // 100}")
                elif metric == "cumulative_benefit_paise":
                    improvements.append(f"Cumulative benefit increased by ₹{change // 100}")
                elif metric == "interest_saved_paise":
                    improvements.append(f"Interest savings projected at ₹{change // 100}")
                elif metric == "foir":
                    improvements.append("FOIR improved below safe threshold")
            elif change < 0:
                if metric == "monthly_surplus_paise":
                    risks.append(f"Monthly surplus decreased by ₹{abs(change) // 100}")
                elif metric == "foir":
                    if float(FOIR_WARNING_THRESHOLD) < scenario_val <= float(FOIR_WARNING_THRESHOLD):
                        pass  # warning zone - no explicit risk
                    else:
                        risks.append("FOIR increased above safe threshold")

    return ScenarioComparison(
        improvements=improvements,
        risks=risks,
        delta=delta,
    )
