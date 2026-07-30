"""Financial Intelligence Engine - Forecasting Functions.

Pure forecasting functions for cashflow, liquidity, and credit predictions.
No database access. All monetary values are integers in paise (₹1.00 = 100 paise).

Consumes outputs from:
- Cashflow Engine (monthly surplus data)
- Financial Events (credit events)
- Behaviour Engine (credit dependency patterns)
- Loan Engine (EMI obligations)
- Credit Card Engine (utilization data)
"""

from decimal import Decimal
from typing import Any

from .utils import (
    DEFAULT_EMERGENCY_THRESHOLD_PAISE,
    DEFAULT_FORECAST_MONTHS,
    compute_confidence_from_variance,
    compute_trend_direction,
    find_stress_month,
    generate_month_sequence,
    project_running_balance,
)

# ============================================================
# Cashflow Forecasting
# ============================================================


def forecast_cashflow(
    cashflow_history: list[dict[str, Any]],
    forecast_months: int = DEFAULT_FORECAST_MONTHS,
) -> dict[str, Any]:
    """Project future monthly cash position.

    Uses weighted moving average where recent months have higher weights.
    Confidence is derived from variance of historical surpluses.

    Args:
        cashflow_history: List of monthly cashflow dicts with keys:
            - month: YYYY-MM format string
            - income_paise: Total income (int)
            - expense_paise: Total expenses (int)
            - surplus_paise: income - expense (int, optional)
        forecast_months: Number of months to forecast (default: 3, max: 12)

    Returns:
        Dict with:
            - forecast: List of forecasted months with expected income/expense/surplus
            - confidence: Decimal confidence score (0-1)
            - model_version: Version string for the forecasting model
    """
    # Validate forecast_months
    forecast_months = max(1, min(forecast_months, 12))

    if not cashflow_history:
        # Return empty forecast with zero values
        return {
            "forecast": [
                {
                    "month": month,
                    "expected_income_paise": 0,
                    "expected_expense_paise": 0,
                    "expected_surplus_paise": 0,
                }
                for month in generate_month_sequence("2026-01", forecast_months)
            ],
            "confidence": Decimal("0.5"),  # Neutral confidence for no data
            "model_version": "v1.0-weightedaverage",
        }

    # Sort by month
    sorted_history = sorted(cashflow_history, key=lambda h: h.get("month", ""))

    # Extract values for analysis
    incomes = [int(h.get("income_paise", 0) or 0) for h in sorted_history]
    expenses = [int(h.get("expense_paise", 0) or 0) for h in sorted_history]

    # Calculate surpluses (income - expense)
    surpluses = []
    for h in sorted_history:
        if h.get("surplus_paise") is not None:
            surpluses.append(int(h.get("surplus_paise", 0) or 0))
        else:
            inc = int(h.get("income_paise", 0) or 0)
            exp = int(h.get("expense_paise", 0) or 0)
            surpluses.append(inc - exp)

    # Compute weighted averages (recent months weighted higher)
    expected_income = int(round(_weighted_average(incomes)))
    expected_expense = int(round(_weighted_average(expenses)))
    expected_surplus = expected_income - expected_expense

    # Compute confidence from variance
    confidence = compute_confidence_from_variance(surpluses)

    # Generate forecast months
    last_month = sorted_history[-1].get("month", "2026-01")
    forecast_month_list = generate_month_sequence(
        _next_month(last_month), forecast_months
    )

    forecast = [
        {
            "month": month,
            "expected_income_paise": expected_income,
            "expected_expense_paise": expected_expense,
            "expected_surplus_paise": expected_surplus,
        }
        for month in forecast_month_list
    ]

    return {
        "forecast": forecast,
        "confidence": confidence,
        "model_version": "v1.0-weightedaverage",
    }


def _next_month(month: str) -> str:
    """Get the next month in YYYY-MM format.

    Args:
        month: Month in YYYY-MM format

    Returns:
        Next month in YYYY-MM format
    """
    year, mon = int(month[:4]), int(month[5:7] if len(month) > 5 else "01")
    if mon == 12:
        return f"{year + 1}-01"
    return f"{year}-{mon + 1:02d}"


def _weighted_average(values: list[int]) -> float:
    """Compute weighted average with linear weights.

    Args:
        values: List of integer values

    Returns:
        Weighted average as float
    """
    if not values:
        return 0.0

    weights = [float(i + 1) for i in range(len(values))]
    total_weight = sum(weights)
    weighted_sum = sum(v * w for v, w in zip(values, weights, strict=True))
    return weighted_sum / total_weight if total_weight > 0 else 0.0


