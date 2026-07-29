"""Property-based tests for reconciliation engine."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st
from src.engines.reconciliation_engine import (
    _calculate_confidence,
    _date_difference_days,
    _simple_description_similarity,
    _check_match,
)

# --- Strategies ---

@st.composite
def date_pair(draw):
    """Generate a pair of dates with controlled difference."""
    base_date = "2023-01-01"
    days_diff = draw(st.integers(min_value=0, max_value=30))
    return base_date, f"2023-01-{days_diff + 1:02d}"

@st.composite
def transaction_pair(draw):
    """Generate a pair of transactions for reconciliation testing."""
    amount = draw(st.integers(min_value=1, max_value=1000000))
    date_a, date_b = draw(date_pair())
    account_a = draw(st.text(min_size=1, max_size=10, alphabet="abc123"))
    account_b = draw(st.text(min_size=1, max_size=10, alphabet="abc123").filter(lambda x: x != account_a))

    # Ensure different accounts
    if account_a == account_b:
        account_b = account_a + "_2"

    return {
        "id": 1,
        "date_iso": date_a,
        "description": "Test transfer",
        "debit": amount,
        "credit": 0,
        "account_id": account_a,
    }, {
        "id": 2,
        "date_iso": date_b,
        "description": "Test transfer",
        "debit": 0,
        "credit": amount,
        "account_id": account_b,
    }

@st.composite
def matching_transaction_pair(draw):
    """Generate a pair of transactions that should match."""
    txn_a, txn_b = draw(transaction_pair())
    # Ensure date difference is within 3 days (default window)
    date_a = txn_a["date_iso"]
    date_b = f"2023-01-{min(int(date_a[-2:]) + draw(st.integers(min_value=0, max_value=3)), 31):02d}"
    txn_b["date_iso"] = date_b
    return txn_a, txn_b

@st.composite
def non_matching_transaction_pair(draw):
    """Generate a pair of transactions that should not match."""
    txn_a, txn_b = draw(transaction_pair())
    # Make amounts different
    txn_b["credit"] = txn_a["debit"] + draw(st.integers(min_value=1, max_value=1000))
    return txn_a, txn_b

# --- Tests for Utility Functions ---

@settings(max_examples=50)
@given(date_pair())
def test_date_difference_days(date_pair):
    """Date difference calculation must be deterministic and non-negative."""
    date_a, date_b = date_pair
    diff = _date_difference_days(date_a, date_b)
    assert diff is not None
    assert diff >= 0
    assert diff <= 30  # Based on our date_pair strategy

@settings(max_examples=50)
@given(st.text(), st.text())
def test_description_similarity_bounds(desc_a, desc_b):
    """Description similarity must be in [0, 1]."""
    similarity = _simple_description_similarity(desc_a, desc_b)
    assert 0.0 <= similarity <= 1.0

@settings(max_examples=50)
@given(
    st.integers(min_value=0, max_value=30),  # date_diff_days
    st.booleans(),  # amount_exact
    st.floats(min_value=0.0, max_value=1.0),  # description_similarity
)
def test_confidence_calculation_bounds(date_diff_days, amount_exact, description_similarity):
    """Confidence must be in [0, 1] and deterministic."""
    confidence = _calculate_confidence(
        date_diff_days=date_diff_days,
        amount_exact=amount_exact,
        description_similarity=description_similarity,
    )
    assert 0.0 <= confidence <= 1.0
    assert isinstance(confidence, float)

# --- Tests for Matching Logic ---

@settings(max_examples=50)
@given(matching_transaction_pair())
def test_matching_transactions_have_confidence(txn_pair):
    """Transactions that match should have non-zero confidence."""
    txn_a, txn_b = txn_pair
    match = _check_match(txn_a, txn_b)
    assert match is not None
    assert match["match_confidence"] > 0.0
    assert match["match_confidence"] <= 1.0

@settings(max_examples=50)
@given(non_matching_transaction_pair())
def test_non_matching_transactions_no_match(txn_pair):
    """Transactions that don't match should return None."""
    txn_a, txn_b = txn_pair
    match = _check_match(txn_a, txn_b)
    assert match is None

@settings(max_examples=50)
@given(matching_transaction_pair())
def test_exact_date_matches_have_higher_confidence(txn_pair):
    """Exact date matches should have higher confidence than window matches."""
    txn_a, txn_b = txn_pair

    # Test exact date match
    txn_b["date_iso"] = txn_a["date_iso"]
    exact_match = _check_match(txn_a, txn_b)
    assert exact_match is not None
    assert exact_match["match_type"] == "exact"

    # Test window match
    txn_b["date_iso"] = "2023-01-02"  # 1 day difference
    window_match = _check_match(txn_a, txn_b)
    assert window_match is not None
    assert window_match["match_type"] == "window"

    # Exact match should have higher confidence
    assert exact_match["match_confidence"] >= window_match["match_confidence"]

@settings(max_examples=50)
@given(matching_transaction_pair())
def test_same_account_no_match(txn_pair):
    """Transactions from the same account should not match."""
    txn_a, txn_b = txn_pair
    txn_b["account_id"] = txn_a["account_id"]  # Same account
    match = _check_match(txn_a, txn_b)
    assert match is None

@settings(max_examples=50)
@given(matching_transaction_pair())
def test_deterministic_key_consistency(txn_pair):
    """Deterministic key should be consistent for the same transaction pair."""
    txn_a, txn_b = txn_pair

    # Test multiple times with same transactions
    match1 = _check_match(txn_a, txn_b)
    match2 = _check_match(txn_a, txn_b)

    assert match1 is not None
    assert match2 is not None
    assert match1["deterministic_key"] == match2["deterministic_key"]

    # Test with order reversed
    match_reversed = _check_match(txn_b, txn_a)
    assert match_reversed is not None
    assert match_reversed["deterministic_key"] == match1["deterministic_key"]

# --- Tests for Confidence Calculation ---

@settings(max_examples=50)
@given(st.integers(min_value=0, max_value=30))
def test_confidence_date_factors(date_diff_days):
    """Test date-related confidence factors."""
    confidence = _calculate_confidence(
        date_diff_days=date_diff_days,
        amount_exact=True,
        description_similarity=0.0,
    )

    if date_diff_days == 0:
        assert confidence == 0.8  # 0.4 (date) + 0.4 (amount)
    elif date_diff_days == 1:
        assert confidence == 0.7  # 0.3 (date) + 0.4 (amount)
    else:
        # Should be 0.4 (amount only) since date_diff_days > 1
        assert confidence == 0.4

@settings(max_examples=50)
@given(st.floats(min_value=0.0, max_value=1.0))
def test_confidence_description_factors(description_similarity):
    """Test description similarity confidence factors."""
    confidence = _calculate_confidence(
        date_diff_days=0,
        amount_exact=True,
        description_similarity=description_similarity,
    )

    if description_similarity > 0.7:
        assert confidence == 1.0  # 0.4 (date) + 0.4 (amount) + 0.2 (description) = 1.0 (capped)
    else:
        assert confidence == 0.8  # 0.4 (date) + 0.4 (amount)

def test_confidence_capping():
    """Confidence should be capped at 1.0."""
    confidence = _calculate_confidence(
        date_diff_days=0,
        amount_exact=True,
        description_similarity=1.0,  # Should trigger all factors
    )
    assert confidence == 1.0  # Capped at 1.0
