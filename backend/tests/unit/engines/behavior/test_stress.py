"""Unit tests for behaviour_engine/stress.py."""


class TestStressUtilityFunctions:
    """Tests for utility functions in stress.py."""

    def test_parse_date_iso_format(self):
        """ISO format dates parse correctly."""
        from src.engines.behaviour_engine.stress import _parse_date

        result = _parse_date("2025-01-15")
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_indian_format(self):
        """Indian format dates parse correctly."""
        from src.engines.behaviour_engine.stress import _parse_date

        result = _parse_date("15/01/2025")
        assert result is not None
        assert result.day == 15
        assert result.month == 1

    def test_parse_date_invalid(self):
        """Invalid dates return None."""
        from src.engines.behaviour_engine.stress import _parse_date

        assert _parse_date("") is None
        assert _parse_date(None) is None  # type: ignore
        assert _parse_date("invalid") is None
        assert _parse_date("99/99/9999") is None

    def test_normalize_score_bounds(self):
        """Score normalization clamps to [0, 1]."""
        from src.engines.behaviour_engine.stress import _normalize_score

        assert _normalize_score(-10, 0, 100) == 0.0
        assert _normalize_score(200, 0, 100) == 1.0
        assert _normalize_score(50, 0, 100) == 0.5
        assert _normalize_score(0, 0, 100) == 0.0
        assert _normalize_score(100, 0, 100) == 1.0

    def test_normalize_score_equal_bounds(self):
        """Equal min/max returns midpoint."""
        from src.engines.behaviour_engine.stress import _normalize_score

        assert _normalize_score(42, 7, 7) == 0.5

    def test_coefficient_of_variation_empty(self):
        """Empty list returns zero."""
        from src.engines.behaviour_engine.stress import _coefficient_of_variation

        assert _coefficient_of_variation([]) == 0.0

    def test_coefficient_of_variation_single(self):
        """Single value returns zero."""
        from src.engines.behaviour_engine.stress import _coefficient_of_variation

        assert _coefficient_of_variation([42]) == 0.0

    def test_coefficient_of_variation_identical(self):
        """Identical values have zero CV."""
        from src.engines.behaviour_engine.stress import _coefficient_of_variation

        assert _coefficient_of_variation([10, 10, 10]) == 0.0


class TestLossAversionIndex:
    """Tests for loss_aversion_index function."""

    def test_empty_transactions(self):
        """Empty transactions return baseline score."""
        from src.engines.behaviour_engine.stress import loss_aversion_index

        result = loss_aversion_index([])
        assert result["score"] == 0.5
        assert result["post_income_velocity"] == 0.0
        assert result["recovery_time_days"] == 0

    def test_no_credits(self):
        """Only debits return baseline score."""
        from src.engines.behaviour_engine.stress import loss_aversion_index

        transactions = [
            {"type": "debit", "date_iso": "2025-01-15", "amount_paise": 100000}
        ]
        result = loss_aversion_index(transactions)
        assert result["score"] == 0.5

    def test_no_debits(self):
        """Only credits return baseline score."""
        from src.engines.behaviour_engine.stress import loss_aversion_index

        transactions = [
            {"type": "credit", "date_iso": "2025-01-15", "amount_paise": 500000}
        ]
        result = loss_aversion_index(transactions)
        assert result["score"] == 0.5

    def test_post_income_spending_velocity(self):
        """Post-income velocity calculated correctly."""
        from src.engines.behaviour_engine.stress import loss_aversion_index

        transactions = [
            {"type": "credit", "date_iso": "2025-01-01", "amount_paise": 1000000},
            {"type": "debit", "date_iso": "2025-01-01", "amount_paise": 500000},
            {"type": "debit", "date_iso": "2025-01-02", "amount_paise": 300000},
        ]
        result = loss_aversion_index(transactions)
        # Velocity should be positive (spending within 72h of income)
        assert result["post_income_velocity"] > 0
        assert result["score"] >= 0  # Valid score range

    def test_large_expense_detection(self):
        """Large expenses (>2x median) detected correctly."""
        from src.engines.behaviour_engine.stress import loss_aversion_index

        transactions = [
            {"type": "credit", "date_iso": "2025-01-01", "amount_paise": 1000000},
            {"type": "debit", "date_iso": "2025-01-01", "amount_paise": 100000},
            {"type": "debit", "date_iso": "2025-01-02", "amount_paise": 100000},
            {
                "type": "debit",
                "date_iso": "2025-01-03",
                "amount_paise": 500000,
            },  # Large expense
        ]
        result = loss_aversion_index(transactions)
        assert result["large_expense_count"] >= 1
        assert result["recovery_time_days"] > 0

    def test_recovery_time_capped(self):
        """Recovery time capped at 30 days."""
        from src.engines.behaviour_engine.stress import loss_aversion_index

        # Create scenario with very large expense
        transactions = [
            {"type": "credit", "date_iso": "2025-01-01", "amount_paise": 100000},
            {"type": "debit", "date_iso": "2025-01-01", "amount_paise": 1000},
            {"type": "debit", "date_iso": "2025-01-02", "amount_paise": 1000},
            {
                "type": "debit",
                "date_iso": "2025-01-03",
                "amount_paise": 1000000,
            },  # Huge expense
        ]
        result = loss_aversion_index(transactions)
        assert result["recovery_time_days"] <= 30


