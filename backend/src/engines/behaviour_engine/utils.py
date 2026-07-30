"""Utility functions for behaviour engine calculations.

All functions use integer arithmetic with paise values and ROUND_HALF_UP rounding
where Decimal is needed. No database access - pure functions only.
"""

import math
from decimal import ROUND_HALF_UP, Decimal


def _median(values: list[int]) -> Decimal:
    """Calculate median of a list of integers.

    Returns Decimal('0') for empty lists.
    """
    if not values:
        return Decimal("0")

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2

    if n % 2 == 0:
        return (Decimal(str(sorted_vals[mid - 1])) + Decimal(str(sorted_vals[mid]))) / 2
    return Decimal(str(sorted_vals[mid]))


def _variance(values: list[int]) -> Decimal:
    """Calculate variance of a list of integers.

    Returns Decimal('0') for lists with fewer than 2 elements.
    """
    if len(values) < 2:
        return Decimal("0")

    mean = sum(values) / len(values)
    sum_sq_diff = sum((x - mean) ** 2 for x in values)
    return Decimal(str(sum_sq_diff / len(values)))


def _coefficient_of_variation(values: list[int]) -> Decimal:
    """Calculate coefficient of variation (std/mean) for stability metrics.

    Returns Decimal('0') for empty lists or when mean is zero.
    Used for income/expense stability calculations.
    """
    if not values or len(values) < 2:
        return Decimal("0")

    mean = sum(values) / len(values)
    if mean == 0:
        return Decimal("0")

    variance = _variance(values)
    std = Decimal(str(math.sqrt(float(variance))))
    return std / Decimal(str(mean))


def _percentage_change(current: int, previous: int) -> Decimal:
    """Calculate percentage change: (current - previous) / previous.

    Returns Decimal('-1') for zero previous (fully decreased).
    Returns Decimal('0') for equal values.
    """
    if previous == 0:
        # Zero previous - use sentinel for "infinite decrease" but cap at -100%
        return Decimal("-1") if current == 0 else Decimal("-0.9999")

    return Decimal(str(current - previous)) / Decimal(str(previous))


def to_basis_points(decimal_value: Decimal) -> int:
    """Convert a decimal (e.g., 0.1234) to basis points (e.g., 1234).

    Used for stable comparisons and storage of percentage-like values.
    """
    return int(
        (decimal_value * Decimal("10000")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )


def from_basis_points(bps: int) -> Decimal:
    """Convert basis points to decimal (e.g., 1234 -> 0.1234)."""
    return Decimal(str(bps)) / Decimal("10000")


def round_decimal(value: Decimal, places: int = 4) -> Decimal:
    """Round decimal to specified decimal places using ROUND_HALF_UP.

    Used to ensure consistent precision in ratio outputs.
    """
    return value.quantize(Decimal("0." + "0" * places), rounding=ROUND_HALF_UP)
