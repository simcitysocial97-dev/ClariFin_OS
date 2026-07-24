"""Tests for Behaviour Engine Phase 4 — Income Intelligence metrics.

Tests cover:
- Income source classification (SALARY, BUSINESS, INVESTMENT, TRANSFER, REFUND, BORROWING, UNKNOWN)
- Salary dependence ratio calculation
- Income diversification score

All tests verify:
- Determinism (same input → same output)
- Edge cases (empty inputs, zero values, missing data)
"""

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.behaviour_engine import (
    classify_income_source,
    compute_income_diversification_score,
    compute_salary_dependence_ratio,
    compute_true_income_total,
    filter_true_income,
)

# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def salary_transactions() -> list[dict[str, Any]]:
    """Sample salary income transactions."""
    return [
        {"description": "Salary credit", "amount_paise": 5000000},
        {"description": "PAYROLL transfer", "amount_paise": 4500000},
        {"description": "Professional fees - salaried", "amount_paise": 500000},
    ]


@pytest.fixture
def diversified_transactions() -> list[dict[str, Any]]:
    """Sample diversified income transactions (salary + investment)."""
    return [
        {"description": "Salary credit", "amount_paise": 5000000},
        {"description": "Dividend from stocks", "amount_paise": 100000},
        {"description": "Mutual fund interest", "amount_paise": 50000},
    ]


@pytest.fixture
def mixed_transactions() -> list[dict[str, Any]]:
    """Mixed income transactions including non-true income."""
    return [
        {"description": "Salary credit", "amount_paise": 5000000},
        {"description": "Transfer to own account", "amount_paise": 100000},
        {"description": "Loan from bank", "amount_paise": 500000},
        {"description": "Refund from Amazon", "amount_paise": 2000},
        {"description": "Business consulting income", "amount_paise": 200000},
        {"description": "Dividend from stocks", "amount_paise": 50000},  # Added investment
    ]


# ============================================================
# Tests: classify_income_source
# ============================================================

class TestClassifyIncomeSource:
    """Tests for income source classification."""

    def test_salary_classification(self):
        """Test SALARY classification."""
        txn = {"description": "Salary credit for April"}
        category, confidence = classify_income_source(txn)
        assert category == "salary"
        assert confidence >= 0.8

    def test_salary_salaried_match(self):
        """Test SALARY classification for salaried."""
        txn = {"description": "Salaried employee payment"}
        category, confidence = classify_income_source(txn)
        assert category == "salary"

    def test_business_classification(self):
        """Test BUSINESS classification."""
        txn = {"description": "Freelance consulting payment"}
        category, confidence = classify_income_source(txn)
        assert category == "business"

    def test_business_commission(self):
        """Test BUSINESS classification for commission."""
        txn = {"description": "Sales commission received"}
        category, confidence = classify_income_source(txn)
        assert category == "business"

    def test_investment_classification(self):
        """Test INVESTMENT classification."""
        txn = {"description": "Dividend from stocks"}
        category, confidence = classify_income_source(txn)
        assert category == "investment"

    def test_investment_interest(self):
        """Test INVESTMENT classification for interest income."""
        txn = {"description": "Fixed deposit interest income"}
        category, confidence = classify_income_source(txn)
        assert category == "investment"

    def test_investment_mutual_fund(self):
        """Test INVESTMENT classification for mutual fund."""
        txn = {"description": "Mutual fund returns"}
        category, confidence = classify_income_source(txn)
        assert category == "investment"

    def test_transfer_classification(self):
        """Test TRANSFER classification."""
        txn = {"description": "Transfer to own account"}
        category, confidence = classify_income_source(txn)
        assert category == "transfer"

    def test_refund_classification(self):
        """Test REFUND classification."""
        txn = {"description": "Refund from Amazon purchase"}
        category, confidence = classify_income_source(txn)
        assert category == "refund"

    def test_refund_cashback(self):
        """Test REFUND classification for cashback."""
        txn = {"description": "Cashback reward credited"}
        category, confidence = classify_income_source(txn)
        assert category == "refund"

    def test_borrowing_classification(self):
        """Test BORROWING classification."""
        txn = {"description": "Loan from bank credited"}
        category, confidence = classify_income_source(txn)
        assert category == "borrowing"

    def test_unknown_classification(self):
        """Test UNKNOWN classification for no matching keywords."""
        txn = {"description": "XYZ Corporation payment"}
        category, confidence = classify_income_source(txn)
        assert category == "unknown"

    def test_empty_description(self):
        """Test UNKNOWN classification for empty description."""
        txn = {"description": ""}
        category, confidence = classify_income_source(txn)
        assert category == "unknown"
        assert confidence == 0.0

    def test_whole_word_confidence(self):
        """Test that whole-word match gets confidence 1.0."""
        txn = {"description": "Salary credit"}
        category, confidence = classify_income_source(txn)
        assert category == "salary"
        assert confidence == 1.0  # "salary" is a whole word

    def test_partial_word_confidence(self):
        """Test that partial match gets confidence 0.8."""
        txn = {"description": "Salarycredited"}  # No space
        category, confidence = classify_income_source(txn)
        assert category == "salary"
        assert confidence == 0.8  # Partial match (substring in larger word)

    def test_classify_deterministic(self):
        """Test that classification is deterministic."""
        txn = {"description": "Salary credit"}
        for _ in range(10):
            category, confidence = classify_income_source(txn)
            assert category == "salary"
            assert confidence == 1.0


