"""Forecast Invariants - Confidence in bps range, valid values."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def assert_forecast_invariants(forecast_result: dict[str, Any]) -> None:
    """Validate forecasting engine output invariants.

    INVARIANT 6: Forecast confidence in basis points (0-10000 bps = 0-100%).
    All monetary values must be integer paise.

    Args:
        forecast_result: Result dictionary from forecast engine

    Raises:
        AssertionError: If forecast violates invariants
    """
    # Confidence must be in valid range
    if "confidence" in forecast_result:
        confidence = forecast_result["confidence"]

        if isinstance(confidence, Decimal):
            if confidence < Decimal("0") or confidence > Decimal("10000"):
                raise AssertionError(
                    f"Confidence {confidence} out of bps range (0-10000)"
                )
        elif isinstance(confidence, (int, float)):
            if confidence < 0 or confidence > 10000:
                raise AssertionError(
                    f"Confidence {confidence} out of bps range (0-10000)"
                )

    # All paise values must be integers
    from .money import assert_money_invariants

    if "forecast" in forecast_result:
        for row in forecast_result.get("forecast", []):
            assert_money_invariants(row)


def assert_liquidity_forecast_invariants(result: dict[str, Any]) -> None:
    """Validate liquidity forecast invariants.

    INVARIANT: Risk level must be valid (low/warning/high).
    INVARIANT: Months until stress must be None or positive integer.

    Args:
        result: Result from liquidity forecast

    Raises:
        AssertionError: If liquidity forecast violates invariants
    """
    valid_risk_levels = {"low", "warning", "high"}
    if "risk_level" in result and result["risk_level"] not in valid_risk_levels:
        raise AssertionError(f"Invalid risk_level: {result['risk_level']}")

    if "months_until_stress" in result:
        months = result["months_until_stress"]
        if months is not None and months < 0:
            raise AssertionError("months_until_stress cannot be negative")

    # Projected min balance must be non-negative
    if "projected_min_balance_paise" in result:
        if result["projected_min_balance_paise"] < 0:
            raise AssertionError("projected_min_balance_paise cannot be negative")