# ============================================================
# Liquidity Forecasting
# ============================================================


def forecast_liquidity(
    current_liquidity_paise: int,
    cashflow_forecast: list[dict[str, Any]],
    emergency_threshold_paise: int = DEFAULT_EMERGENCY_THRESHOLD_PAISE,
) -> dict[str, Any]:
    """Predict future liquidity position.

    Identifies when projected balance crosses the emergency threshold.

    Args:
        current_liquidity_paise: Current liquid assets in paise
        cashflow_forecast: List of forecast dicts from forecast_cashflow()
            Each dict must have 'expected_surplus_paise' key
        emergency_threshold_paise: Threshold for stress detection (default: 3,000,000 paise = ₹30,000)

    Returns:
        Dict with:
            - months_until_stress: Month number when threshold crossed (or None)
            - projected_min_balance_paise: Minimum projected balance
            - risk_level: "low", "medium", or "high"
            - model_version: Version string for the forecasting model
    """
    if not cashflow_forecast:
        # No forecast - assume current state continues
        return {
            "months_until_stress": None,
            "projected_min_balance_paise": current_liquidity_paise,
            "risk_level": (
                "low"
                if current_liquidity_paise >= emergency_threshold_paise
                else "high"
            ),
            "model_version": "v1.0-weightedaverage",
        }

    # Extract surpluses from forecast
    monthly_surpluses = [
        int(f.get("expected_surplus_paise", 0) or 0) for f in cashflow_forecast
    ]

    # Project balance trajectory
    projected_min = project_running_balance(current_liquidity_paise, monthly_surpluses)
    stress_month = find_stress_month(
        current_liquidity_paise,
        monthly_surpluses,
        emergency_threshold_paise,
    )

    # Determine risk level based on projected minimum and stress month
    if projected_min >= emergency_threshold_paise:
        risk_level = "low"
    elif stress_month == 1 or stress_month is not None and stress_month <= 2:
        risk_level = "high"
    elif stress_month is not None and stress_month <= 3:
        risk_level = "medium"
    else:
        # Will cross threshold but beyond forecast horizon
        risk_level = "low" if projected_min > 0 else "medium"

    return {
        "months_until_stress": stress_month,
        "projected_min_balance_paise": projected_min,
        "risk_level": risk_level,
        "model_version": "v1.0-weightedaverage",
    }


# ============================================================
# Credit Utilization Forecasting
# ============================================================


