"""Property Test Evidence Collector."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

from .base import EvidenceCollector, EvidenceArtifact


class PropertyTestCollector(EvidenceCollector):
    """Collects property-based testing evidence from hypothesis/golden tests."""

    @property
    def artifact_type(self) -> str:
        return "property_test"

    @property
    def name(self) -> str:
        return "Property Test Results"

    def collect(self) -> List[EvidenceArtifact]:
        artifacts = []

        # Property test results
        prop_dir = self.workspace_root / "backend" / "tests" / "generated"
        if not prop_dir.exists():
            return artifacts

        # Property test results JSON
        for prop_file in prop_dir.glob("*property*.json"):
            data = self._read_json(prop_file)
            if data:
                artifacts.append(
                    self._artifact(
                        name=f"Property Test: {prop_file.stem}",
                        path=prop_file,
                        metadata={
                            "tests_run": data.get("tests_run", 0),
                            "failures": data.get("failures", 0),
                            "errors": data.get("errors", 0),
                        },
                    )
                )

        # Golden regression results
        golden_dir = self.workspace_root / "backend" / "tests" / "golden" / "regressions"
        if golden_dir.exists():
            for reg_file in golden_dir.glob("*.json"):
                data = self._read_json(reg_file)
                if data:
                    artifacts.append(
                        self._artifact(
                            name=f"Golden Regression: {reg_file.stem}",
                            path=reg_file,
                            metadata={
                                "passed": data.get("passed", False),
                                "diff": data.get("diff", ""),
                            },
                        )
                    )

        return artifacts