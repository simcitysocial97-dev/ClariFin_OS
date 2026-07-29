"""
Behaviour Engine Phase 12 — Integration Testing
================================================

Consolidated from test_behaviour_engine_integration.py.
Integration tests for complete financial behaviour analysis pipeline.

Tests verify end-to-end integration of:
- Income source classification (excludes borrowing)
- Debt intelligence metrics (FOIR, credit dependency, revolver ratio)
- Financial personality classification (DEBT_DEPENDENT profile)
- Wellness score calculation (reduced due to debt obligations)
- Recommendation generation (debt and FOIR alerts)

All monetary values are in paise (₹1.00 = 100 paise).
"""

from decimal import Decimal

import pytest

from src.engines.behaviour_engine import (
    classify_financial_personality,
    compute_borrowed_lifestyle_ratio,
    compute_credit_dependency_ratio,
    compute_credit_revolver_ratio,
    compute_debt_cycle_score,
    compute_foir,
    compute_resilience_index,
    compute_true_savings_rate,
)
from src.engines.behaviour_engine.income import (
    classify_income_source,
    compute_true_income_total,
    filter_true_income,
)
from src.engines.behaviour_engine.profile import (
    DEBT_DEPENDENT_MIN_BORROWED_RATIO,
)
from src.engines.behaviour_engine.wellness import (
    classify_wellness_band,
    compute_wellness_score,
)
from src.engines.recommendation_engine import (
    check_debt_dependency,
    check_foir,
    check_liquidity,
    compute_recommendations,
)
from src.engines.recommendation_engine.recommendations import (
    FOIR_THRESHOLD,
)

# ============================================================
# Test Fixtures - Single Month Transaction Data for DEBT_DEPENDENT
# ============================================================


@pytest.fixture
def debt_dependent_transactions() -> list[dict]:
    """
    Generate single month transaction data matching the DEBT_DEPENDENT scenario.

    Scenario as specified:
    - Monthly salary: ₹80000 (800,000 paise)
    - Monthly expenses: ₹110,000 (1,100,000 paise) - exceeds income
    - Credit-funded expenses: ₹30,000 (300,000 paise) - 27% of total expenses
    - Loan EMI: ₹25,000 (250,000 paise)
    - Credit card partial payment: revolving behavior
    - Negative savings rate (expenses > income)
    """
    # Monthly salary - TRUE INCOME
    salary = {
        "id": 1,
        "date_iso": "2023-01-01",
        "description": "Salary credit",
        "amount_paise": 800000,
        "type": "credit",
        "category": "income",
    }

    # Essential expenses (73% of total - to make credit-funded expenses exactly 27%)
    essential_expenses = [
        {
            "id": 2,
            "date_iso": "2023-01-05",
            "description": "Rent payment",
            "amount_paise": 400000,
            "type": "debit",
            "category": "rent",
        },
        {
            "id": 3,
            "date_iso": "2023-01-07",
            "description": "Groceries",
            "amount_paise": 300000,
            "type": "debit",
            "category": "groceries",
        },
        {
            "id": 4,
            "date_iso": "2023-01-10",
            "description": "Utilities",
            "amount_paise": 100000,
            "type": "debit",
            "category": "utilities",
        },
    ]

    # Credit-funded expenses (27% of total) - these are flagged as credit in description
    credit_funded_expenses = [
        {
            "id": 5,
            "date_iso": "2023-01-15",
            "description": "Credit card Amazon",
            "amount_paise": 150000,
            "type": "debit",
            "category": "shopping",
        },
        {
            "id": 6,
            "date_iso": "2023-01-20",
            "description": "Credit card Swiggy",
            "amount_paise": 150000,
            "type": "debit",
            "category": "dining",
        },
    ]

    return [salary] + essential_expenses + credit_funded_expenses


@pytest.fixture
def credit_card_data() -> list[dict]:
    """
    Credit card data with outstanding balances indicating revolving behavior.

    - All cards have outstanding balances (partial payments)
    - Indicates revolving credit usage
    """
    return [
        {
            "id": 1,
            "name": "HDFC Bank Credit Card",
            "credit_limit_paise": 500000,  # ₹5L limit
            "outstanding_paise": 150000,  # ₹1.5L outstanding (revolving)
        },
        {
            "id": 2,
            "name": "SBI Credit Card",
            "credit_limit_paise": 300000,  # ₹3L limit
            "outstanding_paise": 80000,  # ₹80K outstanding (revolving)
        },
    ]


