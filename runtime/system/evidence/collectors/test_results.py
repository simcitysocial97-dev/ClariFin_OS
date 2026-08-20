"""Test Result Evidence Collector — reads JUnit XML from pytest."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from runtime.foundation.verification.totals import (
    TotalsInconsistentError,
    assert_totals_consistent,
)
from .base import EvidenceCollector, EvidenceArtifact


@dataclass(frozen=True, slots=True)
class TestResultEvidence:
    passed: int = 0
    failed: int = 0
    error: int = 0
    skipped: int = 0
    failed_test_names: list[str] = field(default_factory=list)
    error_test_names: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    timestamp: str = ""

    def __post_init__(self) -> None:
        # M9-C37 meta-invariant: totals arithmetic must always hold. error is
        # a sub-count of failures for the purposes of the invariant is NOT what
        # we assert here; the evidence carries error separately, so we assert
        # that the collected counters are individually non-negative. The
        # passed+failed+skipped==total identity is enforced by the collector,
        # which sets total from the actual enumerated testcases.
        if any(v < 0 for v in (self.passed, self.failed, self.error, self.skipped)):
            raise TotalsInconsistentError(
                "test result counters contain negative values"
            )


class TestResultCollector(EvidenceCollector):
    """Collects test result evidence from JUnit XML output."""

    @property
    def artifact_type(self) -> str:
        return "test_results"

    @property
    def name(self) -> str:
        return "Test Results Collector"

    def collect(self, artifact_path: Path | None = None) -> TestResultEvidence:
        if artifact_path is None:
            candidate_paths = [
                self.workspace_root / "backend" / "tests" / "generated" / "junit.xml",
                self.workspace_root
                / "backend"
                / "tests"
                / "generated"
                / "test-results.xml",
                self.workspace_root
                / "backend"
                / "tests"
                / "generated"
                / "pytest-results.xml",
            ]
            artifact_path = None
            for candidate in candidate_paths:
                if candidate.exists():
                    artifact_path = candidate
                    break
            if artifact_path is None:
                return TestResultEvidence(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
        elif not artifact_path.exists():
            return TestResultEvidence(
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        try:
            tree = ET.parse(artifact_path)
            root = tree.getroot()
        except ET.ParseError:
            return TestResultEvidence(
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        passed = 0
        failed = 0
        errors = 0
        skipped = 0
        total = 0
        duration = 0.0
        failed_names: list[str] = []
        error_names: list[str] = []

        for testsuite in root.iter("testsuite"):
            duration += float(testsuite.get("time", "0"))

            # M9-C37: derive totals by enumerating the actual testcase nodes
            # (ground truth) instead of trusting the suite ``tests``/``failures``
            # attributes, so arithmetic can never contradict the evidence.
            # Each testcase is classified into exactly one bucket.
            for testcase in testsuite.iter("testcase"):
                total += 1
                class_name = testcase.get("classname", "")
                test_name = testcase.get("name", "")
                full_name = f"{class_name}#{test_name}" if class_name else test_name
                if testcase.find("failure") is not None:
                    failed += 1
                    failed_names.append(full_name)
                elif testcase.find("error") is not None:
                    errors += 1
                    error_names.append(full_name)
                elif testcase.find("skipped") is not None:
                    skipped += 1
                else:
                    passed += 1

        # M9-C37 meta-invariant — 4-way: each enumerated testcase lands in
        # exactly one bucket, therefore the buckets must sum to the total.
        assert_totals_consistent(
            total,
            passed,
            failed + errors,
            skipped,
            context="test_results junit enumeration",
        )

        return TestResultEvidence(
            passed=passed,
            failed=failed,
            error=errors,
            skipped=skipped,
            failed_test_names=failed_names,
            error_test_names=error_names,
            duration_seconds=duration,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def collect_artifacts(self) -> list[EvidenceArtifact]:
        artifacts: list[EvidenceArtifact] = []
        evidence = self.collect()
        junit_path = (
            self.workspace_root / "backend" / "tests" / "generated" / "junit.xml"
        )
        artifacts.append(
            self._artifact(
                name="Test Results",
                path=junit_path,
                metadata={
                    "passed": evidence.passed,
                    "failed": evidence.failed,
                    "error": evidence.error,
                    "skipped": evidence.skipped,
                    "duration_seconds": evidence.duration_seconds,
                },
            )
        )
        return artifacts
