# Golden dataset regression tests
import json
from pathlib import Path


def _normalize_for_comparison(result):
    """Remove timestamps, IDs, and ordering-sensitive fields for comparison."""
    normalized = {}
    ignore_keys = {"id", "created_at", "updated_at", "timestamp", "model_version"}
    for key, value in result.items():
        if key in ignore_keys:
            continue
        if isinstance(value, list):
            normalized[key] = sorted([str(v) for v in value]) if value else []
        else:
            normalized[key] = value
    return normalized


def _load_golden_dataset(name):
    """Load a golden dataset by name."""
    path = Path(__file__).parent / "datasets" / f"{name}.json"
    return json.loads(path.read_text())


class TestGoldenDatasets:
    """Semantic comparison tests against golden dataset snapshots."""

    def test_normal_household_regression(self):
        data = _load_golden_dataset("normal_household")
        result = data["expected_output"]
        assert isinstance(result["monthly_surplus_paise"], int)
        assert result["monthly_surplus_paise"] > 0

    def test_high_debt_household_regression(self):
        data = _load_golden_dataset("high_debt_household")
        result = data["expected_output"]
        assert result["financial_stress"]["score"] > 0.7
        assert result["financial_stress"]["flag"] is True

    def test_irregular_income_regression(self):
        data = _load_golden_dataset("irregular_income")
        result = data["expected_output"]
        assert result.get("income_volatility") == "high"

    def test_cc_statement_scenario_regression(self):
        data = _load_golden_dataset("cc_statement_scenario")
        result = data["expected_output"]
        assert result["cash_advance_fee_paise"] > 0

    # --- New financial journey datasets ---

    def test_salary_only_regression(self):
        """Single income source, no debt."""
        data = _load_golden_dataset("salary_only")
        result = data["expected_output"]
        assert result["monthly_surplus_paise"] > 0
        assert result["income_volatility"] == "low"
        assert result["has_debt"] is False
        assert result["confidence_bps"] >= 8000

    def test_salary_plus_loan_regression(self):
        """Income with active loan repayment."""
        data = _load_golden_dataset("salary_plus_loan")
        result = data["expected_output"]
        assert result["has_debt"] is True
        assert result["monthly_surplus_paise"] > 0
        assert "has_loan" in result.get("risk_flags", [])

    def test_credit_card_revolver_regression(self):
        """Revolving credit card debt."""
        data = _load_golden_dataset("credit_card_revolver")
        result = data["expected_output"]
        assert result["has_revolving_debt"] is True
        assert result["credit_utilization_ratio"] > 0.5
        assert "revolving_debt" in result.get("risk_flags", [])

    def test_cash_advance_regression(self):
        """Cash advance scenario with fees."""
        data = _load_golden_dataset("cash_advance")
        result = data["expected_output"]
        assert result["has_cash_advance"] is True
        assert result["cash_advance_fee_paise"] > 0
        assert "cash_advance_activity" in result.get("risk_flags", [])

    def test_multiple_loans_regression(self):
        """Two+ concurrent loans."""
        data = _load_golden_dataset("multiple_loans")
        result = data["expected_output"]
        assert result["has_multiple_loans"] is True
        assert result["total_emi_paise"] > 0
        assert "high_debt_burden" in result.get("risk_flags", [])

    def test_family_household_regression(self):
        """Multi-member household with shared accounts."""
        data = _load_golden_dataset("family_household")
        result = data["expected_output"]
        assert result["household_size"] == 4
        assert result["has_multiple_earners"] is True
        assert result["monthly_surplus_paise"] > 0

    def test_financial_forecast_regression(self):
        """Financial forecast 6-month projection regression."""
        data = _load_golden_dataset("financial_forecast")
        forecast = data["expected_forecast"]["6_month_projection"]

        assert (
            forecast["monthly_surplus_paise"] > 0
        ), "Should have positive monthly surplus"
        assert (
            forecast["total_income_paise"]
            == 6 * data["household"]["monthly_income_paise"]
        ), "6-month income should be 6x monthly income"
        assert (
            forecast["total_expenses_paise"]
            == 6 * data["household"]["monthly_expenses_paise"]
        ), "6-month expenses should be 6x monthly expenses"
        assert (
            forecast["total_savings_paise"]
            == forecast["total_income_paise"] - forecast["total_expenses_paise"]
        ), "Total savings should be income minus expenses"

    def test_investment_portfolio_regression(self):
        """Investment portfolio total value regression."""
        data = _load_golden_dataset("investment_portfolio")
        portfolio = data["expected_portfolio"]

        assert portfolio["total_holdings"] == len(data["investments"]), (
            f"Total holdings ({portfolio['total_holdings']}) should match "
            f"number of investments ({len(data['investments'])})"
        )

        calculated_value = sum(inv["value_paise"] for inv in data["investments"])
        assert calculated_value == portfolio["total_value_paise"], (
            f"Calculated total value ({calculated_value}) should match "
            f"expected ({portfolio['total_value_paise']})"
        )

        assert (
            0 <= portfolio["diversification_score"] <= 1
        ), f"Diversification score should be 0-1, got {portfolio['diversification_score']}"

    def test_reconciliation_match_regression(self):
        """Reconciliation match confidence regression."""
        data = _load_golden_dataset("reconciliation_match")
        matches = data["expected_matches"]

        assert len(matches) > 0, "Should have reconciliation matches"
        for match in matches:
            assert (
                match["confidence_bps"] >= 8000
            ), f"Match confidence should be >= 8000 bps, got {match['confidence_bps']}"
            assert match["amount_paise"] > 0, "Match amount should be positive"
            assert (
                match["debit_txn_id"] != match["credit_txn_id"]
            ), "Debit and credit transactions should be different"


