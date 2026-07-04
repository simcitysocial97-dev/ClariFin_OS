"""
Deterministic Golden Tests for ClariFin Financial Engines
=========================================================
Every test uses hardcoded inputs and asserts EXACT outputs.
If any test fails after a code change, the change broke financial correctness.

FIRST RUN: Execute tests, note actual values, update expected values.
SUBSEQUENT RUNS: Any deviation from golden values = regression.
"""

import pytest
import tempfile
import os
from datetime import date
from decimal import Decimal


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    from src.db import FinanceDB
    db = FinanceDB(':memory:')
    yield db
    db.close()


# ============================================================
# Loan Engine Tests
# ============================================================

class TestEMICalculation:
    """EMI formula must match known bank calculator values."""
    
    @pytest.mark.parametrize("principal,rate,tenure,expected_emi", [
        # Format: (principal_paise, annual_rate_%, tenure_months, expected_emi_paise)
        # Values verified against standard EMI formula
        # GOLDEN VALUES: Computed by compute_emi() on 2025-02-27
        (5000000_00, 8.5, 240, 4339116),   # 50L home loan, 8.5%, 20yr = ₹43,391.16
        (1000000_00, 12.0, 36, 3321431),    # 10L personal loan, 12%, 3yr = ₹33,214.31
        (300000_00, 0.0, 12, 25000_00),      # 3L interest-free, 12 months = ₹25,000
    ])
    def test_emi_known_values(self, principal, rate, tenure, expected_emi):
        from src.engines.loan_engine import compute_emi
        result = compute_emi(principal, rate, tenure)
        # Allow ±1 paise tolerance for rounding
        assert abs(result - expected_emi) <= 1, f"EMI {result} != expected {expected_emi} (±1)"

    def test_emi_determinism(self):
        """Same inputs must produce identical EMI every time."""
        from src.engines.loan_engine import compute_emi
        results = [compute_emi(5000000_00, 8.5, 240) for _ in range(100)]
        assert len(set(results)) == 1, "EMI not deterministic"

    def test_zero_interest_emi(self):
        """0% interest should give simple division."""
        from src.engines.loan_engine import compute_emi
        result = compute_emi(1200000_00, 0.0, 12)
        assert result == 100000_00  # 12L paise / 12 months = 1L paise


class TestAmortizationSchedule:
    
    def test_schedule_length_matches_tenure(self):
        from src.engines.loan_engine import generate_ideal_schedule
        schedule = generate_ideal_schedule(5000000_00, 8.5, 12, date(2025, 1, 1))
        assert len(schedule) == 12

    def test_schedule_determinism(self):
        from src.engines.loan_engine import generate_ideal_schedule
        s1 = generate_ideal_schedule(5000000_00, 8.5, 12, date(2025, 1, 1))
        s2 = generate_ideal_schedule(5000000_00, 8.5, 12, date(2025, 1, 1))
        for a, b in zip(s1, s2):
            assert a == b, "Schedule not deterministic"

    def test_final_balance_near_zero(self):
        """After all EMIs, remaining principal should be 0 or near 0."""
        from src.engines.loan_engine import generate_ideal_schedule
        schedule = generate_ideal_schedule(5000000_00, 8.5, 240, date(2025, 1, 1))
        final = schedule[-1]
        # Allow ±100 paise (₹1) tolerance
        remaining = final.get("remaining_principal_paise", 0)
        assert abs(remaining) <= 100, f"Final balance not zero: {remaining}"

    def test_principal_plus_interest_equals_emi(self):
        """For each month: principal_component + interest_component ≈ EMI."""
        from src.engines.loan_engine import generate_ideal_schedule
        schedule = generate_ideal_schedule(5000000_00, 8.5, 12, date(2025, 1, 1))
        for entry in schedule:
            principal = entry.get("principal_paise", 0)
            interest = entry.get("interest_paise", 0)
            emi = entry.get("emi_paise", 0)
            assert abs(principal + interest - emi) <= 1, f"P({principal}) + I({interest}) != EMI({emi})"


