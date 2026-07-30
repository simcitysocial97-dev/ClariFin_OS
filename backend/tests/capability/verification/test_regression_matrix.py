"""Capability tests for verification regression matrix.

Tests the regression engine and matrix generation functionality.
"""

import json
from datetime import datetime

import pytest

from src.verification.intelligence.regression_engine import (
    RegressionEngine,
    RegressionTestMatrix,
)


@pytest.fixture
def regression_engine():
    """Fixture: Regression engine instance."""
    return RegressionEngine()


def test_regression_engine_initialization(regression_engine):
    """Test: Regression engine initializes correctly."""
    assert len(regression_engine.test_results) == 0


def test_add_test_results(regression_engine):
    """Test: Test results are added correctly."""
    test_results = [
        {
            "capability_id": "financial_events",
            "capability_name": "Financial Events",
            "test_type": "capability",
            "status": "passed",
            "timestamp": datetime.now().isoformat(),
            "risk_level": "MEDIUM",
        }
    ]

    regression_engine.add_test_results(test_results)
    assert len(regression_engine.test_results) == 1


def test_capability_test_results_generation(regression_engine):
    """Test: Capability test results are generated correctly."""
    test_results = [
        {
            "capability_id": "financial_events",
            "capability_name": "Financial Events",
            "test_type": "capability",
            "status": "passed",
            "timestamp": datetime.now().isoformat(),
            "risk_level": "MEDIUM",
        },
        {
            "capability_id": "financial_events",
            "capability_name": "Financial Events",
            "test_type": "capability",
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
            "risk_level": "MEDIUM",
            "critical": True,
        },
        {
            "capability_id": "credit_cards",
            "capability_name": "Credit Cards",
            "test_type": "contract",
            "status": "passed",
            "timestamp": datetime.now().isoformat(),
            "risk_level": "HIGH",
        },
    ]

    regression_engine.add_test_results(test_results)
    results = regression_engine.generate_capability_test_results()

    assert len(results) == 2  # financial_events + credit_cards

    # Check financial_events capability
    fe_result = next(r for r in results if r.capability_id == "financial_events")
    assert fe_result.capability_name == "Financial Events"
    assert fe_result.test_type == "capability"
    assert fe_result.test_count == 2
    assert fe_result.passed == 1
    assert fe_result.failed == 1
    assert fe_result.pass_rate == 50.0
    assert fe_result.critical_failures == 1


def test_regression_matrix_generation(regression_engine):
    """Test: Regression matrix is generated correctly."""
    test_results = [
        {
            "capability_id": "financial_events",
            "capability_name": "Financial Events",
            "test_type": "capability",
            "status": "passed",
            "timestamp": datetime.now().isoformat(),
            "risk_level": "MEDIUM",
        },
        {
            "capability_id": "financial_events",
            "capability_name": "Financial Events",
            "test_type": "property",
            "status": "passed",
            "timestamp": datetime.now().isoformat(),
            "risk_level": "MEDIUM",
        },
        {
            "capability_id": "credit_cards",
            "capability_name": "Credit Cards",
            "test_type": "capability",
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
            "risk_level": "HIGH",
            "critical": True,
        },
    ]

    regression_engine.add_test_results(test_results)
    matrix = regression_engine.generate_regression_matrix()

    assert isinstance(matrix, RegressionTestMatrix)
    assert (
        len(matrix.capabilities) == 3
    )  # financial_events(capability) + financial_events(property) + credit_cards
    assert matrix.overall_pass_rate > 0
    assert matrix.overall_pass_rate <= 100
    assert matrix.total_tests == 3
    assert matrix.high_risk_failures == 1  # credit_cards failure
    assert matrix.coverage_percentage > 0
    assert "financial_events" in matrix.historical_trends
    assert "credit_cards" in matrix.historical_trends


def test_sample_matrix_generation(tmp_path):
    """Test: Sample regression matrix is generated correctly."""
    engine = RegressionEngine()
    output_path = tmp_path / "regression-matrix.json"

    engine.generate_sample_matrix(str(output_path))

    assert output_path.exists()

    with open(output_path) as f:
        matrix_data = json.load(f)

    assert "capabilities" in matrix_data
    assert "overall_pass_rate" in matrix_data
    assert "high_risk_failures" in matrix_data
    assert "historical_trends" in matrix_data

    assert len(matrix_data["capabilities"]) > 0
    assert matrix_data["overall_pass_rate"] > 0
    assert matrix_data["overall_pass_rate"] <= 100