class TestImpulsivityScore:
    """Tests for impulsivity_score function."""

    def test_empty_transactions(self):
        """Empty transactions return baseline."""
        from src.engines.behaviour_engine.stress import impulsivity_score

        result = impulsivity_score([])
        assert result["score"] == 0.5

    def test_no_debits(self):
        """Only credits return baseline."""
        from src.engines.behaviour_engine.stress import impulsivity_score

        transactions = [
            {"type": "credit", "date_iso": "2025-01-15", "amount_paise": 500000}
        ]
        result = impulsivity_score(transactions)
        assert result["score"] == 0.5

    def test_micro_transactions_detected(self):
        """Micro-transactions (<₹500) ratio calculated."""
        from src.engines.behaviour_engine.stress import impulsivity_score

        transactions = [
            {
                "type": "debit",
                "date_iso": "2025-01-15",
                "amount_paise": 10000,
                "category": "Food",
            },
            {
                "type": "debit",
                "date_iso": "2025-01-16",
                "amount_paise": 5000,
                "category": "Transport",
            },
            {
                "type": "debit",
                "date_iso": "2025-01-17",
                "amount_paise": 100000,
                "category": "Rent",
            },
        ]
        result = impulsivity_score(transactions)
        assert result["micro_txn_ratio"] > 0
        assert result["micro_txn_count"] == 2  # Two transactions < ₹500

    def test_weekend_vs_weekday_ratio(self):
        """Weekend spending ratio calculated."""
        from src.engines.behaviour_engine.stress import impulsivity_score

        transactions = [
            {
                "type": "debit",
                "date_iso": "2025-01-11",
                "amount_paise": 100000,
            },  # Saturday
            {
                "type": "debit",
                "date_iso": "2025-01-12",
                "amount_paise": 100000,
            },  # Sunday
            {
                "type": "debit",
                "date_iso": "2025-01-13",
                "amount_paise": 50000,
            },  # Monday
        ]
        result = impulsivity_score(transactions)
        assert result["weekend_ratio"] >= 1.0  # Weekend spend >= weekday

    def test_discretionary_spending_ratio(self):
        """Discretionary category ratio calculated."""
        from src.engines.behaviour_engine.stress import impulsivity_score

        transactions = [
            {
                "type": "debit",
                "date_iso": "2025-01-15",
                "amount_paise": 100000,
                "category": "Food & Dining",
            },
            {
                "type": "debit",
                "date_iso": "2025-01-16",
                "amount_paise": 50000,
                "category": "Entertainment",
            },
            {
                "type": "debit",
                "date_iso": "2025-01-17",
                "amount_paise": 200000,
                "category": "Salary",
            },
        ]
        result = impulsivity_score(transactions)
        assert result["discretionary_ratio"] > 0
        assert result["discretionary_ratio"] < 1.0


class TestHabitStabilityScore:
    """Tests for habit_stability_score function."""

    def test_empty_transactions(self):
        """Empty transactions return baseline."""
        from src.engines.behaviour_engine.stress import habit_stability_score

        result = habit_stability_score([])
        assert result["score"] == 0.5

    def test_no_debits(self):
        """Only credits return baseline."""
        from src.engines.behaviour_engine.stress import habit_stability_score

        transactions = [
            {"type": "credit", "date_iso": "2025-01-15", "amount_paise": 500000}
        ]
        result = habit_stability_score(transactions)
        assert result["score"] == 0.5

    def test_recurring_expenses_detected(self):
        """Recurring expenses increase stability score."""
        from src.engines.behaviour_engine.stress import habit_stability_score

        transactions = [
            {
                "type": "debit",
                "date_iso": "2025-01-01",
                "amount_paise": 100000,
                "description": "Netflix",
                "category": "Entertainment",
            },
            {
                "type": "debit",
                "date_iso": "2025-02-01",
                "amount_paise": 100000,
                "description": "Netflix",
                "category": "Entertainment",
            },
            {
                "type": "debit",
                "date_iso": "2025-03-01",
                "amount_paise": 100000,
                "description": "Netflix",
                "category": "Entertainment",
            },
            {
                "type": "debit",
                "date_iso": "2025-01-15",
                "amount_paise": 50000,
                "description": "Groceries",
                "category": "Groceries",
            },
        ]
        result = habit_stability_score(transactions)
        assert result["recurring_count"] >= 1
        assert result["score"] > 0.3

    def test_category_cv_calculated(self):
        """Category coefficient of variation computed."""
        from src.engines.behaviour_engine.stress import habit_stability_score

        transactions = [
            {
                "type": "debit",
                "date_iso": "2025-01-15",
                "amount_paise": 100000,
                "category": "Food",
            },
            {
                "type": "debit",
                "date_iso": "2025-02-15",
                "amount_paise": 120000,
                "category": "Food",
            },
            {
                "type": "debit",
                "date_iso": "2025-03-15",
                "amount_paise": 110000,
                "category": "Food",
            },
        ]
        result = habit_stability_score(transactions)
        assert isinstance(result["category_cv"], float)
        assert result["category_cv"] >= 0


