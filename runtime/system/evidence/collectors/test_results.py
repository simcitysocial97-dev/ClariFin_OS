"""Test Result Evidence Collector — reads JUnit XML from pytest."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

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


class TestResultCollector(EvidenceCollector):
    """Collects test result evidence from JUnit XML output."""

    @property
    def artifact_type(self) -> str:
        return "test_results"

    @property
    def name(self) -> str:
        return "Test Results Collector"

    def collect(
        self, artifact_path: Path | None = None
    ) -> TestResultEvidence:
        if artifact_path is None:
            candidate_paths = [
                self.workspace_root / "backend" / "tests" / "generated" / "junit.xml",
                self.workspace_root / "backend" / "tests" / "generated" / "test-results.xml",
                self.workspace_root / "backend" / "tests" / "generated" / "pytest-results.xml",
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
        duration = 0.0
        failed_names: list[str] = []
        error_names: list[str] = []

        for testsuite in root.iter("testsuite"):
            total_tests = int(testsuite.get("tests", "0"))
            failures = int(testsuite.get("failures", "0"))
            test_errors = int(testsuite.get("errors", "0"))
            skipped_tests = int(testsuite.get("skipped", "0"))
            duration += float(testsuite.get("time", "0"))

            passed += total_tests - failures - test_errors - skipped_tests
            failed += failures
            errors += test_errors
            skipped += skipped_tests

            for testcase in testsuite.iter("testcase"):
                class_name = testcase.get("classname", "")
                test_name = testcase.get("name", "")
                full_name = (
                    f"{class_name}#{test_name}" if class_name else test_name
                )
                if testcase.find("failure") is not None:
                    failed_names.append(full_name)
                elif testcase.find("error") is not None:
                    error_names.append(full_name)

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
            self.workspace_root
            / "backend"
            / "tests"
            / "generated"
            / "junit.xml"
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