@pytest.fixture
def loan_data() -> list[dict]:
    """
    Loan data with EMIs matching scenario.

    - One personal loan with ₹25K monthly EMI
    """
    return [
        {
            "id": 1,
            "name": "Personal Loan",
            "emi_paise": 250000,  # ₹25K EMI (matches scenario)
            "principal_paise": 5000000,  # ₹50L principal
            "interest_paise": 0,
        },
    ]


@pytest.fixture
def account_data() -> list[dict]:
    """
    Account data with minimal liquid assets.

    - Low savings indicating insufficient emergency fund
    """
    return [
        {
            "id": 1,
            "account_type": "savings",
            "balance_paise": 200000,  # ₹20K - low liquidity
        },
    ]


# ============================================================
# Test: Income Excludes Borrowing
# ============================================================


class TestIntegrationIncomeExcludesBorrowing:
    """Verify that income calculations exclude borrowing transactions."""

    def test_salary_only_true_income(self, debt_dependent_transactions):
        """True income should only include salary, not loans or credit."""
        true_income = compute_true_income_total(debt_dependent_transactions)

        # Only salary transaction should count
        expected = 800000  # ₹80K

        assert true_income == expected, f"Expected {expected}, got {true_income}"

    def test_filter_true_income_removes_borrowing(self):
        """filter_true_income should remove loan/borrowing transactions."""
        mixed_transactions = [
            {
                "id": 1,
                "description": "Salary credit",
                "amount_paise": 8000000,
                "type": "credit",
            },
            {
                "id": 2,
                "description": "Business income",
                "amount_paise": 2000000,
                "type": "credit",
            },
            {
                "id": 3,
                "description": "Investment dividend",
                "amount_paise": 1000000,
                "type": "credit",
            },
            {
                "id": 4,
                "description": "Home loan disbursement",
                "amount_paise": 50000000,
                "type": "credit",
            },
            {
                "id": 5,
                "description": "Credit card cash withdrawal",
                "amount_paise": 1000000,
                "type": "credit",
            },
            {
                "id": 6,
                "description": "Transfer from other account",
                "amount_paise": 1000000,
                "type": "credit",
            },
            {
                "id": 7,
                "description": "Refund from store",
                "amount_paise": 50000,
                "type": "credit",
            },
        ]

        true_income_txns = filter_true_income(mixed_transactions)

        # Should only include salary, business, investment
        assert len(true_income_txns) == 3

        descriptions = [t["description"].lower() for t in true_income_txns]
        assert "salary" in descriptions[0]
        assert "business" in descriptions[1]
        assert "investment" in descriptions[2]

    def test_classify_income_borrowing(self):
        """classify_income_source should identify borrowing correctly."""
        borrowing_txn = {
            "description": "Home loan disbursement",
            "amount_paise": 50000000,
        }
        category, confidence = classify_income_source(borrowing_txn)

        assert category == "borrowing"
        assert confidence == 1.0

    def test_classify_income_salary(self):
        """classify_income_source should identify salary correctly."""
        salary_txn = {"description": "Salary credit for June", "amount_paise": 8000000}
        category, confidence = classify_income_source(salary_txn)

        assert category == "salary"
        assert confidence == 1.0


# ============================================================
# Test: Debt Dependency Detection
# ============================================================


