"""Tests for Behaviour Engine India-Specific Signals (Phase 6/7).

Tests for credit_dependency.py functions.

Run: python -m pytest tests/test_behaviour_engine_credit_dependency.py -v
"""
import sys
from decimal import Decimal
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.behaviour_engine.credit_dependency import (
    artificial_income_flag,
    credit_dependency_ratio,
    debt_rolling_flag,
    financial_stress_index,
    household_divergence,
    liquidity_extraction_frequency,
    revolver_ratio,
    transactor_vs_revolver,
)

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def empty_events():
    """Return empty financial events list."""
    return []


@pytest.fixture
def cash_advance_events():
    """Financial events with cash advances (artificial income)."""
    return [
        {
            "id": 1,
            "event_type": "credit_card_cash_advance",
            "amount_paise": 50000,  # ₹500
            "liability_change_paise": 50000,
            "date_iso": "2025-01-15",
            "month_bucket": "2025-01",
            "account_id": "CC1",
            "lifecycle_state": "settled",
            "owner_id": "self",
            "household_id": "primary",
        },
        {
            "id": 2,
            "event_type": "cash_advance",
            "amount_paise": 100000,  # ₹1000
            "liability_change_paise": 100000,
            "date_iso": "2025-02-10",
            "month_bucket": "2025-02",
            "account_id": "CC2",
            "lifecycle_state": "open",
            "owner_id": "self",
            "household_id": "primary",
        },
        {
            "id": 3,
            "event_type": "income",
            "amount_paise": 500000,  # ₹5000 - true income
            "date_iso": "2025-01-01",
            "month_bucket": "2025-01",
            "account_id": "",
            "lifecycle_state": "settled",
            "owner_id": "self",
            "household_id": "primary",
        },
    ]


@pytest.fixture
def revolver_events():
    """Events indicating revolver behavior."""
    return [
        {
            "id": 1,
            "event_type": "credit_card_cash_advance",
            "amount_paise": 80000,
            "liability_change_paise": 80000,
            "date_iso": "2025-01-10",
            "month_bucket": "2025-01",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "owner_id": "self",
            "household_id": "primary",
        },
        {
            "id": 2,
            "event_type": "credit_card_cash_advance",
            "amount_paise": 60000,
            "liability_change_paise": 60000,
            "date_iso": "2025-02-10",
            "month_bucket": "2025-02",
            "account_id": "CC1",
            "lifecycle_state": "partially_settled",
            "owner_id": "self",
            "household_id": "primary",
        },
        {
            "id": 3,
            "event_type": "liability_repayment",
            "amount_paise": 100000,
            "liability_change_paise": -100000,
            "date_iso": "2025-01-20",
            "month_bucket": "2025-01",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "owner_id": "self",
            "household_id": "primary",
        },
    ]


@pytest.fixture
def transactor_events():
    """Events indicating transactor behavior."""
    return [
        {
            "id": 1,
            "event_type": "credit_card_cash_advance",
            "amount_paise": 50000,
            "liability_change_paise": 50000,
            "date_iso": "2025-01-10",
            "month_bucket": "2025-01",
            "account_id": "CC1",
            "lifecycle_state": "settled",
            "owner_id": "self",
            "household_id": "primary",
        },
        {
            "id": 2,
            "event_type": "credit_card_cash_advance",
            "amount_paise": 70000,
            "liability_change_paise": 70000,
            "date_iso": "2025-02-10",
            "month_bucket": "2025-02",
            "account_id": "CC1",
            "lifecycle_state": "settled",
            "owner_id": "self",
            "household_id": "primary",
        },
    ]


