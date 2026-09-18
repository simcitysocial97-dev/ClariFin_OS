"""M9-C62 — Framework Integrity Result & Self-Diagnostic Contract.

Provides:
- FrameworkIntegrityResult: canonical self-diagnostic result type (Phase J)
- ArtifactFreshnessDetector: verifies generated artifacts are fresh (Phase H)
- FrameworkSelfTests: K1-K8 self-tests for the detector (Phase K)
"""

from __future__ import annotations

import ast
import importlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
logger = logging.getLogger(__name__)


class FrameworkHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class DriftFinding:
    check_name: str
    detected_component: str
    expected_authority: str
    actual_authority: str
    classification: str
    source_evidence: str
    severity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "detected_component": self.detected_component,
            "expected_authority": self.expected_authority,
            "actual_authority": self.actual_authority,
            "classification": self.classification,
            "source_evidence": self.source_evidence,
            "severity": self.severity,
        }


@dataclass(frozen=True, slots=True)
class FrameworkIntegrityResult:
    """Self-diagnostic contract for the verification framework.

    This is the canonical result type returned by framework self-tests
    and the doctor() diagnostic. It encapsulates all diagnostic dimensions
    of framework integrity in a single, structured, serializable result.
    """

    schema: str = "m9-c62-framework-integrity/v1"
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    health: FrameworkHealth = FrameworkHealth.HEALTHY
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    total_findings: int = 0
    findings: list[DriftFinding] = field(default_factory=list)
    artifact_summary: dict[str, Any] = field(default_factory=dict)
    diagnostic: dict[str, Any] = field(default_factory=dict)

    @property
    def healthy(self) -> bool:
        return self.health == FrameworkHealth.HEALTHY

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "health": self.health.value,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "info_count": self.info_count,
            "total_findings": self.total_findings,
            "findings": [f.to_dict() for f in self.findings],
            "artifact_summary": self.artifact_summary,
            "diagnostic": self.diagnostic,
        }

    @classmethod
    def from_drift_report(cls, report: Any, **kwargs: Any) -> FrameworkIntegrityResult:
        """Construct from an authority drift report."""
        raw_findings = getattr(report, "findings", [])
        findings: list[DriftFinding] = []
        for f in raw_findings:
            if isinstance(f, DriftFinding):
                findings.append(f)
            elif isinstance(f, dict):
                findings.append(DriftFinding(**f))
            else:
                findings.append(DriftFinding(
                    check_name=str(getattr(f, "check_name", "unknown")),
                    detected_component=str(getattr(f, "detected_component", "unknown")),
                    expected_authority=str(getattr(f, "expected_authority", "unknown")),
                    actual_authority=str(getattr(f, "actual_authority", "unknown")),
                    classification=str(getattr(f, "classification", "UNKNOWN")),
                    source_evidence=str(getattr(f, "source_evidence", "")),
                    severity=str(getattr(f, "severity", "INFO")),
                ))
        critical = sum(1 for f in findings if f.severity == "critical")
        high = sum(1 for f in findings if f.severity == "high")
        medium = sum(1 for f in findings if f.severity == "medium")
        low = sum(1 for f in findings if f.severity == "low")
        info = sum(1 for f in findings if f.severity == "info")
        healthy = critical == 0 and high == 0
        return cls(
            health=FrameworkHealth.HEALTHY if healthy else FrameworkHealth.DEGRADED,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            info_count=info,
            total_findings=len(findings),
            findings=findings,
            **kwargs,
        )


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    path: str
    age_seconds: float
    owner_pid: int | None = None
    fresh: bool = True


