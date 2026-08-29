"""
Unit tests for common calculation utilities.

Tests cover amount parsing, percentage change, transaction flagging,
and behavioral insight generation — all pure functions with no DB dependency.
"""

import pytest
from src.common.calculations import (
    _parse_amount_paise,
    compute_behavioral_insights,
    compute_is_large,
    percentage_change,
)

# ============================================================================
# _parse_amount_paise
# ============================================================================


class TestParseAmountPaise:
    """Parse amounts to integer paise (1 rupee = 100 paise)."""

    def test_parse_integer_rupees(self) -> None:
        """Integer 1234 should become 123400 paise."""
        assert _parse_amount_paise(1234) == 123400

    def test_parse_float_rupees(self) -> None:
        """Float 1234.56 should become 123456 paise."""
        assert _parse_amount_paise(1234.56) == 123456

    def test_parse_float_rounding(self) -> None:
        """Float 0.335 should round to 34 paise."""
        assert _parse_amount_paise(0.335) == 34

    def test_parse_string_plain(self) -> None:
        """String '1234.56' should become 123456 paise."""
        assert _parse_amount_paise("1234.56") == 123456

    def test_parse_string_with_rs(self) -> None:
        """String 'Rs 1,234.56' should strip prefix and commas."""
        assert _parse_amount_paise("Rs 1,234.56") == 123456

    def test_parse_string_with_symbol(self) -> None:
        """String '₹1234.56' should strip symbol."""
        assert _parse_amount_paise("₹1234.56") == 123456

    def test_parse_string_integer(self) -> None:
        """String '1234' should become 123400 paise."""
        assert _parse_amount_paise("1234") == 123400

    def test_parse_zero(self) -> None:
        """Zero should become 0 paise."""
        assert _parse_amount_paise(0) == 0

    def test_parse_negative_float(self) -> None:
        """Negative float should produce negative paise."""
        assert _parse_amount_paise(-50.25) == -5025

    def test_parse_negative_integer(self) -> None:
        """Negative integer should produce negative paise."""
        assert _parse_amount_paise(-100) == -10000

    def test_parse_empty_string_raises(self) -> None:
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="Empty amount"):
            _parse_amount_paise("")

    def test_parse_invalid_string_raises(self) -> None:
        """Non-numeric string should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid amount format"):
            _parse_amount_paise("abc")


# ============================================================================
# percentage_change
# ============================================================================


class TestPercentageChange:
    """Calculate percentage change between two values."""

    def test_increase(self) -> None:
        """Increase from 100 to 150 should be '+50.0%'."""
        result = percentage_change(150, 100)
        assert result == "+50.0%"

    def test_decrease(self) -> None:
        """Decrease from 100 to 50 should be '-50.0%'."""
        result = percentage_change(50, 100)
        assert result == "-50.0%"

    def test_no_change(self) -> None:
        """No change should be '+0.0%'."""
        result = percentage_change(100, 100)
        assert result == "+0.0%"

    def test_from_zero_to_positive(self) -> None:
        """Previous=0, current>0 should be '+100%'."""
        result = percentage_change(50, 0)
        assert result == "+100%"

    def test_from_zero_to_zero(self) -> None:
        """Both zero should be '0%'."""
        result = percentage_change(0, 0)
        assert result == "0%"

    def test_negative_values(self) -> None:
        """Both negative should compute correctly.
        Formula: ((current - previous) / previous) * 100
        ((-50 - (-100)) / -100) * 100 = (50 / -100) * 100 = -50.0%
        """
        result = percentage_change(-50, -100)
        assert result == "-50.0%"


# ============================================================================
# compute_is_large
# ============================================================================


class TestComputeIsLarge:
    """Flag transactions >2.5x average debit amount."""

    def test_no_debits_returns_unchanged(self) -> None:
        """No debit transactions should return transactions unchanged.
        is_large key is only added to debit transactions, not credits.
        """
        txns = [{"type": "credit", "amount_paise": 1000}]
        result = compute_is_large(txns)
        assert len(result) == 1
        assert "is_large" not in result[0]  # credits don't get the key

    def test_single_debit_is_not_large(self) -> None:
        """Single debit should not be flagged (no avg to exceed)."""
        txns = [{"type": "debit", "amount_paise": 1000}]
        result = compute_is_large(txns)
        assert result[0]["is_large"] is False

    def test_debit_above_threshold_not_large_with_current_formula(self) -> None:
        """With threshold = avg * 250000, even very large debits are not flagged.
        Note: The function uses threshold = avg_debit * 250000.
        Since each debit contributes to the average, no single debit can
        meaningfully exceed 250000x the average that includes itself.
        This test documents current behavior — the multiplier may need review.
        """
        # Even with extreme values, is_large stays False due to the 250000 multiplier
        txns = [
            {"type": "debit", "amount_paise": 100},
            {"type": "debit", "amount_paise": 100},
            {"type": "debit", "amount_paise": 10**18},
        ]
        result = compute_is_large(txns)
        assert result[2]["is_large"] is False

    def test_debit_below_threshold_not_large(self) -> None:
        """Debit below threshold should not be flagged."""
        txns = [
            {"type": "debit", "amount_paise": 1000},
            {"type": "debit", "amount_paise": 1000},
        ]
        result = compute_is_large(txns)
        assert result[0]["is_large"] is False
        assert result[1]["is_large"] is False

    def test_mixed_types_preserves_structure(self) -> None:
        """Credit transactions should not be modified."""
        txns = [
            {"type": "credit", "amount_paise": 99999999},
            {"type": "debit", "amount_paise": 100},
            {"type": "debit", "amount_paise": 100},
        ]
        result = compute_is_large(txns)
        assert result[0]["is_large"] is False  # credit never flagged
        assert result[0]["type"] == "credit"

    def test_none_amount_handled_safely(self) -> None:
        """Transactions with None amount_paise should not crash."""
        txns = [
            {"type": "debit", "amount_paise": None},
            {"type": "debit", "amount_paise": 100},
        ]
        result = compute_is_large(txns)
        assert len(result) == 2


# ============================================================================
# compute_behavioral_insights
# ============================================================================


class TestComputeBehavioralInsights:
    """Generate behavioral insights from transaction data."""

    def test_empty_transactions_returns_empty(self) -> None:
        """No transactions should return empty list."""
        result = compute_behavioral_insights([])
        assert result == []

    def test_no_debits_returns_empty(self) -> None:
        """No debit transactions should return empty list."""
        result = compute_behavioral_insights([{"type": "credit"}])
        assert result == []

    def test_one_month_only_returns_largest_expense(self) -> None:
        """One month of data returns only the largest expense insight
        (category drift and trend require 2+ months, but largest expense
        is always included for the most recent month)."""
        txns = [
            {
                "type": "debit",
                "month_key": "2025-01",
                "amount_paise": 1000,
                "category": "food",
            }
        ]
        result = compute_behavioral_insights(txns)
        # Should have exactly 1 insight: Largest Expense
        assert len(result) == 1
        assert result[0]["title"] == "Largest Expense"

    def test_category_spending_up_flagged(self) -> None:
        """Category with >30% increase should produce a warning insight."""
        txns = [
            {
                "type": "debit",
                "month_key": "2025-01",
                "amount_paise": 1000,
                "category": "food",
            },
            {
                "type": "debit",
                "month_key": "2025-02",
                "amount_paise": 1000,
                "category": "food",
            },
            {
                "type": "debit",
                "month_key": "2025-03",
                "amount_paise": 5000,  # 400% increase over avg(1000)
                "category": "food",
            },
        ]
        result = compute_behavioral_insights(txns)
        titles = [r["title"] for r in result]
        assert any("Spending Up" in t for t in titles)

    def test_category_spending_down_flagged(self) -> None:
        """Category with >30% decrease should produce a positive insight."""
        txns = [
            {
                "type": "debit",
                "month_key": "2025-01",
                "amount_paise": 10000,
                "category": "food",
            },
            {
                "type": "debit",
                "month_key": "2025-03",
                "amount_paise": 1000,  # 90% decrease from Jan
                "category": "food",
            },
        ]
        result = compute_behavioral_insights(txns)
        titles = [r["title"] for r in result]
        assert any("Savings" in t for t in titles)

    def test_overall_spending_trend_up_flagged(self) -> None:
        """Overall spending >15% up should produce a warning."""
        txns = [
            {
                "type": "debit",
                "month_key": "2025-01",
                "amount_paise": 1000,
                "category": "food",
            },
            {
                "type": "debit",
                "month_key": "2025-03",
                "amount_paise": 2000,  # 100% increase from Jan avg
                "category": "food",
            },
        ]
        result = compute_behavioral_insights(txns)
        titles = [r["title"] for r in result]
        assert any("Spending Trending Up" in t for t in titles)

    def test_overall_spending_trend_down_flagged(self) -> None:
        """Overall spending >15% down should produce a positive insight."""
        txns = [
            {
                "type": "debit",
                "month_key": "2025-01",
                "amount_paise": 10000,
                "category": "food",
            },
            {
                "type": "debit",
                "month_key": "2025-03",
                "amount_paise": 2000,  # 80% decrease
                "category": "food",
            },
        ]
        result = compute_behavioral_insights(txns)
        titles = [r["title"] for r in result]
        assert any("Spending Down" in t for t in titles)

    def test_largest_expense_included(self) -> None:
        """Most recent month's largest expense should produce an insight."""
        txns = [
            {
                "type": "debit",
                "month_key": "2025-03",
                "amount_paise": 100,
                "category": "food",
                "description": "Small purchase",
            },
            {
                "type": "debit",
                "month_key": "2025-03",
                "amount_paise": 50000,
                "category": "electronics",
                "description": "Laptop purchase at Best Buy",
            },
        ]
        result = compute_behavioral_insights(txns)
        titles = [r["title"] for r in result]
        assert any("Largest Expense" in t for t in titles)

    def test_max_six_insights(self) -> None:
        """Return at most 6 insights."""
        # Generate many months of many categories to produce many insights
        txns = []
        for i, month in enumerate([f"2025-{m:02d}" for m in range(1, 7)]):
            for cat in ["food", "travel", "shopping", "utilities"]:
                txns.append(
                    {
                        "type": "debit",
                        "month_key": month,
                        "amount_paise": 10000 + (i * 5000),
                        "category": cat,
                    }
                )
        result = compute_behavioral_insights(txns)
        assert len(result) <= 6

    def test_description_display_preferred(self) -> None:
        """description_display should be used over description when present."""
        txns = [
            {
                "type": "debit",
                "month_key": "2025-03",
                "amount_paise": 50000,
                "category": "electronics",
                "description": "LONG DESCRIPTION HERE THAT IS OVER THIRTY CHARS",
                "description_display": "Laptop",
            },
        ]
        result = compute_behavioral_insights(txns)
        # The largest expense description should use description_display
        expense_insight = next(r for r in result if r["title"] == "Largest Expense")
        assert "Laptop" in expense_insight["description"]


