"""Contract Evidence Collector — reads Schemathesis JSON report."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .base import EvidenceCollector, EvidenceArtifact


@dataclass(frozen=True, slots=True)
class ContractEvidence:
    endpoints_tested: int = 0
    failures: list[dict] = field(default_factory=list)
    schema_violations: int = 0
    status: str = "not_run"
    timestamp: str = ""


class ContractCollector(EvidenceCollector):
    """Collects contract testing evidence from Schemathesis JSON report."""

    @property
    def artifact_type(self) -> str:
        return "contract"

    @property
    def name(self) -> str:
        return "Contract Collector"

    def collect(self, artifact_path: Path | None = None) -> ContractEvidence:
        if artifact_path is None:
            candidates = [
                self.workspace_root
                / "backend"
                / "tests"
                / "generated"
                / "contract-coverage.json",
                self.workspace_root
                / "backend"
                / "tests"
                / "generated"
                / "schemathesis-report.json",
            ]
        else:
            candidates = [artifact_path]

        for candidate in candidates:
            if candidate.exists():
                return self._parse(candidate)

        return ContractEvidence(
            status="not_run",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _parse(self, path: Path) -> ContractEvidence:
        try:
            data = self._read_json(path)
        except (json.JSONDecodeError, OSError):
            return ContractEvidence(
                status="not_run",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        if data is None:
            return ContractEvidence(
                status="not_run",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        endpoints = data.get("endpoints_tested", 0)
        if endpoints == 0:
            endpoints = len(data.get("endpoints", []))

        failures: list[dict] = []
        for failure in data.get("failures", []):
            failures.append(
                {
                    "endpoint": failure.get("endpoint", ""),
                    "method": failure.get("method", ""),
                    "status_code": failure.get("status_code", 0),
                    "response": failure.get("response", ""),
                    "request": failure.get("request", ""),
                }
            )

        violations = data.get("schema_violations", 0)

        has_failures = len(failures) > 0
        has_violations = violations > 0
        if has_failures:
            status = "fail"
        elif has_violations:
            status = "warning"
        else:
            status = "pass"

        return ContractEvidence(
            endpoints_tested=endpoints,
            failures=failures,
            schema_violations=violations,
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def collect_artifacts(self) -> list[EvidenceArtifact]:
        artifacts: list[EvidenceArtifact] = []
        evidence = self.collect()

        candidates = [
            self.workspace_root
            / "backend"
            / "tests"
            / "generated"
            / "contract-coverage.json",
            self.workspace_root
            / "backend"
            / "tests"
            / "generated"
            / "schemathesis-report.json",
        ]

        for candidate in candidates:
            if candidate.exists():
                artifacts.append(
                    self._artifact(
                        name="Contract Test Results",
                        path=candidate,
                        metadata={
                            "endpoints_tested": evidence.endpoints_tested,
                            "failures": len(evidence.failures),
                            "schema_violations": evidence.schema_violations,
                            "status": evidence.status,
                        },
                    )
                )
                break

        return artifacts
