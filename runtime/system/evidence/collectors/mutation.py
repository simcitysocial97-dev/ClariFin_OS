"""Mutation Testing Evidence Collector."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

from .base import EvidenceCollector, EvidenceArtifact


class MutationCollector(EvidenceCollector):
    """Collects mutation testing evidence from mutmut results."""

    @property
    def artifact_type(self) -> str:
        return "mutation"

    @property
    def name(self) -> str:
        return "Mutation Testing Results"

    def collect(self) -> List[EvidenceArtifact]:
        artifacts = []

        mutation_dir = self.workspace_root / "backend" / "tests" / "generated" / "mutation"
        if not mutation_dir.exists():
            return artifacts

        # Main mutation report
        mutation_report = mutation_dir / "mutation-report.md"
        if mutation_report.exists():
            content = self._read_text(mutation_report)
            artifacts.append(
                self._artifact(
                    name="Mutation Report",
                    path=mutation_report,
                    metadata={
                        "size_bytes": mutation_report.stat().st_size,
                        "has_summary": "Surviving" in content or "Killed" in content,
                    },
                )
            )

        # Mutation summary JSON
        mutation_summary = mutation_dir / "mutation-summary.json"
        if mutation_summary.exists():
            data = self._read_json(mutation_summary)
            if data:
                artifacts.append(
                    self._artifact(
                        name="Mutation Summary",
                        path=mutation_summary,
                        metadata={
                            "total_mutants": data.get("total", 0),
                            "killed": data.get("killed", 0),
                            "survived": data.get("survived", 0),
                            "timeout": data.get("timeout", 0),
                            "score": data.get("score", 0.0),
                        },
                    )
                )

        # Individual engine results
        for result_file in mutation_dir.glob("*-results.txt"):
            data = self._read_text(result_file)
            artifacts.append(
                self._artifact(
                    name=f"Mutation Results: {result_file.stem}",
                    path=result_file,
                    metadata={"engine": result_file.stem.replace("-results", "")},
                )
            )

        for survivor_file in mutation_dir.glob("*-survivors.txt"):
            data = self._read_text(survivor_file)
            artifacts.append(
                self._artifact(
                    name=f"Mutation Survivors: {survivor_file.stem}",
                    path=survivor_file,
                    metadata={"engine": survivor_file.stem.replace("-survivors", "")},
                )
            )

        return artifacts