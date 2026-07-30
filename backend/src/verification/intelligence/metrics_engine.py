"""Verification Intelligence Metrics Engine.

Generates performance metrics for verification intelligence including:
- Test execution time
- Coverage metrics
- Risk assessment accuracy
- Selective execution efficiency
- Capability validation performance
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass
class VerificationMetric:
    """Base dataclass for verification metrics."""

    timestamp: str
    metric_name: str
    value: float
    unit: str
    tags: dict[str, str]


@dataclass
class TestPerformanceMetric(VerificationMetric):
    """Test execution performance metrics."""

    test_type: str  # unit, property, contract, capability, invariant
    test_count: int
    avg_execution_time_ms: float
    max_execution_time_ms: float
    min_execution_time_ms: float


@dataclass
class CoverageMetric(VerificationMetric):
    """Code coverage metrics."""

    coverage_type: str  # line, branch, capability
    covered: int
    total: int
    percentage: float


@dataclass
class RiskAssessmentMetric(VerificationMetric):
    """Risk assessment accuracy metrics."""

    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float


@dataclass
class SelectiveExecutionMetric(VerificationMetric):
    """Selective execution efficiency metrics."""

    strategy: str  # full, selective
    jobs_executed: int
    jobs_skipped: int
    execution_time_saved_seconds: float
    efficiency_percentage: float


@dataclass
class CapabilityValidationMetric(VerificationMetric):
    """Capability validation performance metrics."""

    capability_id: str
    validation_passed: bool
    validation_time_ms: float
    issues_found: int
    critical_issues: int


@dataclass
class VerificationPerformanceReport:
    """Comprehensive verification performance report."""

    generated_at: str
    time_period: str  # e.g., "last_24h", "last_week", "last_month"
    test_performance: list[TestPerformanceMetric]
    coverage: list[CoverageMetric]
    risk_assessment: list[RiskAssessmentMetric]
    selective_execution: list[SelectiveExecutionMetric]
    capability_validation: list[CapabilityValidationMetric]
    overall_score: float  # 0-100


class MetricsEngine:
    """Verification Intelligence Metrics Engine.

    Collects and generates performance metrics for verification intelligence.
    """

    def __init__(self) -> None:
        self.metrics: list[VerificationMetric] = []

    def add_metric(self, metric: VerificationMetric) -> None:
        """Add a metric to the collection."""
        self.metrics.append(metric)

    def generate_test_performance_metrics(self, test_results: dict[str, Any]) -> None:
        """Generate test performance metrics from test results."""
        for test_type, results in test_results.items():
            if not results.get("executions"):
                continue

            execution_times = [
                exec["execution_time_ms"] for exec in results["executions"]
            ]
            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)

            metric = TestPerformanceMetric(
                timestamp=datetime.now().isoformat(),
                metric_name=f"test_performance_{test_type}",
                value=avg_time,
                unit="ms",
                tags={"test_type": test_type},
                test_type=test_type,
                test_count=len(execution_times),
                avg_execution_time_ms=avg_time,
                max_execution_time_ms=max_time,
                min_execution_time_ms=min_time,
            )
            self.add_metric(metric)

    def generate_coverage_metrics(self, coverage_data: dict[str, Any]) -> None:
        """Generate coverage metrics from coverage data."""
        for coverage_type, data in coverage_data.items():
            if data["total"] == 0:
                continue

            percentage = (data["covered"] / data["total"]) * 100
            metric = CoverageMetric(
                timestamp=datetime.now().isoformat(),
                metric_name=f"coverage_{coverage_type}",
                value=percentage,
                unit="%",
                tags={"coverage_type": coverage_type},
                coverage_type=coverage_type,
                covered=data["covered"],
                total=data["total"],
                percentage=percentage,
            )
            self.add_metric(metric)

    def generate_risk_assessment_metrics(
        self, risk_data: dict[str, dict[str, int]]
    ) -> None:
        """Generate risk assessment accuracy metrics."""
        for risk_level, counts in risk_data.items():
            total = (
                counts["true_positives"]
                + counts["false_positives"]
                + counts["false_negatives"]
            )
            if total == 0:
                continue

            precision = counts["true_positives"] / (
                counts["true_positives"] + counts["false_positives"]
            )
            recall = counts["true_positives"] / (
                counts["true_positives"] + counts["false_negatives"]
            )

            metric = RiskAssessmentMetric(
                timestamp=datetime.now().isoformat(),
                metric_name=f"risk_assessment_{risk_level.lower()}",
                value=precision,  # Using precision as primary value
                unit="ratio",
                tags={"risk_level": risk_level},
                risk_level=risk_level,
                true_positives=counts["true_positives"],
                false_positives=counts["false_positives"],
                false_negatives=counts["false_negatives"],
                precision=precision,
                recall=recall,
            )
            self.add_metric(metric)

    def generate_selective_execution_metrics(
        self, execution_data: dict[str, Any]
    ) -> None:
        """Generate selective execution efficiency metrics."""
        for strategy, data in execution_data.items():
            if data["total_jobs"] == 0:
                continue

            efficiency = (
                (data["jobs_skipped"] / data["total_jobs"]) * 100
                if data["total_jobs"] > 0
                else 0
            )

            metric = SelectiveExecutionMetric(
                timestamp=datetime.now().isoformat(),
                metric_name=f"selective_execution_{strategy.lower()}",
                value=efficiency,
                unit="%",
                tags={"strategy": strategy},
                strategy=strategy,
                jobs_executed=data["jobs_executed"],
                jobs_skipped=data["jobs_skipped"],
                execution_time_saved_seconds=data["time_saved_seconds"],
                efficiency_percentage=efficiency,
            )
            self.add_metric(metric)

    def generate_capability_validation_metrics(
        self, validation_results: list[dict[str, Any]]
    ) -> None:
        """Generate capability validation performance metrics."""
        for result in validation_results:
            metric = CapabilityValidationMetric(
                timestamp=datetime.now().isoformat(),
                metric_name=f"capability_validation_{result['capability_id']}",
                value=result["validation_time_ms"],
                unit="ms",
                tags={"capability_id": result["capability_id"]},
                capability_id=result["capability_id"],
                validation_passed=result["validation_passed"],
                validation_time_ms=result["validation_time_ms"],
                issues_found=result["issues_found"],
                critical_issues=result["critical_issues"],
            )
            self.add_metric(metric)

    def generate_performance_report(
        self, time_period: str = "last_24h"
    ) -> VerificationPerformanceReport:
        """Generate a comprehensive verification performance report."""
        # Calculate overall score (weighted average)
        overall_score = self._calculate_overall_score()

        report = VerificationPerformanceReport(
            generated_at=datetime.now().isoformat(),
            time_period=time_period,
            test_performance=[
                m for m in self.metrics if isinstance(m, TestPerformanceMetric)
            ],
            coverage=[m for m in self.metrics if isinstance(m, CoverageMetric)],
            risk_assessment=[
                m for m in self.metrics if isinstance(m, RiskAssessmentMetric)
            ],
            selective_execution=[
                m for m in self.metrics if isinstance(m, SelectiveExecutionMetric)
            ],
            capability_validation=[
                m for m in self.metrics if isinstance(m, CapabilityValidationMetric)
            ],
            overall_score=overall_score,
        )

        return report

    def _calculate_overall_score(self) -> float:
        """Calculate overall verification performance score (0-100)."""
        if not self.metrics:
            return 0.0

        # Weighted scoring based on metric types
        weights = {
            "test_performance": 0.2,
            "coverage": 0.3,
            "risk_assessment": 0.2,
            "selective_execution": 0.1,
            "capability_validation": 0.2,
        }

        scores: dict[str, list[float]] = {
            "test_performance": [],
            "coverage": [],
            "risk_assessment": [],
            "selective_execution": [],
            "capability_validation": [],
        }

        for metric in self.metrics:
            if isinstance(metric, TestPerformanceMetric):
                # Higher is worse for execution time, so invert
                normalized = max(0, 100 - (metric.avg_execution_time_ms / 10))
                scores["test_performance"].append(normalized)
            elif isinstance(metric, CoverageMetric):
                scores["coverage"].append(metric.percentage)
            elif isinstance(metric, RiskAssessmentMetric):
                scores["risk_assessment"].append(metric.precision * 100)
            elif isinstance(metric, SelectiveExecutionMetric):
                scores["selective_execution"].append(metric.efficiency_percentage)
            elif isinstance(metric, CapabilityValidationMetric):
                # Score based on validation success and issues found
                success_score = 100 if metric.validation_passed else 0
                issue_penalty = min(50, metric.issues_found * 2)
                scores["capability_validation"].append(
                    max(0, success_score - issue_penalty)
                )

        # Calculate weighted average
        total_score = 0.0
        total_weight = 0.0

        for metric_type, weight in weights.items():
            if scores[metric_type]:
                avg_score = sum(scores[metric_type]) / len(scores[metric_type])
                total_score += avg_score * weight
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def save_report(
        self, report: VerificationPerformanceReport, output_path: str
    ) -> None:
        """Save performance report to JSON file."""
        with open(output_path, "w") as f:
            json.dump(asdict(report), f, indent=2)

    def generate_sample_report(self, output_path: str) -> None:
        """Generate a sample performance report for testing."""
        # Sample test performance data
        self.generate_test_performance_metrics(
            {
                "unit": {
                    "executions": [
                        {"execution_time_ms": 50},
                        {"execution_time_ms": 60},
                        {"execution_time_ms": 45},
                    ]
                },
                "property": {
                    "executions": [
                        {"execution_time_ms": 200},
                        {"execution_time_ms": 210},
                        {"execution_time_ms": 190},
                    ]
                },
                "contract": {
                    "executions": [
                        {"execution_time_ms": 150},
                        {"execution_time_ms": 160},
                        {"execution_time_ms": 140},
                    ]
                },
                "capability": {
                    "executions": [
                        {"execution_time_ms": 300},
                        {"execution_time_ms": 320},
                        {"execution_time_ms": 290},
                    ]
                },
            }
        )

        # Sample coverage data
        self.generate_coverage_metrics(
            {
                "line": {"covered": 850, "total": 1000},
                "branch": {"covered": 720, "total": 900},
                "capability": {"covered": 15, "total": 20},
            }
        )

        # Sample risk assessment data
        self.generate_risk_assessment_metrics(
            {
                "LOW": {
                    "true_positives": 50,
                    "false_positives": 2,
                    "false_negatives": 1,
                },
                "MEDIUM": {
                    "true_positives": 30,
                    "false_positives": 3,
                    "false_negatives": 2,
                },
                "HIGH": {
                    "true_positives": 15,
                    "false_positives": 1,
                    "false_negatives": 0,
                },
                "CRITICAL": {
                    "true_positives": 5,
                    "false_positives": 0,
                    "false_negatives": 0,
                },
            }
        )

        # Sample selective execution data
        self.generate_selective_execution_metrics(
            {
                "full": {
                    "jobs_executed": 10,
                    "jobs_skipped": 0,
                    "time_saved_seconds": 0,
                    "total_jobs": 10,
                },
                "selective": {
                    "jobs_executed": 4,
                    "jobs_skipped": 6,
                    "time_saved_seconds": 1200,
                    "total_jobs": 10,
                },
            }
        )

        # Sample capability validation data
        self.generate_capability_validation_metrics(
            [
                {
                    "capability_id": "financial_events",
                    "validation_passed": True,
                    "validation_time_ms": 850,
                    "issues_found": 0,
                    "critical_issues": 0,
                },
                {
                    "capability_id": "credit_cards",
                    "validation_passed": True,
                    "validation_time_ms": 1200,
                    "issues_found": 2,
                    "critical_issues": 0,
                },
                {
                    "capability_id": "debt_management",
                    "validation_passed": False,
                    "validation_time_ms": 950,
                    "issues_found": 5,
                    "critical_issues": 1,
                },
            ]
        )

        # Generate and save report
        report = self.generate_performance_report("sample")
        self.save_report(report, output_path)
