"""Hypothesis profiles and strategies for property testing.

Profiles:
- fast: 20 examples (developer iteration)
- normal: 150 examples (CI)
- deep: 1000 examples (nightly)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, cast

import pytest
from hypothesis import Phase, settings
from hypothesis import strategies as st

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================================
# Hypothesis Profiles
# ============================================================================

def get_profile() -> str:
    """Get current test profile from environment."""
    return os.getenv("HYPOTHESIS_PROFILE", "fast") or "fast"


def configure_settings() -> settings:
    """Configure Hypothesis settings based on profile."""
    profile = get_profile()

    if profile == "fast":
        return settings(max_examples=20, phases=[Phase.generate])
    elif profile == "normal":
        return settings(max_examples=150, phases=[Phase.generate, Phase.shrink])
    elif profile == "deep":
        return settings(max_examples=1000, phases=[Phase.generate, Phase.shrink, Phase.explain])
    else:
        return settings(max_examples=20)


# ============================================================================
# Domain Strategies (Hypothesis wrapper around plain builders)
# ============================================================================

@st.composite
def paise_strategy(draw: Any, min_val: int = -100000000, max_val: int = 100000000) -> int:
    """Integer paise value strategy.

    Uses full int32 range to support large financial values.
    Negative values are valid (debits/expenses).
    """
    return cast(int, draw(st.integers(min_value=min_val, max_value=max_val)))


@st.composite
def positive_paise_strategy(draw: Any, min_val: int = 1, max_val: int = 100000000) -> int:
    """Positive integer paise strategy."""
    return cast(int, draw(st.integers(min_value=min_val, max_value=max_val)))


@st.composite
def confidence_bps_strategy(draw: Any) -> int:
    """Confidence in basis points (0-10000 = 0-100%)."""
    return cast(int, draw(st.integers(min_value=0, max_value=10000)))


@st.composite
def iso_date_strategy(draw: Any) -> str:
    """ISO 8601 date string strategy."""
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))

    # Handle month-end correctly
    days_in_month = [
        31,
        29 if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0 else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 30,
    ]
    day = draw(st.integers(min_value=1, max_value=days_in_month[month - 1]))

    return f"{year:04d}-{month:02d}-{day:02d}"


@st.composite
def loan_rate_bps_strategy(draw: Any) -> int:
    """Loan interest rate in basis points (600-2400 = 6%-24%)."""
    return cast(int, draw(st.integers(min_value=600, max_value=2400)))


@st.composite
def credit_rate_bps_strategy(draw: Any) -> int:
    """Credit card rate in basis points (1800-4800 = 18%-48%)."""
    return cast(int, draw(st.integers(min_value=1800, max_value=4800)))


@st.composite
def cash_summary_strategy(draw: Any) -> dict[str, Any]:
    """Cashflow summary for cashflow engine."""
    return {
        "income_paise": draw(positive_paise_strategy()),
        "expense_paise": draw(positive_paise_strategy()),
    }


@st.composite
def financial_event_strategy(draw: Any) -> dict[str, Any]:
    """Financial event for cashflow overlay."""
    event_types = ["cash_advance", "credit_card_cash_advance", "liability_increase"]
    return {
        "event_type": draw(st.sampled_from(event_types)),
        "amount_paise": draw(positive_paise_strategy()),
        "asset_change_paise": draw(st.integers(min_value=0, max_value=100000000)),
        "liability_change_paise": draw(positive_paise_strategy()),
        "expense_paise": draw(st.integers(min_value=0, max_value=10000000)),
        "income_paise": draw(st.integers(min_value=0, max_value=10000000)),
        "provider": draw(st.sampled_from(["CRED", "Razorpay", "BankABC"])),
        "date_iso": draw(iso_date_strategy()),
    }


@st.composite
def loan_data_strategy(draw: Any) -> dict[str, Any]:
    """Loan data for loan engine testing."""
    principal = draw(positive_paise_strategy())
    rate_bps = draw(loan_rate_bps_strategy())
    tenure = draw(st.integers(min_value=12, max_value=360))

    return {
        "principal_paise": principal,
        "outstanding_paise": principal,  # Start fully outstanding
        "annual_rate_bps": rate_bps,
        "tenure_months": tenure,
        "start_date": draw(iso_date_strategy()),
    }


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def hypothesis_settings() -> settings:
    """Provide configured Hypothesis settings for tests."""
    return configure_settings()