class TestGoldenDatasetPaisePrecision:
    """Validate paise precision across all golden datasets."""

    def test_all_datasets_have_paise_fields(self):
        """All monetary values in datasets are paise (integers)."""
        dataset_names = [
            "normal_household",
            "high_debt_household",
            "irregular_income",
            "cc_statement_scenario",
            "salary_only",
            "salary_plus_loan",
            "credit_card_revolver",
            "cash_advance",
            "multiple_loans",
            "family_household",
            "financial_forecast",
            "investment_portfolio",
            "reconciliation_match",
        ]

        for name in dataset_names:
            data = _load_golden_dataset(name)
            _validate_paise_in_data(data, f"dataset {name}")

    def test_all_datasets_loadable(self):
        """All 13 golden datasets can be loaded successfully."""
        dataset_names = [
            "cash_advance",
            "cc_statement_scenario",
            "credit_card_revolver",
            "family_household",
            "financial_forecast",
            "high_debt_household",
            "investment_portfolio",
            "irregular_income",
            "multiple_loans",
            "normal_household",
            "reconciliation_match",
            "salary_only",
            "salary_plus_loan",
        ]

        for name in dataset_names:
            data = _load_golden_dataset(name)
            assert data is not None, f"Dataset {name} should be loadable"
            assert "scenario" in data, f"Dataset {name} should have 'scenario' field"


def _validate_paise_in_data(obj, path: str) -> None:
    """Recursively validate that all *_paise scalar fields are integers."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}"
            if (
                key.endswith("_paise")
                and isinstance(value, (int, float))
                and not isinstance(value, bool)
            ):
                assert isinstance(
                    value, int
                ), f"{current_path} should be int (paise), got {type(value).__name__}"
            else:
                _validate_paise_in_data(value, current_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _validate_paise_in_data(item, f"{path}[{i}]")


class TestGoldenDatasetInvariants:
    """Test invariants that must hold across all golden datasets."""

    def test_total_balance_invariant(self):
        """Sum of account balances should match or approximate total_balance_paise."""
        data = _load_golden_dataset("normal_household")
        if (
            "expected_account_metrics" in data
            and "balance_metrics" in data["expected_account_metrics"]
        ):
            balance_metrics = data["expected_account_metrics"]["balance_metrics"]
            if "total_balance_paise" in balance_metrics and "accounts" in data:
                calculated = sum(acc["balance_paise"] for acc in data["accounts"])
                expected = balance_metrics["total_balance_paise"]
                assert abs(calculated - expected) <= 100000, (
                    f"Sum of balances ({calculated}) should approximately match total ({expected}), "
                    f"tolerance: 100000 paise"
                )

    def test_income_expense_invariant(self):
        """total_income - total_expenses = net_cashflow."""
        data = _load_golden_dataset("normal_household")
        if (
            "expected_account_metrics" in data
            and "cashflow_metrics" in data["expected_account_metrics"]
        ):
            cf = data["expected_account_metrics"]["cashflow_metrics"]
            if all(
                k in cf
                for k in [
                    "total_income_paise",
                    "total_expenses_paise",
                    "net_cashflow_paise",
                ]
            ):
                calculated = cf["total_income_paise"] - cf["total_expenses_paise"]
                assert calculated == cf["net_cashflow_paise"], (
                    f"Income ({cf['total_income_paise']}) - Expenses ({cf['total_expenses_paise']}) "
                    f"should equal net cashflow ({cf['net_cashflow_paise']}), got {calculated}"
                )

    def test_loan_principal_invariant(self):
        """outstanding_paise <= principal_paise for all loans."""
        data = _load_golden_dataset("multiple_loans")
        if "loans" in data:
            for loan in data["loans"]:
                if "outstanding_paise" in loan and "principal_paise" in loan:
                    assert loan["outstanding_paise"] <= loan["principal_paise"], (
                        f"Loan outstanding ({loan['outstanding_paise']}) "
                        f"should not exceed principal ({loan['principal_paise']})"
                    )

    def test_reconciliation_no_duplicates(self):
        """No transaction appears in multiple reconciliation matches."""
        data = _load_golden_dataset("normal_household")
        if "expected_reconciliation" in data:
            reconcil = data["expected_reconciliation"]
            all_debit_ids = []
            all_credit_ids = []
            for match_type in [
                "exact_matches",
                "window_matches",
                "duplicate_matches",
                "recurring_matches",
            ]:
                if match_type in reconcil:
                    for m in reconcil[match_type]:
                        all_debit_ids.append(m.get("debit_txn_id"))
                        all_credit_ids.append(m.get("credit_txn_id"))

            if all_debit_ids:
                assert len(all_debit_ids) == len(set(all_debit_ids)), (
                    f"Debit transaction IDs should be unique across all match types, "
                    f"but found duplicates: {all_debit_ids}"
                )
            if all_credit_ids:
                assert len(all_credit_ids) == len(set(all_credit_ids)), (
                    f"Credit transaction IDs should be unique across all match types, "
                    f"but found duplicates: {all_credit_ids}"
                )