# ============================================================
# Tests: compute_salary_dependence_ratio
# ============================================================

class TestSalaryDependenceRatio:
    """Tests for salary dependence ratio calculation."""

    def test_full_dependence(self):
        """Test 100% salary dependence."""
        result = compute_salary_dependence_ratio(5000000, 5000000)
        assert result == Decimal('1.0')

    def test_partial_dependence(self):
        """Test partial salary dependence."""
        result = compute_salary_dependence_ratio(2500000, 5000000)
        assert result == Decimal('0.5')

    def test_low_dependence(self):
        """Test low salary dependence (diversified income)."""
        result = compute_salary_dependence_ratio(1000000, 5000000)
        assert result == Decimal('0.2')

    def test_zero_salary(self):
        """Test zero salary dependence."""
        result = compute_salary_dependence_ratio(0, 5000000)
        assert result == Decimal('0')

    def test_zero_true_income(self):
        """Test with zero true income returns 0."""
        result = compute_salary_dependence_ratio(5000000, 0)
        assert result == Decimal('0')

    def test_both_zero(self):
        """Test with both zero returns 0."""
        result = compute_salary_dependence_ratio(0, 0)
        assert result == Decimal('0')

    def test_salary_exceeds_true_income(self):
        """Test when salary exceeds true income (shouldn't happen, but handle gracefully)."""
        result = compute_salary_dependence_ratio(6000000, 5000000)
        assert result == Decimal('1.2')

    def test_salary_dependence_deterministic(self):
        """Test determinism of salary dependence ratio."""
        for _ in range(10):
            result = compute_salary_dependence_ratio(3000000, 4000000)
            assert result == Decimal('0.75')


# ============================================================
# Tests: compute_income_diversification_score
# ============================================================