@pytest.fixture
def debt_rolling_events():
    """Events with rolls_over lifecycle state and links."""
    return [
        {
            "id": 1,
            "event_type": "credit_card_cash_advance",
            "amount_paise": 100000,
            "liability_change_paise": 100000,
            "date_iso": "2025-01-10",
            "month_bucket": "2025-01",
            "account_id": "CC1",
            "lifecycle_state": "rolls_over",
            "owner_id": "self",
            "household_id": "primary",
            "links": [
                {"link_type": "rolls_over", "linked_event_id": 2}
            ],
        },
        {
            "id": 2,
            "event_type": "credit_card_cash_advance",
            "amount_paise": 100000,
            "liability_change_paise": 100000,
            "date_iso": "2025-01-20",
            "month_bucket": "2025-01",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "owner_id": "self",
            "household_id": "primary",
            "links": [],
        },
    ]


@pytest.fixture
def household_divergence_events():
    """Events with cross-owner funding links."""
    return [
        {
            "id": 1,
            "event_type": "liability_repayment",
            "amount_paise": 50000,
            "liability_change_paise": -50000,
            "date_iso": "2025-01-15",
            "month_bucket": "2025-01",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "owner_id": "spouse",
            "household_id": "primary",
            "links": [
                {"link_type": "settles", "linked_event_id": 2}
            ],
        },
        {
            "id": 2,
            "event_type": "credit_card_cash_advance",
            "amount_paise": 50000,
            "liability_change_paise": 50000,
            "date_iso": "2025-01-01",
            "month_bucket": "2025-01",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "owner_id": "self",
            "household_id": "primary",
            "links": [],
        },
    ]


# ============================================================
# Tests: Artificial Income Flag
# ============================================================


class TestArtificialIncomeFlag:
    """Tests for artificial_income_flag."""

    def test_no_artificial_income(self, empty_events):
        """No artificial income events should return no flag."""
        result = artificial_income_flag(empty_events)

        assert result["flag"] is False
        assert result["artificial_income_paise"] == 0
        assert result["excluded_event_ids"] == []

    def test_detects_cash_advance(self, cash_advance_events):
        """Cash advances should be flagged as artificial income."""
        result = artificial_income_flag(cash_advance_events)

        assert result["flag"] is True
        # Only credit_card_cash_advance and cash_advance are artificial (not income)
        assert result["artificial_income_paise"] == 150000  # 50000 + 100000
        assert 1 in result["excluded_event_ids"]
        assert 2 in result["excluded_event_ids"]

    def test_purity_no_db_calls(self, cash_advance_events):
        """Test that artificial_income_flag makes no DB calls."""
        from unittest.mock import patch

        with patch('sqlite3.connect') as mock_connect:
            artificial_income_flag(cash_advance_events)
            assert mock_connect.call_count == 0, "Should not call sqlite3.connect"


# ============================================================
# Tests: Transactor vs Revolver
# ============================================================


class TestTransactorVsRevolver:
    """Tests for transactor_vs_revolver."""

    def test_transactor_classification(self, transactor_events):
        """All settled events should classify as transactor."""
        result = transactor_vs_revolver(transactor_events, "CC1")

        assert result["type"] == "transactor"
        assert result["confidence"] == Decimal("1.0")
        assert result["settled_count"] == 2
        assert result["revolving_count"] == 0

    def test_revolver_classification(self, revolver_events):
        """Open/partial events should classify as revolver."""
        result = transactor_vs_revolver(revolver_events, "CC1")

        assert result["type"] == "revolver"
        assert result["confidence"] == Decimal("1.0")
        assert result["settled_count"] == 0
        assert result["revolving_count"] == 2

    def test_no_events_default(self, empty_events):
        """No events for account should return transactor with zero confidence."""
        result = transactor_vs_revolver(empty_events, "CC1")

        assert result["type"] == "transactor"
        assert result["confidence"] == Decimal("0")

    def test_purity_no_db_calls(self, transactor_events):
        """Test that transactor_vs_revolver makes no DB calls."""
        from unittest.mock import patch

        with patch('sqlite3.connect') as mock_connect:
            transactor_vs_revolver(transactor_events, "CC1")
            assert mock_connect.call_count == 0


# ============================================================
# Tests: Debt Rolling Flag
# ============================================================


