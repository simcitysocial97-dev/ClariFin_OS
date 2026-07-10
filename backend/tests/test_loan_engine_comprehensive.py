"""
Comprehensive Loan Engine Tests
===============================
Tests for the complete loan engine including prepayment, refinance, health scoring, and tax benefits.

Run: python -m pytest tests/test_loan_engine_comprehensive.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.loan_engine.amortization_builder import (
    generate_schedule,
    total_interest_paise,
    total_payment_paise,
)
from engines.loan_engine.comparison_engine import (
    compare_loans,
    compare_prepayment_scenarios,
    generate_loan_summary,
)
from engines.loan_engine.dynamic_prepayment_engine import (
    apply_floating_rate_change,
    apply_multiple_prepayments,
    apply_prepayment_at_month,
    simulate_floating_rate_schedule,
)
from engines.loan_engine.health_scorer import (
    compute_health_score,
    get_health_insights,
    get_health_recommendations,
)
from engines.loan_engine.payoff_strategies import (
    compare_payoff_strategies,
    compute_minimum_payments_only,
    compute_snowball_timeline,
)
from engines.loan_engine.prepayment_analyzer import (
    apply_prepayment,
    compute_multiple_prepayment_savings,
    compute_savings,
)
from engines.loan_engine.refinance_evaluator import (
    compare_refinance_options,
    evaluate_refinance,
)
from engines.loan_engine.tax_calculator import (
    compare_tax_regimes,
    compute_annual_benefits,
    compute_total_lifetime_tax_savings,
)
from engines.loan_engine.types import (
    FloatingRateChange,
    InterestType,
    LoanInfo,
    PrepaymentMode,
)

# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def sample_loan():
    """Standard loan: ₹10L at 8.5% for 10 years."""
    return {
        "principal_paise": 100000000,  # ₹10,00,000
        "annual_rate_bps": 850,  # 8.5%
        "tenure_months": 120,  # 10 years
        "start_date": "2025-01-01",
    }

@pytest.fixture
def sample_loan_info():
    """LoanInfo object for testing."""
    return LoanInfo(
        loan_id=1,
        outstanding_paise=100000000,  # ₹10,00,000
        annual_rate_bps=850,  # 8.5%
        remaining_months=120,  # 10 years
        emi_paise=123960,  # Approx ₹12,396
        start_date="2025-01-01",
        name="Home Loan",
        lender="SBI",
        interest_type=InterestType.FIXED,
    )

@pytest.fixture
def sample_schedule(sample_loan):
    """Generated schedule for sample loan."""
    return generate_schedule(**sample_loan)

@pytest.fixture
def multiple_loans():
    """Multiple loans for payoff strategy testing."""
    return [
        LoanInfo(
            loan_id=1,
            outstanding_paise=50000000,  # ₹5,00,000
            annual_rate_bps=1000,  # 10%
            remaining_months=60,  # 5 years
            emi_paise=10623,  # Approx ₹10,623
            start_date="2025-01-01",
            name="Personal Loan",
            lender="HDFC",
        ),
        LoanInfo(
            loan_id=2,
            outstanding_paise=30000000,  # ₹3,00,000
            annual_rate_bps=1200,  # 12%
            remaining_months=36,  # 3 years
            emi_paise=10053,  # Approx ₹10,053
            start_date="2025-01-01",
            name="Car Loan",
            lender="ICICI",
        ),
        LoanInfo(
            loan_id=3,
            outstanding_paise=20000000,  # ₹2,00,000
            annual_rate_bps=1800,  # 18%
            remaining_months=24,  # 2 years
            emi_paise=9985,  # Approx ₹9,985
            start_date="2025-01-01",
            name="Credit Card",
            lender="Axis",
        ),
    ]

# ============================================================
# Prepayment Analyzer Tests
# ============================================================

class TestPrepaymentAnalyzer:
    """Tests for prepayment analyzer functionality."""

    def test_single_prepayment_reduce_tenure(self, sample_loan_info):
        """Single prepayment reduces tenure correctly."""
        result = apply_prepayment(
            outstanding_paise=sample_loan_info.outstanding_paise,
            annual_rate_bps=sample_loan_info.annual_rate_bps,
            remaining_months=sample_loan_info.remaining_months,
            prepayment_paise=10000000,  # ₹1,00,000
            mode="reduce_tenure",
        )

        assert result.months_saved > 0
        assert result.interest_saved_paise > 0
        assert result.new_remaining_months < sample_loan_info.remaining_months
        assert result.loan_closed is False

    def test_single_prepayment_reduce_emi(self, sample_loan_info):
        """Single prepayment reduces EMI correctly."""
        result = apply_prepayment(
            outstanding_paise=sample_loan_info.outstanding_paise,
            annual_rate_bps=sample_loan_info.annual_rate_bps,
            remaining_months=sample_loan_info.remaining_months,
            prepayment_paise=10000000,  # ₹1,00,000
            mode="reduce_emi",
        )

        assert result.months_saved == 0  # Tenure stays same
        assert result.new_emi_paise < sample_loan_info.emi_paise
        assert result.interest_saved_paise > 0

    def test_full_foreclosure(self, sample_loan_info):
        """Full foreclosure closes loan."""
        result = apply_prepayment(
            outstanding_paise=sample_loan_info.outstanding_paise,
            annual_rate_bps=sample_loan_info.annual_rate_bps,
            remaining_months=sample_loan_info.remaining_months,
            prepayment_paise=sample_loan_info.outstanding_paise,  # Full amount
            mode="reduce_tenure",
        )

        assert result.loan_closed is True
        assert result.new_remaining_months == 0
        assert result.months_saved == sample_loan_info.remaining_months

    def test_multiple_prepayments(self, sample_schedule, sample_loan):
        """Multiple prepayments work correctly."""
        prepayments = [(6, 5000000), (12, 3000000)]  # ₹50k at month 6, ₹30k at month 12

        new_schedule, results = apply_multiple_prepayments(
            sample_schedule,
            prepayments,
            sample_loan["annual_rate_bps"],
        )

        assert len(results) == 2
        assert len(new_schedule) < len(sample_schedule)
        assert total_interest_paise(new_schedule) < total_interest_paise(sample_schedule)

    def test_prepayment_with_penalty(self, sample_loan_info):
        """Prepayment with penalty reduces savings."""
        result_with_penalty = apply_prepayment(
            outstanding_paise=sample_loan_info.outstanding_paise,
            annual_rate_bps=sample_loan_info.annual_rate_bps,
            remaining_months=sample_loan_info.remaining_months,
            prepayment_paise=10000000,  # ₹1,00,000
            mode="reduce_tenure",
            prepayment_penalty_bps=200,  # 2% penalty
        )

        result_without_penalty = apply_prepayment(
            outstanding_paise=sample_loan_info.outstanding_paise,
            annual_rate_bps=sample_loan_info.annual_rate_bps,
            remaining_months=sample_loan_info.remaining_months,
            prepayment_paise=10000000,  # ₹1,00,000
            mode="reduce_tenure",
            prepayment_penalty_bps=0,  # No penalty
        )

        assert result_with_penalty.interest_saved_paise < result_without_penalty.interest_saved_paise

# ============================================================
# Payoff Strategies Tests
# ============================================================

class TestPayoffStrategies:
    """Tests for debt payoff strategies."""

    def test_snowball_strategy(self, multiple_loans):
        """Snowball strategy works correctly."""
        result = compute_snowball_timeline(
            loans=multiple_loans,
            monthly_surplus_paise=2000000,  # ₹20,000
            strategy="snowball",
        )

        assert result.strategy == "snowball"
        assert result.total_months < 60  # Should be less than longest loan
        assert len(result.loan_results) == 3
        assert len(result.monthly_cash_flow) == result.total_months

    def test_avalanche_strategy(self, multiple_loans):
        """Avalanche strategy works correctly."""
        result = compute_snowball_timeline(
            loans=multiple_loans,
            monthly_surplus_paise=2000000,  # ₹20,000
            strategy="avalanche",
        )

        assert result.strategy == "avalanche"
        assert result.total_months < 60  # Should be less than longest loan
        assert len(result.loan_results) == 3

    def test_minimum_payments(self, multiple_loans):
        """Minimum payments baseline works correctly."""
        result = compute_minimum_payments_only(multiple_loans)

        assert result.strategy == "minimum"
        assert result.total_months == 60  # Longest loan duration
        assert len(result.loan_results) == 3

    def test_strategy_comparison(self, multiple_loans):
        """Strategy comparison returns all three strategies."""
        results = compare_payoff_strategies(
            loans=multiple_loans,
            monthly_surplus_paise=2000000,  # ₹20,000
        )

        assert "minimum" in results
        assert "snowball" in results
        assert "avalanche" in results

        # Avalanche should save more interest than snowball
        assert results["avalanche"].total_interest_paise <= results["snowball"].total_interest_paise

# ============================================================
# Refinance Evaluator Tests
# ============================================================

class TestRefinanceEvaluator:
    """Tests for refinance evaluation."""

    def test_refinance_beneficial(self):
        """Refinance with lower rate is beneficial."""
        result = evaluate_refinance(
            current_outstanding_paise=100000000,  # ₹10,00,000
            current_rate_bps=1000,  # 10%
            remaining_months=120,  # 10 years
            current_emi_paise=132150,  # Approx ₹13,215
            new_rate_bps=850,  # 8.5%
            new_tenure_months=120,  # 10 years
            processing_fees_paise=2000000,  # ₹20,000
            prepayment_penalty_paise=1000000,  # ₹10,000
        )

        assert result.is_beneficial is True
        assert result.emi_savings_paise > 0
        assert result.break_even_months < result.remaining_months

    def test_refinance_not_beneficial(self):
        """Refinance with higher rate is not beneficial."""
        result = evaluate_refinance(
            current_outstanding_paise=100000000,  # ₹10,00,000
            current_rate_bps=850,  # 8.5%
            remaining_months=120,  # 10 years
            current_emi_paise=123960,  # Approx ₹12,396
            new_rate_bps=1000,  # 10%
            new_tenure_months=120,  # 10 years
            processing_fees_paise=2000000,  # ₹20,000
        )

        assert result.is_beneficial is False
        assert result.emi_savings_paise < 0
        assert result.break_even_months == 999

    def test_refinance_with_tax_benefits(self):
        """Refinance with tax benefits calculation."""
        result = evaluate_refinance(
            current_outstanding_paise=100000000,  # ₹10,00,000
            current_rate_bps=1000,  # 10%
            remaining_months=120,  # 10 years
            current_emi_paise=132150,  # Approx ₹13,215
            new_rate_bps=850,  # 8.5%
            new_tenure_months=120,  # 10 years
            processing_fees_paise=2000000,  # ₹20,000
            tax_rate_bps=2000,  # 20%
        )

        assert result.gross_savings_paise > 0
        assert result.tax_benefit_difference_paise >= 0
        assert result.net_savings_paise > 0

    def test_compare_refinance_options(self):
        """Compare multiple refinance options."""
        current_loan = {
            "current_outstanding_paise": 100000000,
            "current_rate_bps": 1000,
            "remaining_months": 120,
            "current_emi_paise": 132150,
        }

        options = [
            {
                "new_rate_bps": 850,
                "new_tenure_months": 120,
                "processing_fees_paise": 2000000,
            },
            {
                "new_rate_bps": 900,
                "new_tenure_months": 120,
                "processing_fees_paise": 1500000,
            },
        ]

        results = compare_refinance_options(current_loan, options)

        assert len(results) == 2
        assert results[0].is_beneficial is True
        assert results[1].is_beneficial is True
        assert results[0].net_savings_paise > results[1].net_savings_paise

# ============================================================
# Health Scorer Tests
# ============================================================

class TestHealthScorer:
    """Tests for loan health scoring."""

    def test_health_score_calculation(self):
        """Health score calculation works correctly."""
        result = compute_health_score(
            monthly_emi_paise=2000000,  # ₹20,000
            monthly_income_paise=10000000,  # ₹1,00,000
            sanction_amount_paise=50000000,  # ₹5,00,000
            outstanding_paise=30000000,  # ₹3,00,000
            missed_payments=1,
            total_payments=12,
            months_since_start=6,
            credit_score=750,
            ltv_ratio=0.6,
        )

        assert 0 <= result.overall_score <= 100
        assert 0 <= result.dti_score <= 100
        assert 0 <= result.utilization_score <= 100
        assert 0 <= result.stress_score <= 100
        assert 0 <= result.payment_score <= 100
        assert 0 <= result.credit_score <= 100

    def test_high_dti_clamping(self):
        """High DTI is clamped to prevent negative scores."""
        result = compute_health_score(
            monthly_emi_paise=5000000,  # ₹50,000
            monthly_income_paise=10000000,  # ₹1,00,000
            sanction_amount_paise=50000000,
            outstanding_paise=30000000,
            missed_payments=0,
            total_payments=12,
            months_since_start=6,
        )

        # DTI = 50% (above MAX_DTI of 40%), should be clamped
        assert result.dti_score == 0.0

    def test_health_recommendations(self):
        """Health recommendations are generated."""
        result = compute_health_score(
            monthly_emi_paise=3000000,  # ₹30,000
            monthly_income_paise=10000000,  # ₹1,00,000
            sanction_amount_paise=50000000,
            outstanding_paise=45000000,  # High utilization
            missed_payments=2,
            total_payments=12,
            months_since_start=6,
            credit_score=600,
            ltv_ratio=0.85,
        )

        recommendations = get_health_recommendations(result)
        insights = get_health_insights(result)

        assert len(recommendations) > 0
        assert len(insights) > 0
        assert "prepayment" in " ".join(recommendations).lower()
        assert "high ltv" in " ".join(recommendations).lower()

# ============================================================
# Tax Calculator Tests
# ============================================================

class TestTaxCalculator:
    """Tests for tax benefit calculations."""

    def test_section_24_benefit(self):
        """Section 24 benefit calculation."""
        from engines.loan_engine.tax_calculator import compute_section_24_benefit

        # ₹2,50,000 interest (above old limit, below new limit)
        benefit_old = compute_section_24_benefit(
            interest_paise=25000000,  # ₹2,50,000
            is_new_regime=False,
        )

        benefit_new = compute_section_24_benefit(
            interest_paise=25000000,  # ₹2,50,000
            is_new_regime=True,
        )

        # New regime has higher limit (₹3,00,000 vs ₹2,00,000)
        assert benefit_new > benefit_old
        assert benefit_old == 4000000  # ₹40,000 (20% of ₹2,00,000)
        assert benefit_new == 5000000  # ₹50,000 (20% of ₹2,50,000)

    def test_section_80c_benefit(self):
        """Section 80C benefit calculation."""
        from engines.loan_engine.tax_calculator import compute_section_80c_benefit

        # ₹1,00,000 principal repayment (below limit)
        benefit = compute_section_80c_benefit(
            principal_paise=10000000,  # ₹1,00,000
        )

        assert benefit == 2000000  # ₹20,000 (20% of ₹1,00,000)

        # With other 80C investments
        benefit_with_other = compute_section_80c_benefit(
            principal_paise=10000000,  # ₹1,00,000
            other_80c_investments_paise=10000000,  # ₹1,00,000
        )

        assert benefit_with_other == 1000000  # ₹10,000 (20% of remaining ₹50,000)

    def test_total_lifetime_tax_savings(self, sample_loan):
        """Total lifetime tax savings calculation."""
        result = compute_total_lifetime_tax_savings(
            principal_paise=sample_loan["principal_paise"],
            annual_rate_bps=sample_loan["annual_rate_bps"],
            tenure_months=sample_loan["tenure_months"],
            start_date=sample_loan["start_date"],
            is_self_occupied=True,
            is_first_time_buyer=True,
            property_value_paise=500000000,  # ₹50,00,000
        )

        assert result.total_benefit_paise > 0
        assert result.section_24_benefit_paise > 0
        assert result.section_80c_benefit_paise > 0
        assert result.section_80ee_benefit_paise > 0  # First-time buyer

    def test_tax_regime_comparison(self, sample_loan):
        """Tax regime comparison works."""
        results = compare_tax_regimes(
            principal_paise=sample_loan["principal_paise"],
            annual_rate_bps=sample_loan["annual_rate_bps"],
            tenure_months=sample_loan["tenure_months"],
            start_date=sample_loan["start_date"],
            is_self_occupied=True,
            is_first_time_buyer=True,
            property_value_paise=500000000,  # ₹50,00,000
        )

        assert "old_regime" in results
        assert "new_regime" in results
        assert results["new_regime"].total_benefit_paise > results["old_regime"].total_benefit_paise

# ============================================================
# Dynamic Prepayment Engine Tests
# ============================================================

class TestDynamicPrepaymentEngine:
    """Tests for dynamic prepayment engine."""

    def test_apply_prepayment_at_month(self, sample_schedule):
        """Apply prepayment at specific month."""
        new_schedule, result = apply_prepayment_at_month(
            schedule=sample_schedule,
            prepayment_month=12,
            prepayment_paise=10000000,  # ₹1,00,000
            annual_rate_bps=850,
        )

        assert len(new_schedule) < len(sample_schedule)
        assert result.months_saved > 0
        assert result.interest_saved_paise > 0
        assert new_schedule[11].balance_paise < sample_schedule[11].balance_paise

    def test_floating_rate_change(self, sample_schedule):
        """Floating rate change works correctly."""
        # Increase rate at month 12
        new_schedule = apply_floating_rate_change(
            schedule=sample_schedule,
            change_month=12,
            new_rate_bps=950,  # 9.5%
            mode="adjust_emi",
        )

        assert len(new_schedule) == len(sample_schedule)
        assert new_schedule[11].emi_paise != sample_schedule[11].emi_paise

    def test_floating_rate_tenure_adjustment(self, sample_schedule):
        """Floating rate change with tenure adjustment."""
        # Increase rate at month 12, keep EMI same
        new_schedule = apply_floating_rate_change(
            schedule=sample_schedule,
            change_month=12,
            new_rate_bps=950,  # 9.5%
            mode="adjust_tenure",
        )

        assert len(new_schedule) > len(sample_schedule)
        assert new_schedule[11].emi_paise == sample_schedule[11].emi_paise

    def test_simulate_floating_rate_schedule(self):
        """Simulate schedule with multiple rate changes."""
        rate_changes = [
            FloatingRateChange(change_month=12, new_rate_bps=900, mode="adjust_emi"),
            FloatingRateChange(change_month=24, new_rate_bps=850, mode="adjust_emi"),
        ]

        schedule = simulate_floating_rate_schedule(
            principal_paise=100000000,  # ₹10,00,000
            initial_rate_bps=850,
            tenure_months=120,
            rate_changes=rate_changes,
        )

        assert len(schedule) == 120
        # EMI should change at month 12 and 24
        assert schedule[11].emi_paise != schedule[12].emi_paise
        assert schedule[23].emi_paise != schedule[24].emi_paise

# ============================================================
# Comparison Engine Tests
# ============================================================

class TestComparisonEngine:
    """Tests for loan comparison engine."""

    def test_compare_loans(self):
        """Compare multiple loan options."""
        loan1 = LoanInfo(
            loan_id=1,
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            emi_paise=123960,
            start_date="2025-01-01",
            interest_type=InterestType.FIXED,
        )

        loan2 = LoanInfo(
            loan_id=2,
            outstanding_paise=100000000,
            annual_rate_bps=900,
            remaining_months=120,
            emi_paise=126675,
            start_date="2025-01-01",
            interest_type=InterestType.FIXED,
        )

        results = compare_loans(
            loan_options=[loan1, loan2],
            monthly_income_paise=100000000,  # ₹10,00,000
            sanction_amount_paise=100000000,
        )

        assert len(results) == 2
        assert results[0].is_best is True  # Lower rate should be best
        assert results[1].is_best is False
        assert results[0].total_cost_paise < results[1].total_cost_paise

    def test_compare_prepayment_scenarios(self, sample_loan_info):
        """Compare different prepayment scenarios."""
        scenarios = [
            [],  # No prepayments
            [(6, 5000000)],  # ₹50,000 at month 6
            [(6, 5000000), (12, 3000000)],  # ₹50k at 6, ₹30k at 12
        ]

        results = compare_prepayment_scenarios(
            loan=sample_loan_info,
            scenarios=scenarios,
            monthly_income_paise=100000000,  # ₹10,00,000
            sanction_amount_paise=100000000,
        )

        assert len(results) == 3
        assert results[0].total_cost_paise > results[1].total_cost_paise
        assert results[1].total_cost_paise > results[2].total_cost_paise
        assert results[2].is_best is True

    def test_generate_loan_summary(self, sample_loan_info):
        """Generate loan summary with health score."""
        summary = generate_loan_summary(
            loan=sample_loan_info,
            monthly_income_paise=100000000,  # ₹10,00,000
            sanction_amount_paise=100000000,
        )

        assert summary.loan_id == sample_loan_info.loan_id
        assert summary.health_score is not None
        assert 0 <= summary.health_score <= 100
        assert summary.loan_type == "fixed"

# ============================================================
# Edge Case Tests
# ============================================================

class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_zero_prepayment(self, sample_loan_info):
        """Zero prepayment should raise error."""
        with pytest.raises(ValueError, match="Prepayment amount must be positive"):
            apply_prepayment(
                outstanding_paise=sample_loan_info.outstanding_paise,
                annual_rate_bps=sample_loan_info.annual_rate_bps,
                remaining_months=sample_loan_info.remaining_months,
                prepayment_paise=0,
            )

    def test_invalid_prepayment_month(self, sample_schedule):
        """Invalid prepayment month should raise error."""
        with pytest.raises(ValueError, match="out of range"):
            apply_prepayment_at_month(
                schedule=sample_schedule,
                prepayment_month=121,  # Beyond schedule length
                prepayment_paise=10000000,
                annual_rate_bps=850,
            )

    def test_invalid_rate_change_month(self, sample_schedule):
        """Invalid rate change month should raise error."""
        with pytest.raises(ValueError, match="out of range"):
            apply_floating_rate_change(
                schedule=sample_schedule,
                change_month=121,  # Beyond schedule length
                new_rate_bps=950,
            )

    def test_negative_rate(self, sample_schedule):
        """Negative rate should raise error."""
        with pytest.raises(ValueError, match="Rate cannot be negative"):
            apply_floating_rate_change(
                schedule=sample_schedule,
                change_month=12,
                new_rate_bps=-100,
            )

    def test_empty_loan_list(self):
        """Empty loan list should return empty result."""
        result = compute_snowball_timeline([], 1000000)
        assert result.total_months == 0
        assert result.total_interest_paise == 0
        assert len(result.loan_results) == 0

    def test_single_loan_payoff(self, sample_loan_info):
        """Single loan payoff should work."""
        result = compute_snowball_timeline([sample_loan_info], 10000000, "snowball")
        assert result.total_months > 0
        assert len(result.loan_results) == 1
        assert result.loan_results[0].loan_id == sample_loan_info.loan_id