class TestFinancialStressIndex:
    """Tests for financial_stress_index function."""

    def test_empty_transactions(self):
        """Empty transactions return baseline."""
        from src.engines.behaviour_engine.stress import financial_stress_index

        result = financial_stress_index([])
        assert result["score"] == 0.5

    def test_no_debits(self):
        """Only credits return baseline."""
        from src.engines.behaviour_engine.stress import financial_stress_index

        transactions = [
            {"type": "credit", "date_iso": "2025-01-15", "amount_paise": 500000}
        ]
        result = financial_stress_index(transactions)
        assert result["score"] == 0.5

    def test_credit_dependency_calculated(self):
        """Credit dependency ratio computed."""
        from src.engines.behaviour_engine.stress import financial_stress_index

        transactions = [
            {"type": "credit", "date_iso": "2025-01-01", "amount_paise": 1000000},
            {"type": "debit", "date_iso": "2025-01-05", "amount_paise": 500000},
            {"type": "debit", "date_iso": "2025-01-10", "amount_paise": 300000},
        ]
        result = financial_stress_index(transactions)
        assert result["credit_dependency"] > 0
        assert result["balance_volatility"] >= 0

    def test_eom_depletion_ratio(self):
        """End-of-month spending ratio calculated."""
        from src.engines.behaviour_engine.stress import financial_stress_index

        transactions = [
            {"type": "debit", "date_iso": "2025-01-01", "amount_paise": 100000},
            {"type": "debit", "date_iso": "2025-01-26", "amount_paise": 200000},
            {"type": "debit", "date_iso": "2025-01-30", "amount_paise": 150000},
        ]
        result = financial_stress_index(transactions)
        assert result["eom_depletion_ratio"] >= 0
        assert result["buffer_days"] >= 0

    def test_buffer_days_computed(self):
        """Buffer days calculated from running balance."""
        from src.engines.behaviour_engine.stress import financial_stress_index

        transactions = [
            {"type": "credit", "date_iso": "2025-01-01", "amount_paise": 1000000},
            {"type": "debit", "date_iso": "2025-01-05", "amount_paise": 100000},
            {"type": "debit", "date_iso": "2025-01-10", "amount_paise": 100000},
        ]
        result = financial_stress_index(transactions)
        assert result["buffer_days"] > 0


class TestSavingsDisciplineScore:
    """Tests for savings_discipline_score function."""

    def test_empty_transactions(self):
        """Empty transactions return baseline."""
        from src.engines.behaviour_engine.stress import savings_discipline_score

        result = savings_discipline_score([])
        assert result["score"] == 0.5

    def test_positive_savings_rate(self):
        """Positive savings rate increases score."""
        from src.engines.behaviour_engine.stress import savings_discipline_score

        transactions = [
            {"type": "credit", "date_iso": "2025-01-01", "amount_paise": 1000000},
            {"type": "debit", "date_iso": "2025-01-15", "amount_paise": 500000},
            {"type": "credit", "date_iso": "2025-02-01", "amount_paise": 1000000},
            {"type": "debit", "date_iso": "2025-02-15", "amount_paise": 400000},
        ]
        result = savings_discipline_score(transactions)
        assert result["savings_rate"] > 0
        assert result["positive_savings_months"] == 2

    def test_negative_savings_rate(self):
        """Negative savings rate (spending > income)."""
        from src.engines.behaviour_engine.stress import savings_discipline_score

        transactions = [
            {"type": "credit", "date_iso": "2025-01-01", "amount_paise": 500000},
            {"type": "debit", "date_iso": "2025-01-15", "amount_paise": 600000},
        ]
        result = savings_discipline_score(transactions)
        assert result["savings_rate"] < 0

    def test_momentum_computed(self):
        """Savings momentum over time."""
        from src.engines.behaviour_engine.stress import savings_discipline_score

        transactions = [
            {"type": "credit", "date_iso": "2025-01-01", "amount_paise": 1000000},
            {"type": "debit", "date_iso": "2025-01-15", "amount_paise": 800000},
            {"type": "credit", "date_iso": "2025-02-01", "amount_paise": 1000000},
            {"type": "debit", "date_iso": "2025-02-15", "amount_paise": 600000},
            {"type": "credit", "date_iso": "2025-03-01", "amount_paise": 1000000},
            {"type": "debit", "date_iso": "2025-03-15", "amount_paise": 400000},
        ]
        result = savings_discipline_score(transactions)
        assert result["momentum"] >= 0  # Improving trend