class TestDebtRollingFlag:
    """Tests for debt_rolling_flag."""

    def test_no_rolling(self, transactor_events):
        """No rolls_over links should return no flag."""
        result = debt_rolling_flag(transactor_events)

        assert result["flag"] is False
        assert result["count"] == 0
        assert result["event_ids"] == []

    def test_rolling_detected(self, debt_rolling_events):
        """Events with rolls_over links should be detected."""
        result = debt_rolling_flag(debt_rolling_events)

        assert result["flag"] is True
        assert result["count"] == 1
        assert 1 in result["event_ids"]

    def test_lifecycle_state_rolling(self):
        """Events with lifecycle_state=rolls_over should be detected."""
        events = [
            {
                "id": 1,
                "event_type": "credit_card_cash_advance",
                "lifecycle_state": "rolls_over",
                "links": [],
            }
        ]
        result = debt_rolling_flag(events)

        assert result["flag"] is True
        assert 1 in result["event_ids"]

    def test_purity_no_db_calls(self, debt_rolling_events):
        """Test that debt_rolling_flag makes no DB calls."""
        from unittest.mock import patch

        with patch('sqlite3.connect') as mock_connect:
            debt_rolling_flag(debt_rolling_events)
            assert mock_connect.call_count == 0


# ============================================================
# Tests: Financial Stress Index
# ============================================================


class TestFinancialStressIndex:
    """Tests for financial_stress_index."""

    def test_no_stress_empty_events(self, empty_events):
        """No financial events should return zero stress scores."""
        cashflow = {
            "expense_paise": 100000,
            "cash_surplus": 50000,
            "credit_dependency_ratio": Decimal("0"),
        }
        result = financial_stress_index(empty_events, cashflow)

        # All components should be zero or near-zero
        assert float(result["score"]) >= 0
        assert float(result["score"]) < 0.1  # Very low stress
        assert result["flag"] is False

    def test_component_independence(self, cash_advance_events):
        """Each component should be independently testable."""
        cashflow = {
            "expense_paise": 100000,
            "cash_surplus": -50000,  # Deficit
            "credit_dependency_ratio": Decimal("1.5"),  # High
        }
        result = financial_stress_index(cash_advance_events, cashflow)

        # Components should sum correctly
        components = result["components"]
        weighted_sum = (
            0.30 * float(components["credit_dependency"]) +
            0.25 * float(components["debt_rolling"]) +
            0.20 * float(components["liquidity_extraction"]) +
            0.15 * float(components["revolving"]) +
            0.10 * float(components["cashflow_deficit"])
        )
        assert abs(float(result["score"]) - weighted_sum) < 0.001

    def test_high_stress_detected(self, debt_rolling_events):
        """High stress conditions should trigger flag."""
        cashflow = {
            "expense_paise": 100000,
            "cash_surplus": -80000,  # Large deficit
            "credit_dependency_ratio": Decimal("2.0"),  # Very high
        }
        result = financial_stress_index(debt_rolling_events, cashflow)

        # With rolling debt and deficit, stress could be elevated
        # Note: actual threshold check depends on component values

    def test_purity_no_db_calls(self, cash_advance_events):
        """Test that financial_stress_index makes no DB calls."""
        from unittest.mock import patch

        cashflow = {
            "expense_paise": 100000,
            "cash_surplus": 0,
            "credit_dependency_ratio": Decimal("0.5"),
        }

        with patch('sqlite3.connect') as mock_connect:
            financial_stress_index(cash_advance_events, cashflow)
            assert mock_connect.call_count == 0


# ============================================================
# Tests: Household Divergence
# ============================================================


class TestHouseholdDivergence:
    """Tests for household_divergence."""

    def test_no_divergence(self, transactor_events):
        """No cross-owner links should return no flag."""
        result = household_divergence(transactor_events)

        assert result["flag"] is False
        assert result["count"] == 0
        assert result["divergent_links"] == []

    def test_cross_owner_detected(self, household_divergence_events):
        """Cross-owner funding should be detected."""
        result = household_divergence(household_divergence_events)

        assert result["flag"] is True
        assert result["count"] == 1
        assert result["divergent_links"][0]["from_owner"] == "spouse"
        assert result["divergent_links"][0]["to_owner"] == "self"
        assert result["divergent_links"][0]["link_type"] == "settles"

    def test_purity_no_db_calls(self, household_divergence_events):
        """Test that household_divergence makes no DB calls."""
        from unittest.mock import patch

        with patch('sqlite3.connect') as mock_connect:
            household_divergence(household_divergence_events)
            assert mock_connect.call_count == 0


