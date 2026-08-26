"""Behavioral strengthening tests for credit_card interest (M9-C42.23 Batch 4).

Pins the financial invariants of the interest module: 365-day Indian convention,
banker's rounding, aggregate monthly accrual, and input-validation guards. These
target the Class-A interest/fee survivors identified in the C42.21/22 inventories.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.engines.credit_card_engine.interest import (
    bps_to_daily_rate,
    compute_daily_interest,
    compute_monthly_interest_charge,
    compute_monthly_interest_simple,
)


def test_bps_to_daily_rate_uses_365_day_year() -> None:
    """Indian credit-card convention: divide by 365*10000, not 360."""
    rate = bps_to_daily_rate(2400)
    assert rate == Decimal(2400) / Decimal(3650000)
    # Distinguish from a 360-day convention (would be materially higher)
    assert rate != Decimal(2400) / Decimal(3600000)


def test_compute_daily_interest_exact_paise() -> None:
    """1,000,000 paise @ 2400 bps/day accrues 658 paise (banker's rounding)."""
    assert compute_daily_interest(1_000_000, 2400) == 658


def test_compute_daily_interest_zero_short_circuits() -> None:
    assert compute_daily_interest(0, 2400) == 0
    assert compute_daily_interest(1_000_000, 0) == 0


def test_compute_daily_interest_rejects_negative_inputs() -> None:
    with pytest.raises(ValueError):
        compute_daily_interest(-1, 2400)
    with pytest.raises(ValueError):
        compute_daily_interest(1_000_000, -1)


def test_monthly_interest_charge_empty_is_zero() -> None:
    assert compute_monthly_interest_charge([], 2400) == 0


def test_monthly_interest_charge_aggregates_daily() -> None:
    balances = [("2025-01-01", 1_000_000), ("2025-01-02", 1_000_000)]
    assert compute_monthly_interest_charge(balances, 2400) == 658 * 2


def test_monthly_interest_charge_rejects_negative_balance() -> None:
    with pytest.raises(ValueError):
        compute_monthly_interest_charge([("2025-01-01", -5)], 2400)


def test_monthly_interest_simple_exact() -> None:
    assert compute_monthly_interest_simple(1_000_000, 2400, 30) == 19_740
    assert compute_monthly_interest_simple(1_000_000, 2400, 1) == 658


def test_monthly_interest_simple_rejects_invalid_cycle() -> None:
    with pytest.raises(ValueError):
        compute_monthly_interest_simple(1_000_000, 2400, 0)
    with pytest.raises(ValueError):
        compute_monthly_interest_simple(1_000_000, 2400, -1)
    with pytest.raises(ValueError):
        compute_monthly_interest_simple(-1, 2400, 30)