class TestDetectRiskPatterns:
    """Tests for detect_risk_patterns function."""

    def test_empty_transactions(self):
        """Empty transactions return all False flags."""
        from src.engines.behaviour_engine.stress import detect_risk_patterns

        result = detect_risk_patterns([])
        assert result["upi_micro_spend_flag"] is False
        assert result["gambling_flag"] is False
        assert result["loan_app_pattern_flag"] is False
        assert result["emi_ratio"] == 0.0

    def test_upi_micro_spend_detection(self):
        """UPI micro-spend pattern detected."""
        from src.engines.behaviour_engine.stress import detect_risk_patterns

        transactions = []
        # Create 11 micro transactions on same day
        for _i in range(11):
            transactions.append(
                {
                    "type": "debit",
                    "date_iso": "2025-01-15",
                    "amount_paise": 10000,  # ₹100
                    "description": "UPI Payment",
                }
            )
        result = detect_risk_patterns(transactions)
        assert result["upi_micro_spend_flag"] is True

    def test_gambling_detection(self):
        """Gambling transactions detected by keywords."""
        from src.engines.behaviour_engine.stress import detect_risk_patterns

        transactions = [
            {
                "type": "debit",
                "date_iso": "2025-01-15",
                "amount_paise": 50000,
                "description": "Dream11 deposit",
            },
            {
                "type": "debit",
                "date_iso": "2025-01-16",
                "amount_paise": 100000,
                "description": "Rummy circle",
            },
        ]
        result = detect_risk_patterns(transactions)
        assert result["gambling_flag"] is True
        assert result["gambling_transaction_count"] >= 1

    def test_loan_app_detection(self):
        """Loan app pattern detected."""
        from src.engines.behaviour_engine.stress import detect_risk_patterns

        transactions = [
            {
                "type": "credit",
                "date_iso": "2025-01-10",
                "amount_paise": 10000,
                "description": "Instant loan credit",
            },
            {
                "type": "credit",
                "date_iso": "2025-01-12",
                "amount_paise": 15000,
                "description": "NBFC cash advance",
            },
        ]
        result = detect_risk_patterns(transactions)
        assert result["loan_app_pattern_flag"] is True
        assert result["loan_credit_count"] >= 2

    def test_emi_ratio_calculation(self):
        """EMI to income ratio calculated."""
        from src.engines.behaviour_engine.stress import detect_risk_patterns

        transactions = [
            {
                "type": "credit",
                "date_iso": "2025-01-01",
                "amount_paise": 1000000,
                "description": "Salary",
            },
            {
                "type": "debit",
                "date_iso": "2025-01-05",
                "amount_paise": 200000,
                "description": "EMI payment",
            },
            {
                "type": "debit",
                "date_iso": "2025-02-01",
                "amount_paise": 1000000,
                "description": "Salary",
            },
            {
                "type": "debit",
                "date_iso": "2025-02-05",
                "amount_paise": 200000,
                "description": "Loan repayment",
            },
        ]
        result = detect_risk_patterns(transactions)
        assert result["emi_ratio"] > 0
        assert result["emi_ratio"] < 1.0  # EMI should be less than income

    def test_no_false_positives(self):
        """Normal transactions don't trigger flags."""
        from src.engines.behaviour_engine.stress import detect_risk_patterns

        transactions = [
            {
                "type": "credit",
                "date_iso": "2025-01-01",
                "amount_paise": 1000000,
                "description": "Salary",
            },
            {
                "type": "debit",
                "date_iso": "2025-01-15",
                "amount_paise": 50000,
                "description": "Grocery shopping",
            },
            {
                "type": "debit",
                "date_iso": "2025-01-20",
                "amount_paise": 100000,
                "description": "Electricity bill",
            },
        ]
        result = detect_risk_patterns(transactions)
        assert result["upi_micro_spend_flag"] is False
        assert result["gambling_flag"] is False
        assert result["loan_app_pattern_flag"] is False