class TestIncomeDiversificationScore:
    """Tests for income diversification score."""

    def test_no_transactions(self):
        """Test empty transactions returns 0."""
        result = compute_income_diversification_score([])
        assert result == Decimal('0')

    def test_single_source_salary_only(self, salary_transactions):
        """Test single source (salary only) returns ~0.33."""
        result = compute_income_diversification_score(salary_transactions)
        assert result == Decimal('0.3333')  # Only "salary" category, 1/3

    def test_two_sources_salary_investment(self, diversified_transactions):
        """Test two sources (salary + investment) returns ~0.67."""
        result = compute_income_diversification_score(diversified_transactions)
        # "salary" and "investment" categories
        assert result == Decimal('0.6667')

    def test_three_sources(self):
        """Test three sources returns 1.0 (capped)."""
        txns = [
            {"description": "Salary credit", "amount_paise": 5000000},
            {"description": "Business income", "amount_paise": 200000},
            {"description": "Dividend from stocks"},
        ]
        result = compute_income_diversification_score(txns)
        assert result == Decimal('1.0')  # All 3 categories = max

    def test_excludes_transfers(self, mixed_transactions):
        """Test that TRANSFER transactions are excluded from diversification."""
        result = compute_income_diversification_score(mixed_transactions)
        # Only salary + business + investment (transfer, loan, refund excluded)
        assert result == Decimal('1.0')  # All 3 categories = max

    def test_excludes_loans(self):
        """Test that BORROWING transactions are excluded from diversification."""
        txns = [
            {"description": "Salary credit"},
            {"description": "Loan from bank credited"},
            {"description": "Investment dividend"},
        ]
        result = compute_income_diversification_score(txns)
        # Only salary + investment (loan excluded) = 2/3
        assert result == Decimal('0.6667')

    def test_excludes_refunds(self):
        """Test that REFUND transactions are excluded from diversification."""
        txns = [
            {"description": "Salary credit"},
            {"description": "Refund from merchant"},
            {"description": "Consulting income"},
        ]
        result = compute_income_diversification_score(txns)
        # Only salary + business (refund excluded) = 2/3
        assert result == Decimal('0.6667')

    def test_diversification_deterministic(self, diversified_transactions):
        """Test that diversification score is deterministic."""
        for _ in range(10):
            result = compute_income_diversification_score(diversified_transactions)
            assert result == Decimal('0.6667')


# ============================================================
# Tests: filter_true_income and compute_true_income_total
# ============================================================

class TestTrueIncomeHelpers:
    """Tests for true income helper functions."""

    def test_filter_true_income(self, mixed_transactions):
        """Test filtering excludes non-true income."""
        filtered = filter_true_income(mixed_transactions)
        assert len(filtered) == 3  # Only salary, business, investment (3 items)
        # Verify each filtered transaction is a true income category
        for txn in filtered:
            category, _ = classify_income_source(txn)
            assert category in {"salary", "business", "investment"}

    def test_compute_true_income_total(self, mixed_transactions):
        """Test true income total excludes non-true income."""
        total = compute_true_income_total(mixed_transactions)
        # Salary + Business + Investment = 5000000 + 200000 + 50000 = 5250000
        assert total == 5250000

    def test_compute_true_income_total_empty(self):
        """Test true income total with empty list."""
        total = compute_true_income_total([])
        assert total == 0

    def test_true_income_total_deterministic(self, mixed_transactions):
        """Test determinism of true income total."""
        for _ in range(10):
            total = compute_true_income_total(mixed_transactions)
            assert total == 5250000


# ============================================================
# Tests: Edge Cases
# ============================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_missing_amount_key(self):
        """Test transactions without amount_paise key."""
        txns = [
            {"description": "Salary credit"},  # No amount
            {"description": "Business payment", "amount_paise": 500000},
        ]
        result = compute_income_diversification_score(txns)
        assert result == Decimal('0.6667')

    def test_missing_description_key(self):
        """Test transactions without description key."""
        txns = [
            {"amount_paise": 500000},  # No description
            {"description": "Dividend income"},
        ]
        result = compute_income_diversification_score(txns)
        assert result == Decimal('0.3333')  # Only investment

    def test_all_non_income_sources(self):
        """Test when all transactions are non-income sources."""
        txns = [
            {"description": "Transfer to own account"},
            {"description": "Loan from bank"},
            {"description": "Cashback reward"},
        ]
        result = compute_income_diversification_score(txns)
        assert result == Decimal('0')

    def test_case_insensitivity(self):
        """Test that classification is case-insensitive."""
        txns = [
            {"description": "SALARY CREDIT"},
            {"description": "Business Payment"},
            {"description": "DIVIDEND Income"},
        ]
        result = compute_income_diversification_score(txns)
        assert result == Decimal('1.0')  # All three categories


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
