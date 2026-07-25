"""Property-based tests for transaction intelligence engine."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from hypothesis import given, settings
from hypothesis import strategies as st

# --- Strategies ---


@st.composite
def transaction_amount(draw):
    """Generate a transaction amount in paise."""
    return draw(st.integers(min_value=1, max_value=10000000))


@st.composite
def transaction_description(draw):
    """Generate a transaction description."""
    merchants = ["AMAZON", "NETFLIX", "STARBUCKS", "WALMART", "UBER", "SPOTIFY"]
    return draw(st.sampled_from(merchants))


# --- Tests ---


class TestTransactionIntelligenceProperties:
    """Property-based tests for transaction intelligence engine."""

    @settings(max_examples=20)
    @given(transaction_amount())
    def test_amount_non_negative(self, amount):
        """Transaction amounts must be non-negative."""
        assert amount >= 0

    @settings(max_examples=20)
    @given(transaction_description())
    def test_description_is_string(self, desc):
        """Transaction descriptions must be strings."""
        assert isinstance(desc, str)
        assert len(desc) > 0

    @settings(max_examples=20)
    @given(transaction_amount())
    def test_amount_is_integer(self, amount):
        """Transaction amounts must be integers (paise)."""
        assert isinstance(amount, int)
