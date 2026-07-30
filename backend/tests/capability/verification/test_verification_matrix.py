"""Capability tests for verification matrix.

Tests the verification matrix engine and matrix generation functionality.
"""

import json
from datetime import datetime

import pytest

from src.verification.intelligence.verification_matrix import (
    VerificationMatrix,
    VerificationMatrixEngine,
)


@pytest.fixture
def matrix_engine():
    """Fixture: Verification matrix engine instance."""
    return VerificationMatrixEngine()


def test_matrix_engine_initialization(matrix_engine):
    """Test: Verification matrix engine initializes correctly."""
    assert matrix_engine.capability_data == {}
    assert len(matrix_engine.test_results) == 0
    assert matrix_engine.risk_data == {}


def test_load_capability_data(matrix_engine):
    """Test: Capability data is loaded correctly."""
    capability_data = {
        "financial_events": {
            "id": "financial_events",
            "name": "Financial Events",
        }
    }

    matrix_engine.load_capability_data(capability_data)
    assert matrix_engine.capability_data == capability_data


def test_load_test_results(matrix_engine):
    """Test: Test results are loaded correctly."""
    test_results = [
        {
            "capability_id": "financial_events",
            "test_type": "capability",
            "status": "passed",
        }
    ]

    matrix_engine.load_test_results(test_results)
    assert len(matrix_engine.test_results) == 1


def test_load_risk_data(matrix_engine):
    """Test: Risk data is loaded correctly."""
    risk_data = {
        "entries": [{"capability_id": "financial_events", "risk_level": "MEDIUM"}]
    }

    matrix_engine.load_risk_data(risk_data)
    assert matrix_engine.risk_data == risk_data


def test_verification_status_generation(matrix_engine):
    """Test: Verification status is generated correctly."""
    # Load sample data
    matrix_engine.load_capability_data(
        {
            "financial_events": {
                "id": "financial_events",
                "name": "Financial Events",
            }
        }
    )

    matrix_engine.load_test_results(
        [
            {
                "capability_id": "financial_events",
                "test_type": "capability",
                "status": "passed",
                "timestamp": datetime.now().isoformat(),
            }
        ]
    )

    matrix_engine.load_risk_data(
        {"entries": [{"capability_id": "financial_events", "risk_level": "MEDIUM"}]}
    )

    status_list = matrix_engine.generate_verification_status()

    assert len(status_list) == 1
    status = status_list[0]

    assert status.capability_id == "financial_events"
    assert status.capability_name == "Financial Events"
    assert status.verification_coverage > 0
    assert "capability" in status.test_types
    assert status.risk_level == "MEDIUM"
    assert status.verification_status == "VERIFIED"


def test_verification_matrix_generation(matrix_engine):
    """Test: Verification matrix is generated correctly."""
    # Load sample data
    matrix_engine.load_capability_data(
        {
            "financial_events": {
                "id": "financial_events",
                "name": "Financial Events",
            },
            "credit_cards": {
                "id": "credit_cards",
                "name": "Credit Cards",
            },
        }
    )

    matrix_engine.load_test_results(
        [
            {
                "capability_id": "financial_events",
                "test_type": "capability",
                "status": "passed",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "capability_id": "credit_cards",
                "test_type": "contract",
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "critical": True,
            },
        ]
    )

    matrix_engine.load_risk_data(
        {
            "entries": [
                {"capability_id": "financial_events", "risk_level": "MEDIUM"},
                {"capability_id": "credit_cards", "risk_level": "HIGH"},
            ]
        }
    )

    matrix = matrix_engine.generate_verification_matrix()

    assert isinstance(matrix, VerificationMatrix)
    assert len(matrix.capabilities) == 2
    assert matrix.overall_verification_coverage > 0
    assert matrix.overall_test_coverage > 0
    assert matrix.high_risk_capabilities == 1
    assert matrix.fully_verified_capabilities == 1
    assert matrix.total_capabilities == 2
    assert "financial_events" in matrix.verification_trends
    assert "credit_cards" in matrix.verification_trends


def test_sample_matrix_generation(tmp_path):
    """Test: Sample verification matrix is generated correctly."""
    engine = VerificationMatrixEngine()
    output_path = tmp_path / "verification-matrix.json"

    engine.generate_sample_matrix(str(output_path))

    assert output_path.exists()

    with open(output_path) as f:
        matrix_data = json.load(f)

    assert "capabilities" in matrix_data
    assert "overall_verification_coverage" in matrix_data
    assert "overall_test_coverage" in matrix_data
    assert "verification_trends" in matrix_data

    assert len(matrix_data["capabilities"]) > 0
    assert matrix_data["overall_verification_coverage"] > 0
    assert matrix_data["overall_verification_coverage"] <= 100
