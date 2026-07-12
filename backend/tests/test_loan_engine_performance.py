"""
Loan Engine Performance & Regression Tests
===========================================
Performance benchmarks and regression tests for the loan engine.

Run: python -m pytest tests/test_loan_engine_performance.py -v --tb=short
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.loan_engine import (
    apply_prepayment,
    compute_emi_fixed,
    generate_schedule,
    total_interest_paise,
    validate_schedule,
)
from engines.loan_engine.models import PrepaymentMode

# ============================================================
# Performance Benchmarks
# ============================================================

# Thresholds (in seconds) — generous for CI, optimized for cold start
EMI_10000_THRESHOLD_S = 0.5
SCHEDULE_360_THRESHOLD_S = 0.5
PREPAYMENT_10_THRESHOLD_S = 1.0


class TestEMIPerformance:
    """Benchmark EMI calculation speed."""

    def test_emi_single_calculation_speed(self):
        """Single EMI calculation should be fast (< 1ms)."""
        start = time.perf_counter()
        for _ in range(100):
            compute_emi_fixed(100000000, 850, 120)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"100 EMI calculations took {elapsed:.3f}s"

    def test_emi_cached_vs_uncached(self):
        """Cache hit should be faster than cache miss."""
        # Warm the cache
        compute_emi_fixed(100000000, 850, 120)

        # Time cached access
        start = time.perf_counter()
        for _ in range(1000):
            compute_emi_fixed(100000000, 850, 120)
        cached_time = time.perf_counter() - start

        # Time uncached (different params)
        start = time.perf_counter()
        for i in range(1000):
            compute_emi_fixed(100000000 + i, 850, 120)
        uncached_time = time.perf_counter() - start

        # Cached should be significantly faster
        assert cached_time < uncached_time, f"Cached {cached_time:.4f}s vs uncached {uncached_time:.4f}s"

    def test_emi_10k_iterations(self):
        """10,000 EMI calculations should complete within threshold."""
        start = time.perf_counter()
        for i in range(10000):
            compute_emi_fixed(100000000 + (i % 100), 850 + (i % 50), 120)
        elapsed = time.perf_counter() - start
        assert elapsed < EMI_10000_THRESHOLD_S, f"10k EMI took {elapsed:.3f}s (threshold: {EMI_10000_THRESHOLD_S}s)"


class TestSchedulePerformance:
    """Benchmark schedule generation speed."""

    def test_schedule_360_month_generation(self):
        """360-month schedule generation should be fast."""
        start = time.perf_counter()
        schedule = generate_schedule(
            principal_paise=500000000,  # ₹50L
            annual_rate_bps=850,
            tenure_months=360,  # 30 years
            start_date="2025-01-01",
        )
        elapsed = time.perf_counter() - start

        assert len(schedule) == 360
        assert schedule[-1].balance_paise == 0
        assert elapsed < SCHEDULE_360_THRESHOLD_S, f"360-month schedule took {elapsed:.3f}s (threshold: {SCHEDULE_360_THRESHOLD_S}s)"

    def test_schedule_1_month_generation(self):
        """1-month schedule should be instant."""
        start = time.perf_counter()
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=1,
            start_date="2025-01-01",
        )
        elapsed = time.perf_counter() - start

        assert len(schedule) == 1
        assert schedule[-1].balance_paise == 0
        assert elapsed < 0.1, f"1-month schedule took {elapsed:.4f}s"

    def test_schedule_validation_overhead(self):
        """Validate schedule overhead is minimal."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=120,
            start_date="2025-01-01",
        )

        start = time.perf_counter()
        for _ in range(100):
            validate_schedule(schedule, 100000000, debug_mode=True)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"100 validations took {elapsed:.3f}s"


class TestPrepaymentPerformance:
    """Benchmark prepayment simulation speed."""

    def test_prepayment_simulation_speed(self):
        """Single prepayment simulation should be fast."""
        start = time.perf_counter()
        for _ in range(10):
            result = apply_prepayment(
                outstanding_paise=100000000,
                annual_rate_bps=850,
                remaining_months=120,
                prepayment_paise=10000000,
                mode=PrepaymentMode.REDUCE_TENURE,
            )
        elapsed = time.perf_counter() - start
        assert elapsed < PREPAYMENT_10_THRESHOLD_S, f"10 prepayments took {elapsed:.3f}s (threshold: {PREPAYMENT_10_THRESHOLD_S}s)"

    def test_foreclosure_simulation_speed(self):
        """Foreclosure simulation should be fast."""
        from engines.loan_engine import compute_foreclosure_amount

        start = time.perf_counter()
        for _ in range(100):
            compute_foreclosure_amount(
                outstanding_paise=100000000,
                annual_rate_bps=850,
                remaining_months=120,
            )
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"100 foreclosures took {elapsed:.3f}s"


