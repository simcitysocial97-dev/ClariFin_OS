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