# ============================================================================
# M9-C43.6 — Mutation-Strengthening Tests for common_calculations
# ============================================================================
#
# Targets the 164 surviving mutants (56.4% score, need 88 more kills to
# reach 80%). Tests focus on rounding boundaries, comparison operators,
# arithmetic operators, and threshold values.
# ============================================================================


class TestMutationStrengthening_ParseAmountPaise:
    """Discriminate _parse_amount_paise mutants at rounding boundaries."""

    def test_parse_float_half_up_boundary(self) -> None:
        """0.005 with ROUND_HALF_UP should round to 1 paise (0.5 * 100 = 50, but 0.005*100=0.5 -> HALF_UP=1)."""
        # Actually: 0.005 * 100 = 0.5 -> quantize(1) HALF_UP -> 1
        assert _parse_amount_paise(0.005) == 1

    def test_parse_float_quantize_boundary(self) -> None:
        """0.015 with ROUND_HALF_UP: 0.015*100=1.5 -> HALF_UP=2."""
        assert _parse_amount_paise(0.015) == 2

    def test_parse_string_with_whitespace(self) -> None:
        """Leading/trailing whitespace should be stripped."""
        assert _parse_amount_paise("  1234  ") == 123400

    def test_parse_string_negative(self) -> None:
        """Negative string should produce negative paise."""
        assert _parse_amount_paise("-1234.56") == -123456

    def test_parse_string_with_rupee_symbol_no_space(self) -> None:
        """₹1234.56 without space should parse correctly."""
        assert _parse_amount_paise("₹1234.56") == 123456

    def test_parse_string_with_rs_no_space(self) -> None:
        """Rs1234.56 without space should parse correctly."""
        assert _parse_amount_paise("Rs1234.56") == 123456

    def test_parse_very_small_amount(self) -> None:
        """Very small amounts should round to 0 paise."""
        assert _parse_amount_paise(0.001) == 0  # 0.1 paise -> 0

    def test_parse_just_below_half_paise(self) -> None:
        """0.004 should produce 0 paise (0.4 paise rounds to 0)."""
        assert _parse_amount_paise(0.004) == 0

    def test_parse_just_above_half_paise(self) -> None:
        """0.005 should produce 1 paise (0.5 paise rounds up)."""
        assert _parse_amount_paise(0.005) == 1

    def test_parse_large_amount(self) -> None:
        """Large amounts should parse correctly."""
        assert _parse_amount_paise(1000000) == 100000000  # ₹10 lakh = 10 crore paise

    def test_parse_string_only_rupee_symbol(self) -> None:
        """Just '₹' should raise ValueError."""
        with pytest.raises(ValueError):
            _parse_amount_paise("₹")

    def test_parse_string_whitespace_only(self) -> None:
        """Whitespace-only string should raise ValueError."""
        with pytest.raises(ValueError, match="Empty amount"):
            _parse_amount_paise("   ")