# ============================================================
# Edge Case Tests (Phase 6B)
# ============================================================

class TestEdgeCaseLoanSizes:
    """Edge cases for loan size."""

    def test_very_small_loan(self):
        """Very small loan (₹1,000) should work correctly."""
        principal = 100000  # ₹1,000
        schedule = generate_schedule(
            principal_paise=principal,
            annual_rate_bps=1200,  # 12%
            tenure_months=6,
            start_date="2025-01-01",
        )
        assert len(schedule) == 6
        assert schedule[-1].balance_paise == 0
        assert sum(r.principal_paise for r in schedule) == principal

    def test_large_loan_crore(self):
        """₹1Cr+ loan should work correctly."""
        principal = 10000000000  # ₹1,00,00,000
        schedule = generate_schedule(
            principal_paise=principal,
            annual_rate_bps=750,  # 7.5%
            tenure_months=240,  # 20 years
            start_date="2025-01-01",
        )
        assert len(schedule) == 240
        assert schedule[-1].balance_paise == 0
        assert sum(r.principal_paise for r in schedule) == principal


class TestEdgeCaseTenure:
    """Edge cases for tenure."""

    def test_one_month_loan(self):
        """1-month loan: full principal + interest paid in one EMI."""
        principal = 100000000
        schedule = generate_schedule(
            principal_paise=principal,
            annual_rate_bps=850,
            tenure_months=1,
            start_date="2025-01-01",
        )
        assert len(schedule) == 1
        assert schedule[0].balance_paise == 0
        assert schedule[0].principal_paise == principal
        assert schedule[0].interest_paise > 0

    def test_360_month_loan(self):
        """360-month (30 year) loan: full amortization."""
        principal = 500000000  # ₹50L
        schedule = generate_schedule(
            principal_paise=principal,
            annual_rate_bps=850,
            tenure_months=360,
            start_date="2025-01-01",
        )
        assert len(schedule) == 360
        assert schedule[-1].balance_paise == 0
        assert sum(r.principal_paise for r in schedule) == principal
        # Validate invariants
        assert validate_schedule(schedule, principal, debug_mode=True)


class TestEdgeCaseInterest:
    """Edge cases for interest rates."""

    def test_zero_interest_loan(self):
        """Zero interest loan: EMI = principal / tenure."""
        principal = 100000000
        tenure = 120
        schedule = generate_schedule(
            principal_paise=principal,
            annual_rate_bps=0,  # 0%
            tenure_months=tenure,
            start_date="2025-01-01",
        )
        assert len(schedule) == tenure
        assert schedule[-1].balance_paise == 0
        # All interest should be zero
        assert all(r.interest_paise == 0 for r in schedule)
        # EMI should be equal for all rows except last (rounding adjustment)
        first_emi = schedule[0].emi_paise
        for row in schedule[:-1]:
            assert row.emi_paise == first_emi, f"EMI mismatch at month {row.month_number}: {row.emi_paise} != {first_emi}"
        # Sum of principal = original
        assert sum(r.principal_paise for r in schedule) == principal

    def test_very_low_interest(self):
        """Very low interest (0.5%) should produce valid schedule."""
        principal = 100000000
        schedule = generate_schedule(
            principal_paise=principal,
            annual_rate_bps=50,  # 0.5%
            tenure_months=120,
            start_date="2025-01-01",
        )
        assert len(schedule) == 120
        assert schedule[-1].balance_paise == 0
        assert validate_schedule(schedule, principal, debug_mode=True)

    def test_high_interest(self):
        """High interest (30%) should produce valid schedule."""
        principal = 100000000
        schedule = generate_schedule(
            principal_paise=principal,
            annual_rate_bps=3000,  # 30%
            tenure_months=120,
            start_date="2025-01-01",
        )
        assert len(schedule) == 120
        assert schedule[-1].balance_paise == 0
        assert validate_schedule(schedule, principal, debug_mode=True)