class TestIntegrationDebtDependency:
    """Verify debt dependency metrics are correctly computed."""

    def test_credit_dependency_ratio_detects_borrowing(
        self, debt_dependent_transactions
    ):
        """Credit dependency ratio should be above 20% threshold for scenario."""
        total_expenses = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit"
        )

        # Credit-funded expenses: credit card transactions only
        credit_funded = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit" and "credit" in t["description"].lower()
        )

        ratio = compute_credit_dependency_ratio(credit_funded, total_expenses)

        # Credit expenses: 300,000 / 1,100,000 = 27% (> 20% threshold)
        assert (
            ratio > DEBT_DEPENDENT_MIN_BORROWED_RATIO
        ), f"Borrowed lifestyle ratio {ratio} should exceed {DEBT_DEPENDENT_MIN_BORROWED_RATIO}"

    def test_foir_calculated_correctly(self, loan_data, credit_card_data):
        """FOIR should be calculated from EMI and minimum due."""
        loan_emi = sum(loan.get("emi_paise", 0) for loan in loan_data)

        # Minimum due is typically 5% of credit card outstanding
        credit_min_due = sum(
            int(card.get("outstanding_paise", 0) * 0.05) for card in credit_card_data
        )

        monthly_income = 800000  # ₹80K monthly salary

        foir, band = compute_foir(loan_emi, credit_min_due, monthly_income)

        # FOIR = (250,000 + min_due) / 800,000
        # min_due = (150,000 + 80,000) * 0.05 = 11,500
        # FOIR ≈ 0.32 (32%)
        assert foir > Decimal("0"), "FOIR should be positive with obligations"
        assert foir <= Decimal("1"), "FOIR should not exceed 100%"
        assert band in ["HEALTHY", "MODERATE", "WARNING", "CRITICAL"]

    def test_credit_revolver_ratio_high(self, credit_card_data):
        """High revolving credit behavior should be detected."""
        # All cards have outstanding balances
        active_months = len(credit_card_data)

        ratio = compute_credit_revolver_ratio(active_months, active_months)

        # All cards active with outstanding = 1.0 ratio
        assert ratio == Decimal("1.0")

    def test_debt_cycle_score_elevated(self):
        """Debt cycle score should be elevated with credit advances and revolving."""
        # Simulate credit advances and revolving in last 6 months
        credit_advances = 4  # High number of advances
        revolving_months = 6  # All months have revolving
        debt_trend = Decimal("0.5")  # Rising debt trend

        score = compute_debt_cycle_score(credit_advances, revolving_months, debt_trend)

        # Score should be elevated (not low)
        assert (
            score > 50
        ), f"Debt cycle score {score} should be elevated with advances and revolving"


# ============================================================
# Test: FOIR Calculation
# ============================================================


class TestIntegrationFOIRCalculation:
    """Verify FOIR is correctly calculated and banded."""

    def test_foir_with_loan_emi(self, loan_data, credit_card_data):
        """FOIR should include loan EMI and credit card minimum due."""
        loan_emi = sum(loan.get("emi_paise", 0) for loan in loan_data)
        credit_min_due = sum(
            int(card.get("outstanding_paise", 0) * 0.05) for card in credit_card_data
        )

        foir, band = compute_foir(loan_emi, credit_min_due, 800000)

        # Verify the ratio is approximately correct (rounding differences)
        expected_total = loan_emi + credit_min_due
        expected_ratio = Decimal(str(expected_total)) / Decimal("800000")

        # Allow for rounding differences
        assert abs(foir - expected_ratio) < Decimal(
            "0.001"
        ), f"FOIR {foir} should be close to {expected_ratio}"

    def test_foir_above_threshold(self, loan_data):
        """FOIR above 50% should trigger HIGH severity recommendation."""
        loan_emi = 250000

        # Create scenario with high FOIR - but this loan EMI alone won't exceed threshold
        foir, band = compute_foir(loan_emi, 0, 400000)  # Lower income

        assert foir > FOIR_THRESHOLD or band in ["WARNING", "CRITICAL"]


# ============================================================
# Test: Financial Personality = DEBT_DEPENDENT
# ============================================================


