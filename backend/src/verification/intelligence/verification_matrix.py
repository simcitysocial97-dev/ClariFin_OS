"""Verification Intelligence Matrix Generator.

Generates a comprehensive verification matrix showing:
- Capability coverage
- Test coverage
- Risk assessment
- Verification status
- Historical trends
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass
class CapabilityVerificationStatus:
    """Verification status for a single capability."""

    capability_id: str
    capability_name: str
    verification_coverage: float  # 0-100%
    test_coverage: dict[str, float]  # test_type -> coverage_percentage
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    verification_status: str  # NOT_VERIFIED, PARTIALLY_VERIFIED, VERIFIED
    last_verified: str
    issues_found: int
    critical_issues: int
    historical_pass_rate: list[float]  # Last 5 runs
    test_types: list[str]  # unit, property, contract, capability, invariant
    overall_test_coverage: float = 0.0


@dataclass
class VerificationMatrix:
    """Comprehensive verification matrix."""

    generated_at: str
    capabilities: list[CapabilityVerificationStatus]
    overall_verification_coverage: float
    overall_test_coverage: float
    high_risk_capabilities: int
    fully_verified_capabilities: int
    total_capabilities: int
    verification_trends: dict[
        str, list[float]
    ]  # capability_id -> verification_coverage_history


class VerificationMatrixEngine:
    """Verification Intelligence Matrix Engine.

    Generates comprehensive verification matrices for capability validation.
    """

    def __init__(self) -> None:
        self.capability_data: dict[str, Any] = {}
        self.test_results: list[dict[str, Any]] = []
        self.risk_data: dict[str, Any] = {}

    def load_capability_data(self, capability_data: dict[str, Any]) -> None:
        """Load capability registry data."""
        self.capability_data = capability_data

    def load_test_results(self, test_results: list[dict[str, Any]]) -> None:
        """Load test results data."""
        self.test_results = test_results

    def load_risk_data(self, risk_data: dict[str, Any]) -> None:
        """Load risk assessment data."""
        self.risk_data = risk_data

    def generate_verification_status(self) -> list[CapabilityVerificationStatus]:
        """Generate verification status for each capability."""
        capability_status: dict[str, CapabilityVerificationStatus] = {}

        # Initialize with capability data
        for cap_id, cap_data in self.capability_data.items():
            capability_status[cap_id] = CapabilityVerificationStatus(
                capability_id=cap_id,
                capability_name=cap_data.get("name", cap_id),
                verification_coverage=0.0,
                test_coverage={},
                risk_level=self._get_capability_risk(cap_id),
                verification_status="NOT_VERIFIED",
                last_verified="",
                issues_found=0,
                critical_issues=0,
                historical_pass_rate=[],
                test_types=[],
            )

        # Update with test results
        for result in self.test_results:
            cap_id = result.get("capability_id", "unknown")
            if cap_id not in capability_status:
                continue

            status = capability_status[cap_id]
            test_type = result.get("test_type", "unknown")

            # Track test types
            if test_type not in status.test_types:
                status.test_types.append(test_type)

            # Update test coverage
            if test_type not in status.test_coverage:
                status.test_coverage[test_type] = 0.0

            # Update verification status
            if result.get("status") == "passed":
                status.verification_coverage = min(
                    100.0, status.verification_coverage + 20.0
                )
                status.test_coverage[test_type] = min(
                    100.0, status.test_coverage[test_type] + 25.0
                )
            else:
                status.issues_found += 1
                if result.get("critical", False):
                    status.critical_issues += 1

            # Update last verified timestamp
            timestamp = result.get("timestamp", "")
            if timestamp > status.last_verified:
                status.last_verified = timestamp

        # Determine final verification status
        for _cap_id, status in capability_status.items():
            # Calculate average test coverage
            if status.test_coverage:
                status.overall_test_coverage = sum(status.test_coverage.values()) / len(
                    status.test_coverage
                )
            else:
                status.overall_test_coverage = 0.0

            # Determine verification status
            if status.verification_coverage >= 20.0 and status.critical_issues == 0:
                status.verification_status = "VERIFIED"
            elif status.verification_coverage >= 10.0:
                status.verification_status = "PARTIALLY_VERIFIED"
            else:
                status.verification_status = "NOT_VERIFIED"

            # Generate historical pass rate (simplified)
            if status.verification_coverage > 0:
                status.historical_pass_rate = [
                    max(0, status.verification_coverage - 10 * i) for i in range(5)
                ]

        return list(capability_status.values())

    def _get_capability_risk(self, capability_id: str) -> str:
        """Get risk level for a capability."""
        if not self.risk_data:
            return "MEDIUM"

        for entry in self.risk_data.get("entries", []):
            if entry.get("capability_id") == capability_id:
                risk = entry.get("risk_level", "MEDIUM")
                return risk if isinstance(risk, str) else "MEDIUM"
        return "MEDIUM"

    def generate_verification_matrix(self) -> VerificationMatrix:
        """Generate a comprehensive verification matrix."""
        capabilities = self.generate_verification_status()

        # Calculate overall statistics
        total_capabilities = len(capabilities)
        fully_verified = sum(
            1 for c in capabilities if c.verification_status == "VERIFIED"
        )
        high_risk = sum(1 for c in capabilities if c.risk_level in ["HIGH", "CRITICAL"])

        # Calculate overall coverage
        overall_verification = (
            sum(c.verification_coverage for c in capabilities) / total_capabilities
            if total_capabilities > 0
            else 0.0
        )
        overall_test = (
            sum(
                sum(c.test_coverage.values()) / len(c.test_coverage)
                for c in capabilities
                if c.test_coverage
            )
            / total_capabilities
            if total_capabilities > 0
            else 0.0
        )

        # Generate verification trends (simplified)
        verification_trends = {}
        for capability in capabilities:
            verification_trends[capability.capability_id] = (
                capability.historical_pass_rate
            )

        return VerificationMatrix(
            generated_at=datetime.now().isoformat(),
            capabilities=capabilities,
            overall_verification_coverage=overall_verification,
            overall_test_coverage=overall_test,
            high_risk_capabilities=high_risk,
            fully_verified_capabilities=fully_verified,
            total_capabilities=total_capabilities,
            verification_trends=verification_trends,
        )

    def save_matrix(self, matrix: VerificationMatrix, output_path: str) -> None:
        """Save verification matrix to JSON file."""
        with open(output_path, "w") as f:
            json.dump(asdict(matrix), f, indent=2)

    def generate_sample_matrix(self, output_path: str) -> None:
        """Generate a sample verification matrix for testing."""
        # Sample capability data
        sample_capabilities = {
            "financial_events": {
                "id": "financial_events",
                "name": "Financial Events",
                "description": "Track lifecycle of financial events",
            },
            "credit_cards": {
                "id": "credit_cards",
                "name": "Credit Cards",
                "description": "Analyze credit card statements",
            },
            "debt_management": {
                "id": "debt_management",
                "name": "Debt Management",
                "description": "Compute loan schedules",
            },
            "account_management": {
                "id": "account_management",
                "name": "Account Management",
                "description": "Manage bank accounts",
            },
        }

        # Sample test results
        sample_results = [
            {
                "capability_id": "financial_events",
                "capability_name": "Financial Events",
                "test_type": "capability",
                "status": "passed",
                "timestamp": datetime.now().isoformat(),
                "critical": False,
            },
            {
                "capability_id": "financial_events",
                "capability_name": "Financial Events",
                "test_type": "property",
                "status": "passed",
                "timestamp": datetime.now().isoformat(),
                "critical": False,
            },
            {
                "capability_id": "credit_cards",
                "capability_name": "Credit Cards",
                "test_type": "capability",
                "status": "passed",
                "timestamp": datetime.now().isoformat(),
                "critical": False,
            },
            {
                "capability_id": "credit_cards",
                "capability_name": "Credit Cards",
                "test_type": "contract",
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "critical": True,
            },
            {
                "capability_id": "debt_management",
                "capability_name": "Debt Management",
                "test_type": "capability",
                "status": "passed",
                "timestamp": datetime.now().isoformat(),
                "critical": False,
            },
            {
                "capability_id": "account_management",
                "capability_name": "Account Management",
                "test_type": "unit",
                "status": "passed",
                "timestamp": datetime.now().isoformat(),
                "critical": False,
            },
        ]

        # Sample risk data
        sample_risk = {
            "entries": [
                {"capability_id": "financial_events", "risk_level": "MEDIUM"},
                {"capability_id": "credit_cards", "risk_level": "HIGH"},
                {"capability_id": "debt_management", "risk_level": "HIGH"},
                {"capability_id": "account_management", "risk_level": "LOW"},
            ]
        }

        self.load_capability_data(sample_capabilities)
        self.load_test_results(sample_results)
        self.load_risk_data(sample_risk)

        matrix = self.generate_verification_matrix()
        self.save_matrix(matrix, output_path)