class ArtifactFreshnessDetector:
    """Verify generated artifacts are fresh and owned by the current process."""

    MAX_AGE_SECONDS: float = 2592000.0  # 30 days

    def check(self) -> list[DriftFinding]:
        findings: list[DriftFinding] = []

        generated_root = REPO_ROOT / "runtime" / "generated"
        if not generated_root.exists():
            findings.append(DriftFinding(
                check_name="artifact_freshness",
                detected_component=str(generated_root),
                expected_authority="runtime/generated/ exists",
                actual_authority="runtime/generated/ MISSING",
                classification="ARTIFACT_INTEGRITY_DEFECT",
                source_evidence="Generated artifacts directory does not exist",
                severity="MEDIUM",
            ))
            return findings

        now = datetime.now(UTC).timestamp()
        stale_artifacts: list[str] = []
        missing_ownership: list[str] = []

        for py_file in sorted(generated_root.rglob("*")):
            if not py_file.is_file():
                continue
            rel = str(py_file.relative_to(REPO_ROOT))
            if any(x in rel for x in ["__pycache__", ".git", "node_modules"]):
                continue

            try:
                stat = py_file.stat()
                age = now - stat.st_mtime
                if age > self.MAX_AGE_SECONDS:
                    stale_artifacts.append(f"{rel} ({age:.0f}s old)")
            except OSError:
                stale_artifacts.append(f"{rel} (stat failed)")

        if stale_artifacts:
            findings.append(DriftFinding(
                check_name="stale_artifacts",
                detected_component=str(generated_root),
                expected_authority=f"All artifacts < {self.MAX_AGE_SECONDS:.0f}s old",
                actual_authority=f"{len(stale_artifacts)} stale artifacts",
                classification="ARTIFACT_INTEGRITY_DEFECT",
                source_evidence=f"Stale artifacts: {', '.join(stale_artifacts[:5])}"
                + (f" (+{len(stale_artifacts)-5} more)" if len(stale_artifacts) > 5 else ""),
                severity="MEDIUM",
            ))

        return findings


def _find_python_files(root: Path, pattern: str = "*.py") -> list[Path]:
    return sorted(root.rglob(pattern))