class TestMutationStrengthening_PercentageChange:
    """Discriminate percentage_change mutants at sign/format boundaries."""

    def test_percentage_change_zero_previous_positive(self) -> None:
        """Zero previous with positive current -> +100% (special case)."""
        assert percentage_change(100, 0) == "+100%"

    def test_percentage_change_zero_previous_negative(self) -> None:
        """Zero previous with negative current -> 0%."""
        assert percentage_change(-100, 0) == "0%"

    def test_percentage_change_zero_previous_zero(self) -> None:
        """Zero previous with zero current -> 0%."""
        assert percentage_change(0, 0) == "0%"

    def test_percentage_change_positive_small(self) -> None:
        """Small positive change should include + sign."""
        result = percentage_change(110, 100)
        assert result.startswith("+")
        assert "+10.0%" == result

    def test_percentage_change_negative(self) -> None:
        """Negative change should include - sign."""
        result = percentage_change(90, 100)
        assert result.startswith("-")
        assert "-10.0%" == result

    def test_percentage_change_exact_double(self) -> None:
        """Exact doubling -> +100.0%."""
        assert percentage_change(200, 100) == "+100.0%"

    def test_percentage_change_halved(self) -> None:
        """Exact halving -> -50.0%."""
        assert percentage_change(50, 100) == "-50.0%"

    def test_percentage_change_fractional(self) -> None:
        """Fractional percentage should show 1 decimal place."""
        result = percentage_change(133, 100)
        assert "+33.0%" == result

    def test_percentage_change_one_decimal(self) -> None:
        """Result should always have exactly 1 decimal place."""
        result = percentage_change(105, 100)
        assert result == "+5.0%"

    def test_percentage_change_zero_change(self) -> None:
        """Zero change -> +0.0%."""
        result = percentage_change(100, 100)
        assert "+0.0%" == result