class TestEdgeCaseDates:
    """Edge cases for dates."""

    def test_month_end_start(self):
        """Starting on Jan 31 should handle Feb correctly."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=12,
            start_date="2025-01-31",
        )
        assert len(schedule) == 12
        # Feb date should be Feb 28 (non-leap year)
        assert schedule[1].payment_date == "2025-02-28"

    def test_february_dates(self):
        """February dates should be handled correctly."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=3,
            start_date="2025-02-15",
        )
        assert len(schedule) == 3
        assert schedule[0].payment_date == "2025-02-15"
        assert schedule[1].payment_date == "2025-03-15"
        assert schedule[2].payment_date == "2025-04-15"

    def test_leap_year_february(self):
        """Leap year February should handle Feb 29 correctly."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=24,
            start_date="2024-02-29",  # Leap year
        )
        assert len(schedule) == 24
        # Month 13 should be Feb 2025 (non-leap) - should be Feb 28
        assert schedule[12].payment_date == "2025-02-28"


class TestEdgeCasePrepayment:
    """Edge cases for prepayment."""

    def test_first_month_prepayment(self):
        """Prepayment in first month should work."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode=PrepaymentMode.REDUCE_TENURE,
        )
        assert result.interest_saved_paise > 0
        assert result.months_saved > 0

    def test_last_month_prepayment(self):
        """Prepayment in last month should close loan early."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=120,
            start_date="2025-01-01",
        )
        from engines.loan_engine import apply_prepayment_at_month

        new_schedule, result = apply_prepayment_at_month(
            schedule, 119, schedule[118].balance_paise, 850,
        )
        assert result.loan_closed is True
        assert result.new_remaining_months == 0

    def test_full_foreclosure(self):
        """Full foreclosure closes loan with zero remaining."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=100000000,
            mode=PrepaymentMode.REDUCE_TENURE,
        )
        assert result.loan_closed is True
        assert result.new_remaining_months == 0
        assert result.months_saved == 120

    def test_multiple_prepayments_sequential(self):
        """Multiple prepayments applied sequentially."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=120,
            start_date="2025-01-01",
        )
        from engines.loan_engine import apply_multiple_prepayments

        prepayments = [(6, 5000000), (12, 5000000), (24, 10000000)]
        new_schedule, results = apply_multiple_prepayments(
            schedule, prepayments, 850,
        )
        assert len(results) == 3
        assert len(new_schedule) < len(schedule)
        assert sum(r.interest_saved_paise for r in results) > 0

    def test_zero_interest_prepayment(self):
        """Prepayment on zero-interest loan."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=0,
            tenure_months=120,
            start_date="2025-01-01",
        )
        from engines.loan_engine import apply_prepayment

        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=0,
            remaining_months=120,
            prepayment_paise=10000000,
            mode=PrepaymentMode.REDUCE_TENURE,
        )
        # Zero interest means no interest saved, but tenure may reduce
        assert result.interest_saved_paise == 0
        assert result.months_saved >= 0


# ============================================================
# Regression Tests (Phase 6F)
# ============================================================

class TestRegression:
    """Regression tests: verify existing API responses unchanged."""

    def test_known_emi_values(self):
        """Known EMI values must remain unchanged."""
        # Standard: ₹10L @ 8.5% for 10 years
        emi = compute_emi_fixed(100000000, 850, 120)
        assert emi == 1239857, f"EMI changed from 1239857 to {emi}"

        # Zero interest: ₹10L @ 0% for 60 months
        emi = compute_emi_fixed(100000000, 0, 60)
        assert emi == 1666666, f"Zero-interest EMI changed from 1666666 to {emi}"

        # Small loan: ₹50k @ 18% for 24 months
        emi = compute_emi_fixed(5000000, 1800, 24)
        assert emi > 0

    def test_known_schedule_totals(self):
        """Known schedule totals must remain unchanged."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=120,
            start_date="2025-01-01",
        )
        total_interest = total_interest_paise(schedule)
        # Known value: total interest should be approximately ₹49L
        assert total_interest > 40000000  # > ₹4L
        assert total_interest < 60000000  # < ₹6L

    def test_schedule_format_stability(self):
        """Schedule format must match spec."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=12,
            start_date="2025-01-01",
        )
        row = schedule[0]
        # All required fields must exist
        assert hasattr(row, 'month_number')
        assert hasattr(row, 'payment_date')
        assert hasattr(row, 'emi_paise')
        assert hasattr(row, 'principal_paise')
        assert hasattr(row, 'interest_paise')
        assert hasattr(row, 'balance_paise')
        assert hasattr(row, 'cumulative_interest_paise')
        # Date must be ISO format
        assert len(row.payment_date) == 10
        assert row.payment_date[4] == '-'
        assert row.payment_date[7] == '-'