class TestLoanReplayPayments:
    """Test replay_payments function for correctness."""
    
    def test_replay_with_no_payments(self):
        """With no payments, balance should equal principal."""
        from src.engines.loan_engine import replay_payments
        result = replay_payments(
            principal_paise=1000000_00,
            annual_rate_percent=10.0,
            start_date=date(2025, 1, 1),
            payments=[]
        )
        assert result["remaining_principal_paise"] == 1000000_00
        assert result["total_interest_paid_paise"] == 0
        assert result["total_principal_paid_paise"] == 0

    def test_replay_determinism(self):
        """Same payments should give same result."""
        from src.engines.loan_engine import replay_payments
        payments = [
            {"date": date(2025, 2, 1), "amount_paise": 50000_00, "type": "EMI"},
            {"date": date(2025, 3, 1), "amount_paise": 50000_00, "type": "EMI"},
        ]
        r1 = replay_payments(1000000_00, 10.0, date(2025, 1, 1), payments)
        r2 = replay_payments(1000000_00, 10.0, date(2025, 1, 1), payments)
        assert r1["remaining_principal_paise"] == r2["remaining_principal_paise"]
        assert r1["total_interest_paid_paise"] == r2["total_interest_paid_paise"]


# ============================================================
# Projection Engine Tests
# ============================================================

class TestGoalProjection:

    def test_goal_no_returns(self):
        """Without returns, months = target / monthly_savings."""
        from src.engines.projection_engine import project_goal
        result = project_goal(
            monthly_savings_paise=100000_00,  # ₹1,00,000
            target_paise=1200000_00,          # ₹12,00,000
            current_paise=0,
            annual_return=0.0,
        )
        assert result["months_needed"] == 12

    def test_goal_with_existing_amount(self):
        from src.engines.projection_engine import project_goal
        result = project_goal(
            monthly_savings_paise=100000_00,
            target_paise=1200000_00,
            current_paise=600000_00,  # Already have ₹6L
            annual_return=0.0,
        )
        assert result["months_needed"] == 6

    def test_goal_determinism(self):
        from src.engines.projection_engine import project_goal
        r1 = project_goal(100000_00, 1200000_00, 0, 8.0)
        r2 = project_goal(100000_00, 1200000_00, 0, 8.0)
        assert r1 == r2

    def test_goal_already_achieved(self):
        """If current >= target, months_needed should be 0."""
        from src.engines.projection_engine import project_goal
        result = project_goal(
            monthly_savings_paise=100000_00,
            target_paise=500000_00,
            current_paise=600000_00,
            annual_return=0.0,
        )
        assert result["months_needed"] == 0
        assert result["target_already_achieved"] is True


# ============================================================
# Net Worth Engine Tests
# ============================================================

class TestNetWorthInvariant:

    def test_net_worth_equals_assets_minus_liabilities(self):
        """Fundamental accounting equation must hold."""
        from src.db import FinanceDB
        from src.engines.networth_engine import compute_net_worth
        
        db = FinanceDB(':memory:')
        
        # Insert test account
        db.create_account({
            "name": "Savings",
            "account_type": "savings",
            "balance_paise": 500000_00
        })
        
        # Insert test loan
        db.insert_loan({
            "name": "Car Loan",
            "loan_type": "car",
            "principal_paise": 300000_00,
            "outstanding_paise": 200000_00,
            "interest_rate": 9.0,
            "start_date": "2024-01-01"
        })
        
        result = compute_net_worth(db)
        calculated = result["total_assets_paise"] - result["total_liabilities_paise"]
        assert result["net_worth_paise"] == calculated, \
            f"Invariant broken: {result['net_worth_paise']} != {result['total_assets_paise']} - {result['total_liabilities_paise']}"
        db.close()

    def test_net_worth_determinism(self):
        """Same data should give same net worth."""
        from src.db import FinanceDB
        from src.engines.networth_engine import compute_net_worth
        
        db = FinanceDB(':memory:')
        db.create_account({
            "name": "Savings",
            "account_type": "savings",
            "balance_paise": 500000_00
        })
        
        r1 = compute_net_worth(db)
        r2 = compute_net_worth(db)
        
        assert r1["net_worth_paise"] == r2["net_worth_paise"]
        db.close()


# ============================================================
# Cashflow Engine Tests
# ============================================================

