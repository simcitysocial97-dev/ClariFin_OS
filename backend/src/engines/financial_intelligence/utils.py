"""Financial Intelligence Engine Utilities.

Pure helper functions for forecasting calculations.
No database access. All monetary values are integers in paise.
"""

from decimal import Decimal
from typing import Any

# ============================================================
# Constants
# ============================================================

DEFAULT_EMERGENCY_THRESHOLD_PAISE = 3000000  # ₹30,000 emergency buffer
DEFAULT_FORECAST_MONTHS = 3
MAX_FORECAST_MONTHS = 12

# ============================================================
# FOIR Thresholds for Loan Affordability
# ============================================================

FOIR_SAFE_THRESHOLD = Decimal("0.40")  # Below 40% - safe
FOIR_WARNING_THRESHOLD = Decimal("0.60")  # 40-60% - warning, above 60% - unsafe

# ============================================================
# Debt Interest Rate Thresholds (basis points)
# ============================================================

HIGH_INTEREST_THRESHOLD_BPS = 1800  # 18% APR
MEDIUM_INTEREST_THRESHOLD_BPS = 800  # 8% APR

# ============================================================
# Financial Policy Constants
# ============================================================

# Emergency fund
EMERGENCY_FUND_MIN_MONTHS = 6

# Debt allocation default
DEFAULT_DEBT_ALLOCATION_RATIO = Decimal(
    "0.60"
)  # 60% of surplus to debt when high-interest exists

# Goal allocation for long-term goals
LONG_TERM_GOAL_ALLOCATION_RATIO = Decimal("0.40")  # 40% of remaining to long-term goals

# ============================================================
# Action Scoring Weights
# ============================================================

ACTION_WEIGHTS = {
    "interest_saving": Decimal("0.35"),
    "risk_reduction": Decimal("0.30"),
    "urgency": Decimal("0.20"),
    "goal_alignment": Decimal("0.15"),
}

# ============================================================
# Date/Month Utilities
# ============================================================


def next_month(month: str) -> str:
    """Get the next month in YYYY-MM format.

    Args:
        month: Month in YYYY-MM format

    Returns:
        Next month in YYYY-MM format (e.g., "2025-01" -> "2025-02", "2025-12" -> "2026-01")
    """
    year, mon = int(month[:4]), int(month[5:7])
    if mon == 12:
        return f"{year + 1}-01"
    return f"{year}-{mon + 1:02d}"


def generate_month_sequence(start_month: str, count: int) -> list[str]:
    """Generate a sequence of months starting from start_month.

    Args:
        start_month: Starting month in YYYY-MM format
        count: Number of months to generate

    Returns:
        List of months in YYYY-MM format
    """
    months = []
    current = start_month
    for _ in range(count):
        months.append(current)
        current = next_month(current)
    return months


# ============================================================
# Statistical Utilities
# ============================================================


def compute_variance(values: list[int]) -> float:
    """Compute variance of a list of integer values.

    Args:
        values: List of integer values

    Returns:
        Variance as float (0.0 for empty or single-element lists)
    """
    if len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    squared_diffs = [(v - mean) ** 2 for v in values]
    return sum(squared_diffs) / len(values)


def compute_weighted_average(
    values: list[int],
    weights: list[float] | None = None,
) -> float:
    """Compute weighted average of values.

    If no weights provided, uses linear weights (most recent = highest weight).

    Args:
        values: List of integer values
        weights: Optional list of weights (same length as values)

    Returns:
        Weighted average as float
    """
    if not values:
        return 0.0

    if weights is None:
        # Linear weights: last element gets highest weight
        weights = [float(i + 1) for i in range(len(values))]

    if len(weights) != len(values):
        raise ValueError("Weights must have same length as values")

    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(v * w for v, w in zip(values, weights, strict=True))
    return weighted_sum / total_weight


def compute_confidence_from_variance(
    values: list[int],
    max_variance: float = 1e12,
) -> Decimal:
    """Compute confidence score from variance of historical values.

    Lower variance = higher confidence. Confidence is inversely proportional
    to variance and bounded between 0 and 1.

    Args:
        values: List of historical values
        max_variance: Maximum expected variance for normalization (default: 1e12 paise²)

    Returns:
        Decimal confidence score between 0 and 1
    """
    variance = compute_variance(values)

    # Inverse relationship: lower variance = higher confidence
    # Normalize: confidence = 1 / (1 + variance/max_variance)
    normalized = 1.0 / (1.0 + variance / max_variance)
    return Decimal(str(round(min(1.0, max(0.0, normalized)), 4)))


# ============================================================
# Credit Utilization Utilities
# ============================================================


def compute_utilization_ratio(
    credit_history: list[dict[str, Any]],
) -> Decimal:
    """Compute average credit utilization ratio from history.

    Args:
        credit_history: List of credit snapshots with utilization_ratio field

    Returns:
        Decimal average utilization ratio (0-1)
    """
    if not credit_history:
        return Decimal("0")

    ratios = [Decimal(str(h.get("utilization_ratio", 0) or 0)) for h in credit_history]

    if not ratios:
        return Decimal("0")

    return sum(ratios) / Decimal(str(len(ratios)))


def compute_trend_direction(
    ratios: list[Decimal],
) -> str:
    """Determine trend direction from a series of ratios.

    Args:
        ratios: List of Decimal ratios over time

    Returns:
        "improving", "stable", or "worsening"
    """
    if len(ratios) < 2:
        return "stable"

    # Compare first half average to second half average
    mid = len(ratios) // 2
    first_half_avg = sum(ratios[:mid]) / Decimal(str(mid))
    second_half_avg = sum(ratios[mid:]) / Decimal(str(len(ratios) - mid))

    # Small change threshold (10% relative difference)
    if first_half_avg == 0:
        if second_half_avg == 0:
            return "stable"
        diff = second_half_avg
    else:
        diff = abs(second_half_avg - first_half_avg) / first_half_avg

    if diff < Decimal("0.1"):
        return "stable"
    elif second_half_avg > first_half_avg:
        return "worsening"
    else:
        return "improving"


# ============================================================
# Balance Projection Utilities
# ============================================================


def project_running_balance(
    starting_balance: int,
    monthly_surpluses: list[int],
) -> int:
    """Project the minimum balance over a series of months.

    Args:
        starting_balance: Initial balance in paise
        monthly_surpluses: List of monthly surplus/deficit values (positive = surplus)

    Returns:
        Projected minimum balance (most negative point reached)
    """
    current = starting_balance
    min_balance = starting_balance

    for surplus in monthly_surpluses:
        current += surplus
        min_balance = min(min_balance, current)

    return min_balance


def find_stress_month(
    starting_balance: int,
    monthly_surpluses: list[int],
    threshold_paise: int,
) -> int | None:
    """Find the month when balance crosses below threshold.

    Args:
        starting_balance: Initial balance in paise
        monthly_surpluses: List of monthly surplus/deficit values
        threshold_paise: Emergency threshold in paise

    Returns:
        Month number (1-indexed) when threshold crossed, or None if never
    """
    current = starting_balance

    for i, surplus in enumerate(monthly_surpluses):
        current += surplus
        if current < threshold_paise:
            return i + 1  # 1-indexed month

    return None
