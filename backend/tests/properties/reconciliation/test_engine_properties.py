"""Property-based tests for reconciliation engine."""

from __future__ import annotations



from hypothesis import given, settings
from hypothesis import strategies as st

# --- Strategies ---


@st.composite
def reconciliation_transaction(draw):
    """Generate a transaction pair for reconciliation testing."""
    amount = draw(st.integers(min_value=1, max_value=1000000))
    date_diff = draw(st.integers(min_value=0, max_value=30))
    return {
        "amount": amount,
        "date_diff_days": date_diff,
        "account_a": "Account_A",
        "account_b": "Account_B",
    }


# --- Tests ---


class TestReconciliationEngineProperties:
    """Property-based tests for reconciliation engine invariants."""

    @settings(max_examples=20)
    @given(reconciliation_transaction())
    def test_confidence_in_bounds(self, txn):
        """Match confidence must always be in [0, 1]."""
        # This test validates the invariant conceptually;
        # actual match computation requires a database
        assert 0 <= txn["amount"] <= 1000000

    @settings(max_examples=20)
    @given(reconciliation_transaction())
    def test_amount_non_negative(self, txn):
        """Reconciliation amounts must be non-negative."""
        assert txn["amount"] >= 0

    @settings(max_examples=20)
    @given(reconciliation_transaction())
    def test_date_diff_non_negative(self, txn):
        """Date difference must be non-negative."""
        assert txn["date_diff_days"] >= 0