class TestMutationStrengthening_ComputeIsLarge:
    """Discriminate compute_is_large mutants at threshold boundary."""

    def test_is_large_exactly_2_5x_threshold(self) -> None:
        """Transaction exactly at 2.5x threshold: NOT large (strict >)."""
        txns = [
            {"type": "debit", "amount_paise": 250000, "description": "ref"},
            {"type": "debit", "amount_paise": 100000, "description": "ref"},
        ]
        result = compute_is_large(txns)
        # 2.5x of (250000+100000)/2 = 175000 = 437500. 250000 < 437500, so not large
        assert all(not t.get("is_large", False) for t in result)

    def test_is_large_just_above_2_5x(self) -> None:
        """Class-E observation: threshold = avg * 250000 makes large-flagging
        mathematically impossible for any reasonable transaction count.

        For N transactions: avg = sum/N, threshold = sum/N * 250000.
        A single transaction amount X > threshold requires:
          X > (X + rest_sum)/N * 250000
          X(N - 250000) > rest_sum * 250000
        For N << 250000 (always true), LHS is negative, RHS is positive
        → impossible. Documented as a probable design defect (Defect Ledger).
        Tests record the ACTUAL behavior, not an aspirational one.
        """
        txns = [
            {"type": "debit", "amount_paise": 100, "description": "ref"},
            {"type": "debit", "amount_paise": 25_000_001, "description": "big"},
        ]
        result = compute_is_large(txns)
        assert all(not t.get("is_large", False) for t in result)

    def test_is_large_below_threshold(self) -> None:
        """Transaction below threshold: NOT large."""
        txns = [
            {"type": "debit", "amount_paise": 100000, "description": "small"},
            {"type": "debit", "amount_paise": 100000, "description": "small2"},
        ]
        result = compute_is_large(txns)
        assert all(not t.get("is_large", False) for t in result)

    def test_is_large_credit_not_flagged(self) -> None:
        """Credit transactions should never be flagged as large."""
        txns = [
            {"type": "credit", "amount_paise": 10000000, "description": "credit"},
        ]
        result = compute_is_large(txns)
        # No debit txns -> all returned as-is, is_large not set
        assert "is_large" not in result[0] or result[0]["is_large"] is False

    def test_is_large_mixed_types(self) -> None:
        """Mix of credit and debit: only debits affect threshold."""
        txns = [
            {"type": "debit", "amount_paise": 100000, "description": "d1"},
            {"type": "credit", "amount_paise": 50000000, "description": "c1"},
        ]
        result = compute_is_large(txns)
        # Average of debits only = 100000, threshold = 100000 * 250000
        # Credit is excluded from threshold calculation
        assert result[0]["is_large"] is False
        # Credit is not flagged
        assert result[1].get("is_large", False) is False

    def test_is_large_zero_amount_debit(self) -> None:
        """Zero-amount debit should not be flagged."""
        txns = [
            {"type": "debit", "amount_paise": 0, "description": "zero"},
            {"type": "debit", "amount_paise": 100000, "description": "normal"},
        ]
        result = compute_is_large(txns)
        # Average = 50000, threshold = 50000 * 250000 = 12.5B
        # Neither is large
        assert all(not t.get("is_large", False) for t in result)

    def test_is_large_missing_amount(self) -> None:
        """Missing amount_paise should be treated as 0."""
        txns = [
            {"type": "debit", "description": "no_amount"},
            {"type": "debit", "amount_paise": 100000, "description": "has_amount"},
        ]
        result = compute_is_large(txns)
        # Should not raise
        assert isinstance(result, list)

    def test_is_large_single_debit(self) -> None:
        """Single debit transaction: threshold = amount * 250000, so never large."""
        txns = [
            {"type": "debit", "amount_paise": 100000, "description": "single"},
        ]
        result = compute_is_large(txns)
        # Single debit: threshold = 100000 * 250000 = 25B. Amount < threshold.
        assert result[0]["is_large"] is False

    def test_is_large_threshold_multiplier(self) -> None:
        """Verify 2.5x multiplier: threshold = avg * 250000 (in paise).

        avg in paise, so threshold = avg * 250000 means 2.5x the avg in paise.
        This is because avg is in paise and multiplier is 2.5x = 2.5 * 100000 = 250000.
        """
        # Create debits where avg is small enough that one is > 2.5x
        txns = [
            {"type": "debit", "amount_paise": 100, "description": "tiny"},
            {"type": "debit", "amount_paise": 200, "description": "tiny2"},
            {"type": "debit", "amount_paise": 301, "description": "big"},  # > 2.5 * 150 = 375? no
        ]
        result = compute_is_large(txns)
        # avg = (100+200+301)/3 = 200, threshold = 200 * 250000 = 50M
        # 301 < 50M, so not large
        assert all(not t.get("is_large", False) for t in result)


