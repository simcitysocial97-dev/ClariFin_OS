"""Mutation Evidence Collector — reads mutmut results and survivors."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base import EvidenceCollector, EvidenceArtifact


@dataclass(frozen=True, slots=True)
class MutationEvidence:
    score_pct: float
    killed: int
    survived: int
    per_engine: dict[str, dict[str, Any]] = field(default_factory=dict)
    timestamp: str = ""


class MutationCollector(EvidenceCollector):
    """Collects mutation testing evidence from mutmut output."""

    @property
    def artifact_type(self) -> str:
        return "mutation"

    @property
    def name(self) -> str:
        return "Mutation Collector"

    def collect(self, artifact_path: Path | None = None) -> MutationEvidence:
        if artifact_path is None:
            mutation_dir = (
                self.workspace_root / "backend" / "tests" / "generated" / "mutation"
            )
        else:
            mutation_dir = (
                artifact_path.parent if artifact_path.is_file() else artifact_path
            )

        if not mutation_dir.exists():
            return MutationEvidence(
                score_pct=0.0,
                killed=0,
                survived=0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        per_engine: dict[str, dict[str, Any]] = {}
        total_killed = 0
        total_survived = 0

        summary_path = mutation_dir / "mutation-summary.json"
        summary_used = False
        if summary_path.exists():
            try:
                data = self._read_json(summary_path)
                if data:
                    total_killed = data.get("killed", 0)
                    total_survived = data.get("survived", 0)
                    summary_used = True
            except (json.JSONDecodeError, OSError):
                pass

        # Priority: summary.json > results.txt
        # Never combine both sources for the same engine's totals
        for results_file in sorted(mutation_dir.glob("*-results.txt")):
            engine_name = results_file.stem.replace("-results", "")
            result_text = self._read_text(results_file)
            killed = 0
            survived = 0
            surviving_diffs: list[str] = []

            killed_match = re.search(r"Killed:\s*(\d+)", result_text)
            if killed_match:
                killed = int(killed_match.group(1))

            survived_match = re.search(r"Survived:\s*(\d+)", result_text)
            if survived_match:
                survived = int(survived_match.group(1))

            if not summary_used:
                total_killed += killed
                total_survived += survived

            survivors_file = mutation_dir / f"{engine_name}-survivors.txt"
            if survivors_file.exists():
                surviving_diffs = self._parse_survivors(survivors_file)

            engine_total = killed + survived
            per_engine[engine_name] = {
                "killed": killed,
                "survived": survived,
                "score_pct": (
                    round((killed / engine_total) * 100, 1) if engine_total > 0 else 0.0
                ),
                "surviving_diffs": surviving_diffs,
            }

        score_pct = 0.0
        total = total_killed + total_survived
        if total > 0:
            score_pct = round((total_killed / total) * 100, 1)

        return MutationEvidence(
            score_pct=score_pct,
            killed=total_killed,
            survived=total_survived,
            per_engine=per_engine,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _parse_survivors(self, survivors_path: Path) -> list[str]:
        diffs: list[str] = []
        try:
            content = survivors_path.read_text()
        except OSError:
            return diffs

        blocks = re.split(r"\n---", content)
        for block in blocks:
            block = block.strip()
            if block and (block.startswith("+") or block.startswith("-")):
                diffs.append(block)
            elif block:
                diffs.append(f"---{block}")

        if not diffs:
            lines = content.splitlines()
            for line in lines:
                if line.strip():
                    diffs.append(line.strip())

        return diffs[:50]

    def collect_artifacts(self) -> list[EvidenceArtifact]:
        artifacts: list[EvidenceArtifact] = []
        evidence = self.collect()

        artifacts.append(
            self._artifact(
                name="Mutation Summary",
                path=self.workspace_root
                / "backend"
                / "tests"
                / "generated"
                / "mutation"
                / "mutation-summary.json",
                metadata={
                    "score": evidence.score_pct,
                    "killed": evidence.killed,
                    "survived": evidence.survived,
                },
            )
        )

        for engine_name, engine_data in evidence.per_engine.items():
            killed = (
                engine_data.get("killed", 0) if isinstance(engine_data, dict) else 0
            )
            survived = (
                engine_data.get("survived", 0) if isinstance(engine_data, dict) else 0
            )
            total = killed + survived
            score = round((killed / total) * 100, 1) if total > 0 else 0.0
            artifacts.append(
                self._artifact(
                    name=f"Mutation — {engine_name}",
                    path=self.workspace_root
                    / "backend"
                    / "tests"
                    / "generated"
                    / "mutation"
                    / f"{engine_name}-results.txt",
                    metadata={
                        "score": score,
                        "killed": killed,
                        "survived": survived,
                        "surviving_diffs": (
                            engine_data.get("surviving_diffs", [])
                            if isinstance(engine_data, dict)
                            else []
                        ),
                    },
                )
            )

        return artifacts