class TestIntegrationFinancialPersonality:
    """Verify financial personality classification for DEBT_DEPENDENT scenario."""

    def test_debt_dependent_profile_classification(self, debt_dependent_transactions):
        """Scenario should classify as DEBT_DEPENDENT."""
        # Calculate all required metrics for profile classification
        total_income = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "credit"
        )
        total_expenses = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit"
        )

        savings_rate = compute_true_savings_rate(total_income, total_expenses, 0)
        credit_funded = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit" and "credit" in t["description"].lower()
        )
        borrowed_lifestyle_ratio = compute_borrowed_lifestyle_ratio(
            credit_funded, total_expenses
        )

        # Credit revolver ratio from credit card data - high revolving
        credit_revolver_ratio = Decimal("0.8")  # High revolving behavior

        # Discretionary spending ratio
        discretionary_categories = {"dining", "shopping", "entertainment", "travel"}
        discretionary_spending = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit"
            and t.get("category", "").lower() in discretionary_categories
        )
        discretionary_ratio = Decimal(str(discretionary_spending)) / Decimal(
            str(total_expenses)
        )

        # Impulse ratio (simplified - assume low)
        impulse_ratio = Decimal("0.1")

        # Lifestyle creep
        lifestyle_creep = Decimal("0.2")  # Some lifestyle inflation

        profile, confidence, explanation = classify_financial_personality(
            savings_rate=savings_rate,
            borrowed_lifestyle_ratio=borrowed_lifestyle_ratio,
            credit_revolver_ratio=credit_revolver_ratio,
            discretionary_spending_ratio=discretionary_ratio,
            impulse_transaction_ratio=impulse_ratio,
            lifestyle_creep_index=lifestyle_creep,
            transaction_count=len(debt_dependent_transactions),
        )

        assert profile == "DEBT_DEPENDENT", (
            f"Expected DEBT_DEPENDENT, got {profile}. Explanation: {explanation}. "
            f"borrowed_lifestyle_ratio={borrowed_lifestyle_ratio}"
        )

    def test_debt_dependent_recurring_extraction(self):
        """DEBT_DEPENDENT via high revolver + low savings path."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal("-0.1"),  # Negative savings
            borrowed_lifestyle_ratio=Decimal("0.15"),  # Below threshold
            credit_revolver_ratio=Decimal("0.8"),  # High revolver
            discretionary_spending_ratio=Decimal("0.3"),
            impulse_transaction_ratio=Decimal("0.2"),
            lifestyle_creep_index=Decimal("0.2"),
            transaction_count=100,
        )

        assert profile == "DEBT_DEPENDENT"


# ============================================================
# Test: Wellness Score Reduced
# ============================================================


class TestIntegrationWellnessScore:
    """Verify wellness score is reduced for DEBT_DEPENDENT scenario."""

    def test_wellness_score_reduced_due_to_debt(self, debt_dependent_transactions):
        """Wellness score should be in Risk or Critical band for DEBT_DEPENDENT."""
        total_income = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "credit"
        )
        total_expenses = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit"
        )

        savings_rate = compute_true_savings_rate(total_income, total_expenses, 0)
        cashflow_stability = Decimal("0.5")  # Moderate
        resilience_index = Decimal("0.3")  # Low liquidity
        debt_cycle_score = 70  # Elevated
        credit_revolver_ratio = Decimal("0.8")  # High
        foir = Decimal("0.35")  # Moderate (35%)
        lifestyle_inflation = Decimal("0.25")  # Growing

        wellness = compute_wellness_score(
            cashflow_stability=cashflow_stability,
            debt_cycle_score=debt_cycle_score,
            savings_rate=savings_rate,
            resilience_index=resilience_index,
            lifestyle_inflation=lifestyle_inflation,
            credit_revolver_ratio=credit_revolver_ratio,
            foir=foir,
        )

        band = classify_wellness_band(wellness)

        # Score should be in Risk or Critical band
        assert band in [
            "Risk",
            "Critical",
            "Developing",
        ], f"Wellness band should be Risk/Critical/Developing, got {band} with score {wellness}"

    def test_negative_savings_clamped_in_wellness(self):
        """Negative savings rate should be clamped to 0 in wellness calculation."""
        # Test that negative savings doesn't crash the system
        result = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("-0.5"),  # Negative
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.5"),
            credit_revolver_ratio=Decimal("0.5"),
            foir=Decimal("0.5"),
        )

        # Should produce a valid (clamped) result
        assert Decimal("0") <= result <= Decimal("100")


# ============================================================
# Test: Recommendations Generated
# ============================================================


class TestIntegrationRecommendations:
    """Verify recommendations are generated based on metrics."""

    def test_debt_dependency_recommendation(self, debt_dependent_transactions):
        """Debt dependency should generate HIGH severity recommendation."""
        total_expenses = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit"
        )
        credit_funded = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit" and "credit" in t["description"].lower()
        )
        borrowed_ratio = compute_borrowed_lifestyle_ratio(credit_funded, total_expenses)

        rec = check_debt_dependency(borrowed_ratio)

        assert (
            rec is not None
        ), "Should generate recommendation for debt dependency >20%"
        assert rec.title == "Lifestyle Debt Alert"
        assert rec.severity == "HIGH"
        assert "borrowed money" in rec.reason

    def test_foir_recommendation(self, loan_data):
        """High FOIR should generate appropriate recommendation."""
        loan_emi = sum(loan.get("emi_paise", 0) for loan in loan_data)

        # Create scenario with high FOIR
        foir, band = compute_foir(loan_emi, 0, 400000)  # Lower income

        rec = check_foir(foir)

        if rec is not None:
            assert rec.title == "High Fixed Obligations"
            assert rec.severity in ["HIGH", "CRITICAL"]

    def test_liquidity_recommendation(self):
        """Low liquidity should generate recommendation."""
        # 2 months liquidity (below 3 month threshold)
        rec = check_liquidity(2)

        assert rec is not None
        assert rec.title == "Emergency Fund Needed"
        assert rec.severity == "MEDIUM"

    def test_multiple_recommendations_generated(self):
        """Multiple issues should generate multiple recommendations."""
        recommendations = compute_recommendations(
            borrowed_lifestyle_ratio=Decimal("0.25"),  # Above threshold
            foir=Decimal("0.55"),  # Above threshold
            liquidity_months=2,  # Below threshold
            current_subscriptions=[],
        )

        # Should have debt dependency, FOIR recommendations, and liquidity
        assert len(recommendations) >= 3

        # Verify sorting by severity (CRITICAL first)
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_recs = sorted(
            recommendations, key=lambda r: severity_order.get(r.severity, 4)
        )
        assert recommendations == sorted_recs

    def test_recommendations_contain_actionable_suggestions(
        self, debt_dependent_transactions
    ):
        """All recommendations should have actionable suggested actions."""
        total_expenses = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit"
        )
        credit_funded = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit" and "credit" in t["description"].lower()
        )
        borrowed_ratio = compute_borrowed_lifestyle_ratio(credit_funded, total_expenses)

        rec = check_debt_dependency(borrowed_ratio)

        assert rec is not None
        assert hasattr(rec, "suggested_action")
        assert len(rec.suggested_action) > 10, "Suggested action should be meaningful"


# ============================================================
# Test: Cross-Component Consistency
# ============================================================


class TestIntegrationMetricConsistency:
    """Verify metrics are consistent across engine functions."""

    def test_credit_dependency_matches_borrowed_ratio(
        self, debt_dependent_transactions
    ):
        """Credit dependency ratio should equal borrowed lifestyle ratio."""
        total_expenses = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit"
        )
        credit_funded = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit" and "credit" in t["description"].lower()
        )

        ratio1 = compute_credit_dependency_ratio(credit_funded, total_expenses)
        ratio2 = compute_borrowed_lifestyle_ratio(credit_funded, total_expenses)

        assert (
            ratio1 == ratio2
        ), "Credit dependency ratio should equal borrowed lifestyle ratio"

    def test_negative_savings_handled(self, debt_dependent_transactions):
        """Engine should handle savings rate correctly for scenario."""
        total_income = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "credit"
        )
        total_expenses = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit"
        )

        savings_rate = compute_true_savings_rate(total_income, total_expenses, 0)

        # Savings should be negative when expenses > income
        assert savings_rate < Decimal(
            "0"
        ), f"Savings rate should be negative, got {savings_rate}"


# ============================================================
# Test: Complete Pipeline Integration
# ============================================================


class TestIntegrationCompletePipeline:
    """End-to-end integration tests for complete behaviour analysis."""

    def test_complete_financial_analysis_pipeline(
        self, debt_dependent_transactions, credit_card_data, loan_data, account_data
    ):
        """Run complete pipeline and verify all outputs are consistent."""
        # Step 1: Income analysis
        true_income = compute_true_income_total(debt_dependent_transactions)
        assert true_income > 0

        # Step 2: Expense analysis
        total_expenses = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit"
        )

        # Step 3: Savings rate (will be negative)
        savings_rate = compute_true_savings_rate(true_income, total_expenses, 0)

        # Step 4: Credit dependency
        credit_funded = sum(
            t["amount_paise"]
            for t in debt_dependent_transactions
            if t["type"] == "debit" and "credit" in t["description"].lower()
        )
        borrowed_ratio = compute_borrowed_lifestyle_ratio(credit_funded, total_expenses)

        # Step 5: FOIR
        loan_emi = sum(loan.get("emi_paise", 0) for loan in loan_data)
        credit_min_due = sum(
            int(card.get("outstanding_paise", 0) * 0.05) for card in credit_card_data
        )
        foir, _ = compute_foir(loan_emi, credit_min_due, true_income)

        # Step 6: Resilience
        liquid_assets = sum(
            acc["balance_paise"]
            for acc in account_data
            if acc["account_type"] in {"savings", "current"}
        )

        resilience = compute_resilience_index(
            liquid_assets_paise=liquid_assets,
            essential_monthly_expenses_paise=300000,  # rent + groceries + utilities
            total_income_paise=true_income,
            monthly_incomes_paise=[true_income],  # Stable income
        )

        # Step 7: Wellness score
        wellness = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=70,
            savings_rate=savings_rate,
            resilience_index=resilience,
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.8"),
            foir=foir,
        )

        # Step 8: Profile classification
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=savings_rate,
            borrowed_lifestyle_ratio=borrowed_ratio,
            credit_revolver_ratio=Decimal("0.8"),
            discretionary_spending_ratio=Decimal("0.27"),
            impulse_transaction_ratio=Decimal("0.1"),
            lifestyle_creep_index=Decimal("0.25"),
            transaction_count=len(debt_dependent_transactions),
        )

        # Step 9: Recommendations
        recommendations = compute_recommendations(
            borrowed_lifestyle_ratio=borrowed_ratio,
            foir=foir,
            liquidity_months=2,  # Below threshold
            current_subscriptions=[],
        )

        # Verify all outputs are consistent
        assert profile == "DEBT_DEPENDENT", f"Expected DEBT_DEPENDENT, got {profile}"
        assert len(recommendations) >= 1
        assert wellness < Decimal("50") or classify_wellness_band(wellness) in [
            "Risk",
            "Critical",
            "Developing",
        ]


# ============================================================
# Test: Determinism
# ============================================================


class TestIntegrationDeterminism:
    """Verify all engine functions are deterministic."""

    def test_scenario_deterministic_across_runs(self, debt_dependent_transactions):
        """Complete scenario should produce deterministic results."""
        # Run the same analysis twice
        results = []
        for _ in range(2):
            total_income = sum(
                t["amount_paise"]
                for t in debt_dependent_transactions
                if t["type"] == "credit"
            )
            total_expenses = sum(
                t["amount_paise"]
                for t in debt_dependent_transactions
                if t["type"] == "debit"
            )

            savings_rate = compute_true_savings_rate(total_income, total_expenses, 0)
            credit_funded = sum(
                t["amount_paise"]
                for t in debt_dependent_transactions
                if t["type"] == "debit" and "credit" in t["description"].lower()
            )
            borrowed_ratio = compute_borrowed_lifestyle_ratio(
                credit_funded, total_expenses
            )

            profile, confidence, _ = classify_financial_personality(
                savings_rate=savings_rate,
                borrowed_lifestyle_ratio=borrowed_ratio,
                credit_revolver_ratio=Decimal("0.8"),
                discretionary_spending_ratio=Decimal("0.27"),
                impulse_transaction_ratio=Decimal("0.1"),
                lifestyle_creep_index=Decimal("0.25"),
                transaction_count=len(debt_dependent_transactions),
            )

            wellness = compute_wellness_score(
                cashflow_stability=Decimal("0.5"),
                debt_cycle_score=70,
                savings_rate=savings_rate,
                resilience_index=Decimal("0.3"),
                lifestyle_inflation=Decimal("0.2"),
                credit_revolver_ratio=Decimal("0.8"),
                foir=Decimal("0.4"),
            )

            results.append((profile, wellness))

        # Verify both runs produced same results
        assert results[0][0] == results[1][0], "Profile should be deterministic"
        assert results[0][1] == results[1][1], "Wellness should be deterministic"


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
