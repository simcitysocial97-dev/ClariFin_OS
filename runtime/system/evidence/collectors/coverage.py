"""Coverage Evidence Collector — reads pytest-cov JSON output."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .base import EvidenceCollector, EvidenceArtifact


@dataclass(frozen=True, slots=True)
class CoverageEvidence:
    overall_pct: float
    per_engine: dict[str, float] = field(default_factory=dict)
    uncovered_lines: dict[str, list[int]] = field(default_factory=dict)
    branch_coverage: float = 0.0
    timestamp: str = ""


class CoverageCollector(EvidenceCollector):
    """Collects coverage evidence from pytest-cov JSON output."""

    @property
    def artifact_type(self) -> str:
        return "coverage"

    @property
    def name(self) -> str:
        return "Coverage Collector"

    def collect(
        self, artifact_path: Path | None = None
    ) -> CoverageEvidence:
        if artifact_path is None:
            artifact_path = (
                self.workspace_root
                / "backend"
                / "tests"
                / "generated"
                / "coverage.json"
            )

        if not artifact_path.exists():
            return CoverageEvidence(
                overall_pct=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        try:
            data = self._read_json(artifact_path)
        except (json.JSONDecodeError, OSError):
            return CoverageEvidence(
                overall_pct=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        if data is None:
            return CoverageEvidence(
                overall_pct=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        totals = data.get("totals", {})
        overall_pct = totals.get("percent_covered", 0.0)

        covered_branches = totals.get("covered_branches", 0)
        num_branches = totals.get("num_branches", 0)
        branch_pct = (
            round(covered_branches / num_branches * 100, 2)
            if num_branches > 0
            else 0.0
        )

        files_data = data.get("files", {})
        engine_coverage: dict[str, float] = {}
        uncovered_lines: dict[str, list[int]] = {}

        for file_path, file_data in files_data.items():
            if "/engines/" not in file_path:
                continue

            parts = file_path.split("/")
            engine_idx = None
            for i, part in enumerate(parts):
                if part.endswith("_engine") and i < len(parts) - 1:
                    engine_idx = i
                    break

            if engine_idx is None:
                continue

            engine_name = parts[engine_idx].replace("_engine", "")
            summary = file_data.get("summary", {})
            pct = summary.get("percent_covered", 0.0)
            engine_coverage[engine_name] = pct

            missing = file_data.get("missing_lines", [])
            if missing:
                uncovered_lines[engine_name] = sorted(missing)

        return CoverageEvidence(
            overall_pct=overall_pct,
            per_engine=engine_coverage,
            uncovered_lines=uncovered_lines,
            branch_coverage=branch_pct,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def collect_artifacts(self) -> list[EvidenceArtifact]:
        artifacts: list[EvidenceArtifact] = []
        evidence = self.collect()
        artifacts.append(
            self._artifact(
                name="Backend Coverage",
                path=self.workspace_root
                / "backend"
                / "tests"
                / "generated"
                / "coverage.json",
                metadata={
                    "percentage": evidence.overall_pct,
                    "per_engine": evidence.per_engine,
                    "uncovered_lines": evidence.uncovered_lines,
                    "branch_coverage": evidence.branch_coverage,
                },
            )
        )
        return artifacts