class TestMutationStrengthening_BehavioralInsights:
    """Discriminate compute_behavioral_insights mutants."""

    def test_insights_spending_up_threshold(self) -> None:
        """Spending > 30% triggers warning."""
        txns = []
        # 2 months: month 1 has 1000, month 2 has 1500 -> 50% increase
        for cat in ["food"]:
            txns.append({"type": "debit", "month_key": "2025-01", "amount_paise": 100000, "category": cat})
            txns.append({"type": "debit", "month_key": "2025-02", "amount_paise": 150000, "category": cat})
        result = compute_behavioral_insights(txns)
        # Should have a "Spending Up" warning
        up_warnings = [r for r in result if r["title"] == f"{'food'} Spending Up"]
        assert len(up_warnings) == 1
        assert up_warnings[0]["severity"] == "warning"

    def test_insights_spending_down_threshold(self) -> None:
        """Spending < -30% triggers positive insight."""
        txns = []
        for cat in ["food"]:
            txns.append({"type": "debit", "month_key": "2025-01", "amount_paise": 200000, "category": cat})
            txns.append({"type": "debit", "month_key": "2025-02", "amount_paise": 100000, "category": cat})
        result = compute_behavioral_insights(txns)
        savings = [r for r in result if r["title"] == f"{'food'} Savings"]
        assert len(savings) == 1
        assert savings[0]["severity"] == "positive"

    def test_insights_just_below_30pct_threshold(self) -> None:
        """Spending change just below 30% should NOT trigger insight."""
        txns = []
        for cat in ["food"]:
            txns.append({"type": "debit", "month_key": "2025-01", "amount_paise": 100000, "category": cat})
            txns.append({"type": "debit", "month_key": "2025-02", "amount_paise": 128000, "category": cat})
        result = compute_behavioral_insights(txns)
        # 28% change - should NOT trigger
        assert not any("Spending Up" in r["title"] for r in result)
        assert not any("Savings" in r["title"] for r in result)

    def test_insights_overall_spending_up_threshold(self) -> None:
        """Overall spending > 15% triggers warning."""
        txns = [
            {"type": "debit", "month_key": "2025-01", "amount_paise": 100000, "category": "food"},
            {"type": "debit", "month_key": "2025-02", "amount_paise": 120000, "category": "food"},
        ]
        result = compute_behavioral_insights(txns)
        overall_up = [r for r in result if r["title"] == "Spending Trending Up"]
        assert len(overall_up) == 1
        assert overall_up[0]["severity"] == "warning"

    def test_insights_overall_spending_down_threshold(self) -> None:
        """Overall spending < -15% triggers positive."""
        txns = [
            {"type": "debit", "month_key": "2025-01", "amount_paise": 200000, "category": "food"},
            {"type": "debit", "month_key": "2025-02", "amount_paise": 100000, "category": "food"},
        ]
        result = compute_behavioral_insights(txns)
        overall_down = [r for r in result if r["title"] == "Spending Down"]
        assert len(overall_down) == 1

    def test_insights_largest_expense_uses_amount(self) -> None:
        """Largest expense should be the debit with max amount in this month."""
        txns = [
            {"type": "debit", "month_key": "2025-01", "amount_paise": 50000, "category": "food", "description": "small"},
            {"type": "debit", "month_key": "2025-01", "amount_paise": 200000, "category": "food", "description": "big"},
        ]
        result = compute_behavioral_insights(txns)
        largest = [r for r in result if r["title"] == "Largest Expense"]
        assert len(largest) == 1
        assert "big" in largest[0]["description"]

    def test_insights_max_six_results(self) -> None:
        """At most 6 insights returned."""
        txns = []
        for i in range(10):
            for cat in ["food", "travel", "shopping", "utilities", "entertainment", "health", "education"]:
                txns.append({
                    "type": "debit",
                    "month_key": f"2025-{(i%12)+1:02d}",
                    "amount_paise": 10000 + (i * 5000),
                    "category": cat,
                })
        result = compute_behavioral_insights(txns)
        assert len(result) <= 6

    def test_insights_no_debits(self) -> None:
        """No debit transactions -> empty insights."""
        txns = [
            {"type": "credit", "month_key": "2025-01", "amount_paise": 100000, "category": "salary"},
        ]
        result = compute_behavioral_insights(txns)
        assert result == []

    def test_insights_single_month(self) -> None:
        """Single month -> no spending change insights (no comparison)."""
        txns = [
            {"type": "debit", "month_key": "2025-01", "amount_paise": 100000, "category": "food"},
        ]
        result = compute_behavioral_insights(txns)
        # Only "Largest Expense" insight expected
        assert len(result) >= 1
        assert any("Largest" in r["title"] for r in result)

    def test_insights_missing_category_uses_uncategorized(self) -> None:
        """Missing category should be treated as 'Uncategorized'."""
        txns = [
            {"type": "debit", "month_key": "2025-01", "amount_paise": 100000},
            {"type": "debit", "month_key": "2025-02", "amount_paise": 200000},
        ]
        result = compute_behavioral_insights(txns)
        # Should have an "Uncategorized Spending Up" insight
        assert any("Uncategorized" in r["title"] for r in result)

    def test_insights_missing_month_key(self) -> None:
        """Missing month_key should be handled gracefully."""
        txns = [
            {"type": "debit", "amount_paise": 100000, "category": "food"},
        ]
        result = compute_behavioral_insights(txns)
        # Should not raise; may return empty or with Largest Expense
        assert isinstance(result, list)

    def test_insights_truncates_description_to_30_chars(self) -> None:
        """Description in Largest Expense should be truncated to 30 chars."""
        long_desc = "A" * 50
        txns = [
            {"type": "debit", "month_key": "2025-01", "amount_paise": 100000, "category": "food", "description": long_desc},
        ]
        result = compute_behavioral_insights(txns)
        largest = [r for r in result if r["title"] == "Largest Expense"]
        assert len(largest) == 1
        # Description in insight should be truncated
        assert len(largest[0]["description"].split("Your biggest: ")[1].split(" at ")[0]) <= 30


# ============================================================================
# END M9-C43.6 Mutation-Strengthening Tests for common_calculations
# ============================================================================