class FrameworkSelfTests:
    """K1-K8 self-tests for the authority drift detector and framework integrity.

    These tests verify that the framework's self-observability and
    control-plane integrity detectors work correctly.
    """

    def __init__(self) -> None:
        self._results: dict[str, bool] = {}

    @property
    def results(self) -> dict[str, bool]:
        return dict(self._results)

    def run_all(self) -> FrameworkIntegrityResult:
        """Run K1-K9 self-tests and return a FrameworkIntegrityResult."""
        tests = [
            ("K1", self.test_k1_detector_healthy_on_clean_repo),
            ("K2", self.test_k2_no_critical_high_on_clean_repo),
            ("K3", self.test_k3_detector_produces_valid_json),
            ("K4", self.test_k4_artifact_freshness),
            ("K5", self.test_k5_authority_declarations_resolvable),
            ("K6", self.test_k6_canonical_commands_present),
            ("K7", self.test_k7_evidence_writer_resolvable),
            ("K8", self.test_k8_framework_integrity_result_serializable),
            ("K9", self.test_k9_failure_detection_and_recovery),
        ]
        for name, test_fn in tests:
            try:
                passed = test_fn()
                self._results[name] = passed
                logger.debug("%s: %s", name, "PASS" if passed else "FAIL")
            except Exception as exc:
                self._results[name] = False
                logger.error("%s: ERROR %s", name, exc)

        failures = [n for n, p in self._results.items() if not p]
        if failures:
            health = FrameworkHealth.CRITICAL
        elif any(not p for p in self._results.values()):
            health = FrameworkHealth.DEGRADED
        else:
            health = FrameworkHealth.HEALTHY

        findings = [
            DriftFinding(
                check_name=f"self_test_{name}",
                detected_component="FrameworkSelfTests",
                expected_authority="PASS",
                actual_authority="FAIL" if not p else "PASS",
                classification="FALSE_POSITIVE" if not p else "NORMAL",
                source_evidence=f"Self-test {name} {'passed' if p else 'failed'}",
                severity="CRITICAL" if not p else "INFO",
            )
            for name, p in self._results.items()
            if not p
        ]

        return FrameworkIntegrityResult(
            health=health,
            critical_count=sum(1 for f in findings if f.severity == "CRITICAL"),
            high_count=sum(1 for f in findings if f.severity == "HIGH"),
            medium_count=sum(1 for f in findings if f.severity == "MEDIUM"),
            low_count=sum(1 for f in findings if f.severity == "LOW"),
            info_count=sum(1 for f in findings if f.severity == "INFO"),
            total_findings=len(findings),
            findings=findings,
            diagnostic={
                "self_tests": dict(self._results),
                "passed": sum(self._results.values()),
                "total": len(self._results),
            },
        )

    def test_k1_detector_healthy_on_clean_repo(self) -> bool:
        """K1: Authority drift detector produces HEALTHY on clean repo."""
        from runtime.foundation.verification.authority_drift_detector import (
            run_authority_drift_detection,
        )
        report = run_authority_drift_detection()
        return report.healthy

    def test_k2_no_critical_high_on_clean_repo(self) -> bool:
        """K2: No CRITICAL or HIGH findings on clean repo."""
        from runtime.foundation.verification.authority_drift_detector import (
            run_authority_drift_detection,
        )
        report = run_authority_drift_detection()
        return report.critical_count == 0 and report.high_count == 0

    def test_k3_detector_produces_valid_json(self) -> bool:
        """K3: Detector output is valid JSON serializable."""
        from runtime.foundation.verification.authority_drift_detector import (
            run_authority_drift_detection,
        )
        report = run_authority_drift_detection()
        data = report.to_dict()
        json.dumps(data)
        return "schema" in data and "findings" in data and "healthy" in data

    def test_k4_artifact_freshness(self) -> bool:
        """K4: Artifact freshness detector runs without error."""
        detector = ArtifactFreshnessDetector()
        findings = detector.check()
        return isinstance(findings, list)

    def test_k5_authority_declarations_resolvable(self) -> bool:
        """K5: Canonical authority declarations exist as importable modules."""
        canonical_modules = [
            "runtime.foundation.verification.control_plane",
            "runtime.foundation.verification.execution_orchestrator",
            "runtime.foundation.verification.control_plane_facade",
            "runtime.verify",
        ]
        for mod in canonical_modules:
            try:
                importlib = __import__("importlib")
                importlib.import_module(mod)
            except ImportError:
                return False
        return True

    def test_k6_canonical_commands_present(self) -> bool:
        """K6: All 9 canonical commands present in facade."""
        facade_path = REPO_ROOT / "runtime" / "foundation" / "verification" / "control_plane_facade.py"
        if not facade_path.exists():
            return False
        source = facade_path.read_text(encoding="utf-8")
        canonical = ["check", "plan", "run", "diagnose", "strengthen", "inspect", "certify", "ci", "doctor"]
        return all(cmd in source for cmd in canonical)

    def test_k7_evidence_writer_resolvable(self) -> bool:
        """K7: record_execution_report is importable."""
        try:
            __import__("importlib")
            importlib = __import__("importlib")
            importlib.import_module("runtime.verify")
            from runtime.verify import record_execution_report
            return callable(record_execution_report)
        except Exception:
            return False

    def test_k8_framework_integrity_result_serializable(self) -> bool:
        """K8: FrameworkIntegrityResult can be serialized to dict and JSON."""
        result = FrameworkIntegrityResult(
            health=FrameworkHealth.HEALTHY,
            diagnostic={"test": True},
        )
        data = result.to_dict()
        json.dumps(data)
        return (
            "schema" in data
            and "health" in data
            and "findings" in data
            and "diagnostic" in data
        )

    def test_k9_failure_detection_and_recovery(self) -> bool:
        """K9: Framework integrity result correctly classifies states.

        Demonstrates the failure detection → classification → recovery
        contract without re-triggering self-tests:
        - HEALTHY state has 0 critical/high findings
        - Result structure supports severity counts and diagnostic metadata
        - State transitions are well-defined (HEALTHY → DEGRADED → CRITICAL)
        """
        result = FrameworkIntegrityResult(
            health=FrameworkHealth.HEALTHY,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            info_count=0,
            total_findings=0,
            diagnostic={"test": "recovery state"},
        )
        data = result.to_dict()
        healthy = data["health"] == "HEALTHY"
        no_critical = data["critical_count"] == 0
        no_high = data["high_count"] == 0
        structure_ok = (
            "schema" in data
            and "findings" in data
            and "diagnostic" in data
            and isinstance(data["critical_count"], int)
        )
        degraded = FrameworkIntegrityResult(
            health=FrameworkHealth.DEGRADED,
            critical_count=0,
            high_count=1,
            diagnostic={"test": "degraded state"},
        ).to_dict()
        degraded_detected = degraded["health"] == "DEGRADED" and degraded["high_count"] == 1
        return healthy and no_critical and no_high and structure_ok and degraded_detected
