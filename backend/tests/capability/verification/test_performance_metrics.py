"""Capability tests for verification performance metrics.

Tests the metrics engine and performance reporting functionality.
"""

import json

import pytest

from src.verification.intelligence.metrics_engine import (
    CapabilityValidationMetric,
    CoverageMetric,
    MetricsEngine,
    RiskAssessmentMetric,
    SelectiveExecutionMetric,
    TestPerformanceMetric,
    VerificationPerformanceReport,
)


@pytest.fixture
def metrics_engine():
    """Fixture: Metrics engine instance."""
    return MetricsEngine()


def test_metrics_engine_initialization(metrics_engine):
    """Test: Metrics engine initializes correctly."""
    assert len(metrics_engine.metrics) == 0


def test_test_performance_metrics_generation(metrics_engine):
    """Test: Test performance metrics are generated correctly."""
    test_results = {
        "unit": {
            "executions": [
                {"execution_time_ms": 50},
                {"execution_time_ms": 60},
                {"execution_time_ms": 45},
            ]
        }
    }

    metrics_engine.generate_test_performance_metrics(test_results)

    assert len(metrics_engine.metrics) == 1
    metric = metrics_engine.metrics[0]

    assert isinstance(metric, TestPerformanceMetric)
    assert metric.test_type == "unit"
    assert metric.test_count == 3
    assert metric.avg_execution_time_ms == 51.666666666666664
    assert metric.max_execution_time_ms == 60
    assert metric.min_execution_time_ms == 45


def test_coverage_metrics_generation(metrics_engine):
    """Test: Coverage metrics are generated correctly."""
    coverage_data = {"line": {"covered": 850, "total": 1000}}

    metrics_engine.generate_coverage_metrics(coverage_data)

    assert len(metrics_engine.metrics) == 1
    metric = metrics_engine.metrics[0]

    assert isinstance(metric, CoverageMetric)
    assert metric.coverage_type == "line"
    assert metric.covered == 850
    assert metric.total == 1000
    assert metric.percentage == 85.0


def test_risk_assessment_metrics_generation(metrics_engine):
    """Test: Risk assessment metrics are generated correctly."""
    risk_data = {
        "HIGH": {
            "true_positives": 15,
            "false_positives": 1,
            "false_negatives": 0,
        }
    }

    metrics_engine.generate_risk_assessment_metrics(risk_data)

    assert len(metrics_engine.metrics) == 1
    metric = metrics_engine.metrics[0]

    assert isinstance(metric, RiskAssessmentMetric)
    assert metric.risk_level == "HIGH"
    assert metric.true_positives == 15
    assert metric.false_positives == 1
    assert metric.false_negatives == 0
    assert metric.precision == 0.9375
    assert metric.recall == 1.0


def test_selective_execution_metrics_generation(metrics_engine):
    """Test: Selective execution metrics are generated correctly."""
    execution_data = {
        "selective": {
            "jobs_executed": 4,
            "jobs_skipped": 6,
            "time_saved_seconds": 1200,
            "total_jobs": 10,
        }
    }

    metrics_engine.generate_selective_execution_metrics(execution_data)

    assert len(metrics_engine.metrics) == 1
    metric = metrics_engine.metrics[0]

    assert isinstance(metric, SelectiveExecutionMetric)
    assert metric.strategy == "selective"
    assert metric.jobs_executed == 4
    assert metric.jobs_skipped == 6
    assert metric.execution_time_saved_seconds == 1200
    assert metric.efficiency_percentage == 60.0


def test_capability_validation_metrics_generation(metrics_engine):
    """Test: Capability validation metrics are generated correctly."""
    validation_results = [
        {
            "capability_id": "financial_events",
            "validation_passed": True,
            "validation_time_ms": 850,
            "issues_found": 0,
            "critical_issues": 0,
        }
    ]

    metrics_engine.generate_capability_validation_metrics(validation_results)

    assert len(metrics_engine.metrics) == 1
    metric = metrics_engine.metrics[0]

    assert isinstance(metric, CapabilityValidationMetric)
    assert metric.capability_id == "financial_events"
    assert metric.validation_passed is True
    assert metric.validation_time_ms == 850
    assert metric.issues_found == 0
    assert metric.critical_issues == 0


def test_performance_report_generation(metrics_engine):
    """Test: Performance report is generated correctly."""
    # Add sample metrics
    metrics_engine.generate_test_performance_metrics(
        {"unit": {"executions": [{"execution_time_ms": 50}]}}
    )
    metrics_engine.generate_coverage_metrics({"line": {"covered": 850, "total": 1000}})
    metrics_engine.generate_risk_assessment_metrics(
        {
            "HIGH": {
                "true_positives": 15,
                "false_positives": 1,
                "false_negatives": 0,
            }
        }
    )
    metrics_engine.generate_selective_execution_metrics(
        {
            "selective": {
                "jobs_executed": 4,
                "jobs_skipped": 6,
                "time_saved_seconds": 1200,
                "total_jobs": 10,
            }
        }
    )
    metrics_engine.generate_capability_validation_metrics(
        [
            {
                "capability_id": "financial_events",
                "validation_passed": True,
                "validation_time_ms": 850,
                "issues_found": 0,
                "critical_issues": 0,
            }
        ]
    )

    report = metrics_engine.generate_performance_report()

    assert isinstance(report, VerificationPerformanceReport)
    assert len(report.test_performance) == 1
    assert len(report.coverage) == 1
    assert len(report.risk_assessment) == 1
    assert len(report.selective_execution) == 1
    assert len(report.capability_validation) == 1
    assert report.overall_score > 0
    assert report.overall_score <= 100


def test_sample_report_generation(tmp_path):
    """Test: Sample performance report is generated correctly."""
    engine = MetricsEngine()
    output_path = tmp_path / "verification-performance.json"

    engine.generate_sample_report(str(output_path))

    assert output_path.exists()

    with open(output_path) as f:
        report_data = json.load(f)

    assert "test_performance" in report_data
    assert "coverage" in report_data
    assert "risk_assessment" in report_data
    assert "selective_execution" in report_data
    assert "capability_validation" in report_data
    assert "overall_score" in report_data

    assert report_data["overall_score"] > 0
    assert report_data["overall_score"] <= 100