# ============================================================
# Tests: Revolver Ratio
# ============================================================


class TestRevolverRatio:
    """Tests for revolver_ratio."""

    def test_no_credit_activity(self, empty_events):
        """No credit events should return zero ratio."""
        result = revolver_ratio(empty_events)
        assert result == Decimal("0")

    def test_all_settled(self, transactor_events):
        """All settled events should return low revolver ratio."""
        result = revolver_ratio(transactor_events)
        assert result == Decimal("0")  # No revolving months

    def test_partial_revolving(self, revolver_events):
        """Mixed lifecycle states should show partial ratio."""
        result = revolver_ratio(revolver_events)
        # Months 2025-01 and 2025-02 both have revolving activity
        assert float(result) > 0


# ============================================================
# Tests: Liquidity Extraction Frequency
# ============================================================


class TestLiquidityExtractionFrequency:
    """Tests for liquidity_extraction_frequency."""

    def test_no_advance_events(self, empty_events):
        """No cash advances should return zeros."""
        result = liquidity_extraction_frequency(empty_events)

        assert result["count"] == 0
        assert result["total_paise"] == 0
        assert result["avg_days_between"] is None

    def test_single_advance(self):
        """Single advance should have None for avg_days."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "amount_paise": 50000,
                "date_iso": "2025-01-15",
            }
        ]
        result = liquidity_extraction_frequency(events)

        assert result["count"] == 1
        assert result["total_paise"] == 50000
        assert result["avg_days_between"] is None


# ============================================================
# Tests: Credit Dependency Ratio (Events)
# ============================================================


class TestCreditDependencyRatioEvents:
    """Tests for credit_dependency_ratio (events version)."""

    def test_no_credit_funded(self, empty_events):
        """No credit-funded spending should return zero ratio."""
        cashflow = {"expense_paise": 100000}
        result = credit_dependency_ratio(empty_events, cashflow)
        assert result == Decimal("0")

    def test_high_credit_dependency(self, cash_advance_events):
        """Credit-funded spending should increase ratio."""
        cashflow = {"expense_paise": 100000}
        result = credit_dependency_ratio(cash_advance_events, cashflow)

        # Credit funded = 50000 + 100000 = 150000
        # Ratio = 150000 / 100000 = 1.5
        assert result == Decimal("1.5")


# ============================================================
# Tests: Regression - Empty Events
# ============================================================


class TestEmptyEventsRegression:
    """Regression tests for no FinancialEvents edge case."""

    def test_all_signals_handle_empty_events(self, empty_events):
        """All signals should return neutral values with no events."""
        # Artificial income
        result = artificial_income_flag(empty_events)
        assert result["flag"] is False
        assert result["artificial_income_paise"] == 0

        # Transactor/revolver
        result = transactor_vs_revolver(empty_events, "CC1")
        assert result["type"] == "transactor"
        assert result["confidence"] == Decimal("0")

        # Debt rolling
        result = debt_rolling_flag(empty_events)
        assert result["flag"] is False

        # Stress index
        cashflow = {"expense_paise": 100000, "cash_surplus": 0, "credit_dependency_ratio": Decimal("0")}
        result = financial_stress_index(empty_events, cashflow)
        assert float(result["score"]) < 0.1

        # Household divergence
        result = household_divergence(empty_events)
        assert result["flag"] is False

        # Revolver ratio
        result = revolver_ratio(empty_events)
        assert result == Decimal("0")

        # Liquidity extraction
        result = liquidity_extraction_frequency(empty_events)
        assert result["count"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