def forecast_credit_utilization(
    financial_events: list[dict[str, Any]],
    credit_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """Predict future credit dependency.

    Analyzes revolving behavior and cash advance patterns to forecast
    future credit utilization trends.

    Args:
        financial_events: List of financial event dicts (from FinancialEventsService).
            Normalized events with keys:
            - event_type: Type of event
            - month_bucket: YYYY-MM format
            - lifecycle_state: "open", "settled", "partially_settled", "rolls_over"
        credit_history: List of credit snapshots with keys:
            - month: YYYY-MM format
            - utilization_ratio: Decimal ratio (0-1)
            - revolver_ratio: Decimal ratio (0-1, optional)
            - cash_advance_paise: int (optional)

    Returns:
        Dict with:
            - current_dependency_ratio: Current credit dependency
            - forecast_dependency_ratio: Forecasted ratio based on trend
            - trend: "improving", "stable", or "worsening"
            - model_version: Version string for the forecasting model
    """
    # Compute current dependency from financial events
    current_dependency = _compute_current_credit_dependency(
        financial_events, credit_history
    )

    # Analyze trend from credit history
    utilization_ratios = [
        Decimal(str(h.get("utilization_ratio", 0) or 0))
        for h in credit_history
        if h.get("utilization_ratio") is not None
    ]

    if utilization_ratios:
        trend = compute_trend_direction(utilization_ratios)
    else:
        trend = "stable"

    # Forecast based on trend
    if trend == "worsening" and current_dependency > Decimal("0.1"):
        # Project worsening: increase by 10%
        forecast_dependency = min(
            Decimal("1.0"),
            current_dependency * Decimal("1.1"),
        )
    elif trend == "improving":
        # Project improving: decrease by 10%
        forecast_dependency = max(
            Decimal("0.0"),
            current_dependency * Decimal("0.9"),
        )
    else:
        # Stable trend
        forecast_dependency = current_dependency

    return {
        "current_dependency_ratio": current_dependency,
        "forecast_dependency_ratio": forecast_dependency,
        "trend": trend,
        "model_version": "v1.0-weightedaverage",
    }


def _compute_current_credit_dependency(
    financial_events: list[dict[str, Any]],
    credit_history: list[dict[str, Any]],
) -> Decimal:
    """Compute current credit dependency ratio.

    Uses credit_history if available, otherwise falls back to financial_events.

    Args:
        financial_events: List of financial event dicts
        credit_history: List of credit snapshots

    Returns:
        Decimal credit dependency ratio
    """
    # Try credit history first (normalized structure)
    if credit_history:
        ratios = [
            Decimal(str(h.get("utilization_ratio", 0) or 0)) for h in credit_history
        ]
        if ratios:
            return sum(ratios) / Decimal(str(len(ratios)))

    # Fall back to financial events
    credit_funded = 0
    total_expense = 0

    for event in financial_events:
        event_type = event.get("event_type", "")
        liability_change = int(event.get("liability_change_paise", 0) or 0)

        if event_type in (
            "cash_advance",
            "credit_card_cash_advance",
            "liability_increase",
        ):
            if liability_change > 0:
                credit_funded += liability_change
            total_expense += int(event.get("expense_paise", 0) or 0)

    # If no credit history and no credit events, estimate from revolver behavior
    if credit_funded == 0 and total_expense == 0:
        # Check for revolving behavior in events
        revolver_count = sum(
            1
            for e in financial_events
            if e.get("lifecycle_state") in ("open", "partially_settled", "rolls_over")
        )
        return Decimal("0.3") if revolver_count > 0 else Decimal("0.1")

    if total_expense == 0:
        return Decimal("0")

    ratio = Decimal(str(credit_funded)) / Decimal(str(total_expense))
    return min(Decimal("1.0"), ratio)


# ============================================================
# Cash Shortfall Detection
# ============================================================


def detect_future_cash_shortfall(
    cashflow_forecast: list[dict[str, Any]],
    liquidity_forecast: dict[str, Any],
) -> dict[str, Any]:
    """Early warning signal for future cash shortfall.

    Args:
        cashflow_forecast: List of forecast dicts from forecast_cashflow()
        liquidity_forecast: Dict from forecast_liquidity()

    Returns:
        Dict with:
            - flag: bool indicating shortfall risk
            - severity: "none", "warning", or "critical"
            - expected_month: Month when shortfall expected (or None)
            - reason: Human-readable explanation
            - model_version: Version string for the forecasting model
    """
    months_until_stress = liquidity_forecast.get("months_until_stress")
    projected_min = liquidity_forecast.get("projected_min_balance_paise", 0)
    risk_level = liquidity_forecast.get("risk_level", "low")

    # Count months with negative surplus
    negative_surplus_months = [
        f for f in cashflow_forecast if int(f.get("expected_surplus_paise", 0) or 0) < 0
    ]

    if months_until_stress == 1:
        severity = "critical"
        expected_month = (
            cashflow_forecast[0].get("month") if cashflow_forecast else None
        )
        reason = (
            f"Liquidity will drop below emergency threshold in month {months_until_stress}. "
            f"Projected minimum balance: ₹{abs(projected_min) / 100:.2f}"
        )
    elif months_until_stress and months_until_stress <= 2:
        severity = "critical"
        expected_month = (
            cashflow_forecast[months_until_stress - 1].get("month")
            if len(cashflow_forecast) >= months_until_stress
            else None
        )
        reason = f"Cash shortfall expected within {months_until_stress} months"
    elif months_until_stress:
        severity = "warning"
        expected_month = (
            cashflow_forecast[months_until_stress - 1].get("month")
            if len(cashflow_forecast) >= months_until_stress
            else None
        )
        reason = f"Potential cash shortfall in month {months_until_stress}"
    elif negative_surplus_months and risk_level == "high":
        severity = "warning"
        expected_month = (
            negative_surplus_months[0].get("month") if negative_surplus_months else None
        )
        reason = f"Negative surplus in {len(negative_surplus_months)} forecast month(s)"
    else:
        severity = "none"
        expected_month = None
        reason = "No cash shortfall detected in forecast horizon"

    return {
        "flag": severity in ("warning", "critical"),
        "severity": severity,
        "expected_month": expected_month,
        "reason": reason,
        "model_version": "v1.0-weightedaverage",
    }
