"""
Utility functions for loan engine calculations.
"""

from decimal import Decimal


def bps_to_decimal_rate(bps: int) -> Decimal:
    """
    Convert basis points to decimal annual rate.

    850 bps → 0.085
    """
    return Decimal(bps) / Decimal(10000)


def bps_to_monthly_rate(bps: int) -> Decimal:
    """
    Convert basis points to decimal monthly rate.

    850 bps → 0.007083...
    """
    return Decimal(bps) / Decimal(120000)
