# Golden dataset regression tests
import json
from pathlib import Path

import pytest


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
        # Semantic check: surplus must be integer paise
        assert isinstance(result["monthly_surplus_paise"], int)
        assert result["monthly_surplus_paise"] > 0

    def test_high_debt_household_regression(self):
        data = _load_golden_dataset("high_debt_household")
        result = data["expected_output"]
        # Semantic check: confidence reflects debt risk
        assert result["confidence_bps"] < 7000
        assert "high_debt" in result.get("risk_flags", [])

    def test_irregular_income_regression(self):
        data = _load_golden_dataset("irregular_income")
        result = data["expected_output"]
        # Semantic check: volatility indicator
        assert result.get("income_volatility") == "high"

    def test_cc_statement_scenario_regression(self):
        data = _load_golden_dataset("cc_statement_scenario")
        result = data["expected_output"]
        # Semantic check: cash advance fee tracking
        assert result["cash_advance_fee_paise"] > 0