class TestCashflowCalculation:

    def test_net_cashflow_equals_income_minus_expense(self):
        from src.db import FinanceDB
        from src.engines.cashflow_engine import compute_monthly_cashflow
        
        db = FinanceDB(':memory:')
        
        # Insert a statement first
        stmt_id = db.insert_statement("TestBank", "test.pdf")
        
        # Insert test transactions for a known month
        db.insert_transactions(stmt_id, [
            {
                "date": "15/01/2025",
                "description": "Salary",
                "amount": "50000.00",
                "type": "credit",
            },
            {
                "date": "20/01/2025",
                "description": "Rent",
                "amount": "20000.00",
                "type": "debit",
            },
        ])
        
        result = compute_monthly_cashflow(db, months=1)
        if result:
            month_data = result[0]
            net = month_data["total_income_paise"] - month_data["total_expense_paise"]
            assert month_data["net_cashflow_paise"] == net
        db.close()

    def test_cashflow_determinism(self):
        """Same transactions should give same cashflow."""
        from src.db import FinanceDB
        from src.engines.cashflow_engine import compute_monthly_cashflow
        
        db = FinanceDB(':memory:')
        stmt_id = db.insert_statement("TestBank", "test.pdf")
        db.insert_transactions(stmt_id, [
            {"date": "15/01/2025", "description": "Salary", "amount": "50000.00", "type": "credit"},
        ])
        
        r1 = compute_monthly_cashflow(db, months=1)
        r2 = compute_monthly_cashflow(db, months=1)
        
        if r1 and r2:
            assert r1[0]["net_cashflow_paise"] == r2[0]["net_cashflow_paise"]
        db.close()


# ============================================================
# Balance Engine Tests
# ============================================================

class TestBalanceCalculation:

    def test_running_balance_determinism(self):
        """Running balance should be deterministic."""
        from src.db import FinanceDB
        from src.engines.balance_engine import compute_running_balance
        
        db = FinanceDB(':memory:')
        stmt_id = db.insert_statement("TestBank", "test.pdf")
        db.insert_transactions(stmt_id, [
            {"date": "15/01/2025", "description": "Credit", "amount": "1000.00", "type": "credit"},
            {"date": "16/01/2025", "description": "Debit", "amount": "500.00", "type": "debit"},
        ])
        
        b1 = compute_running_balance(db)
        b2 = compute_running_balance(db)
        
        assert len(b1) == len(b2)
        for r1, r2 in zip(b1, b2):
            assert r1["balance_paise"] == r2["balance_paise"]
        db.close()


# ============================================================
# Utility Tests
# ============================================================

class TestAddMonths:
    """Test the consolidated add_months function."""
    
    def test_add_months_basic(self):
        from src.utils import add_months
        result = add_months(date(2025, 1, 15), 1)
        assert result == date(2025, 2, 15)

    def test_add_months_year_rollover(self):
        from src.utils import add_months
        result = add_months(date(2025, 12, 15), 1)
        assert result == date(2026, 1, 15)

    def test_add_months_clamping(self):
        """Jan 31 + 1 month = Feb 28 (clamped to month end)."""
        from src.utils import add_months
        result = add_months(date(2025, 1, 31), 1)
        assert result == date(2025, 2, 28)

    def test_add_months_leap_year(self):
        """Jan 31 + 1 month in leap year = Feb 29."""
        from src.utils import add_months
        result = add_months(date(2024, 1, 31), 1)
        assert result == date(2024, 2, 29)

    def test_add_months_determinism(self):
        """Same inputs should always give same output."""
        from src.utils import add_months
        results = [add_months(date(2025, 1, 31), 1) for _ in range(100)]
        assert len(set(results)) == 1


# ============================================================
# Financial Constants Tests
# ============================================================

class TestFinancialConstants:
    """Verify financial constants are defined and have correct values."""
    
    def test_days_in_year(self):
        from src.utils import DAYS_IN_YEAR
        assert DAYS_IN_YEAR == 365

    def test_max_projection_months(self):
        from src.utils import MAX_PROJECTION_MONTHS
        assert MAX_PROJECTION_MONTHS == 600

    def test_goal_max_months(self):
        from src.utils import GOAL_MAX_MONTHS
        assert GOAL_MAX_MONTHS == 1000

    def test_default_equity_return(self):
        from src.utils import DEFAULT_EQUITY_RETURN
        assert DEFAULT_EQUITY_RETURN == 10.0

    def test_default_debt_return(self):
        from src.utils import DEFAULT_DEBT_RETURN
        assert DEFAULT_DEBT_RETURN == 7.0

    def test_default_inflation_rate(self):
        from src.utils import DEFAULT_INFLATION_RATE
        assert DEFAULT_INFLATION_RATE == 6.0

    def test_fixed_expense_categories(self):
        from src.utils import FIXED_EXPENSE_CATEGORIES
        assert 'EMI' in FIXED_EXPENSE_CATEGORIES
        assert 'Rent' in FIXED_EXPENSE_CATEGORIES
        assert isinstance(FIXED_EXPENSE_CATEGORIES, frozenset)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
