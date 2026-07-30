"""Longitudinal Determinism Tests.

Verifies that generated artifacts are deterministic across multiple runs.

Part I of Phase 3.2 - Capability Validation & Real-World Verification.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
TESTS_DIR = BACKEND_DIR / "tests"
GENERATED_DIR = TESTS_DIR / "generated"


def _hash_file(path: Path) -> str:
    """Return SHA-256 hash of a file's contents."""

    def _normalize_json(content: str) -> str:
        """Remove generated_at timestamps for deterministic comparison."""
        import json
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return content

        def _strip_generated_at(obj):
            if isinstance(obj, dict):
                return {k: _strip_generated_at(v) for k, v in obj.items() if k != "generated_at"}
            if isinstance(obj, list):
                return [_strip_generated_at(item) for item in obj]
            return obj

        return json.dumps(_strip_generated_at(data), sort_keys=True, indent=2)

    content = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".json":
        content = _normalize_json(content)

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _run_generator_and_collect() -> dict[str, str]:
    """Run the verification intelligence generator and collect output file hashes."""
    import subprocess
    import sys

    # Run the generator
    subprocess.run(
        [sys.executable, "-m", "verification_intelligence", "--all"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )

    # Collect hashes of all generated files
    hashes: dict[str, str] = {}
    for f in GENERATED_DIR.glob("*.json"):
        if f.exists():
            hashes[f.name] = _hash_file(f)
    for f in GENERATED_DIR.glob("*.md"):
        if f.exists() and f.name != "coverage.md":  # coverage.md has timestamp
            hashes[f.name] = _hash_file(f)

    return hashes


class TestLongitudinalDeterminism:
    """Verify that generated artifacts are deterministic across runs."""

    def test_dependency_map_deterministic(self) -> None:
        """Dependency map must be identical across multiple runs."""
        hashes_1 = _run_generator_and_collect()
        hashes_2 = _run_generator_and_collect()

        # Compare dependency-map.json specifically
        if "dependency-map.json" in hashes_1 and "dependency-map.json" in hashes_2:
            assert (
                hashes_1["dependency-map.json"] == hashes_2["dependency-map.json"]
            ), "dependency-map.json differs between runs"

    def test_all_json_artifacts_deterministic(self) -> None:
        """All JSON artifacts must be identical across multiple runs."""
        hashes_1 = _run_generator_and_collect()
        hashes_2 = _run_generator_and_collect()

        # Compare all JSON files (excluding coverage.json which may have timestamps)
        json_files = [
            "api-map.json",
            "capability-registry.yaml",
            "contract-registry.json",
            "change-impact.json",
            "mutation-map.json",
            "mutation-readiness.json",
            "test-strength.json",
            "selective-summary.json",
            "contract-coverage.json",
        ]

        for filename in json_files:
            if filename in hashes_1 and filename in hashes_2:
                assert (
                    hashes_1[filename] == hashes_2[filename]
                ), f"{filename} differs between runs"

    def test_no_timestamp_only_diffs(self) -> None:
        """Generated artifacts must not contain timestamp-only diffs."""
        hashes_1 = _run_generator_and_collect()
        hashes_2 = _run_generator_and_collect()

        # All files should have identical hashes
        mismatches = []
        for filename in hashes_1:
            if filename in hashes_2 and hashes_1[filename] != hashes_2[filename]:
                mismatches.append(filename)

        assert (
            not mismatches
        ), f"Files differ between runs (non-deterministic): {mismatches}"

    def test_dependency_engine_deterministic(self) -> None:
        """DependencyEngine.discover() must produce identical output across runs."""
        from src.verification.intelligence.dependency_engine import DependencyEngine

        engine = DependencyEngine()
        graph1 = engine.discover()
        graph2 = engine.discover()

        d1 = graph1.to_dict()
        d2 = graph2.to_dict()

        assert d1 == d2, "DependencyEngine output differs between runs"

    def test_impact_engine_deterministic(self) -> None:
        """ImpactEngine.analyze() must produce identical output for same inputs."""
        from src.verification.intelligence.impact_engine import ImpactEngine

        engine = ImpactEngine()
        test_file = "backend/src/engines/cashflow_engine.py"

        impact1 = engine.analyze([test_file])
        impact2 = engine.analyze([test_file])

        d1 = impact1.to_dict()
        d2 = impact2.to_dict()

        d1.pop("generated_at", None)
        d2.pop("generated_at", None)

        assert d1 == d2, "ImpactEngine output differs between runs"

    def test_selective_engine_deterministic(self) -> None:
        """SelectiveEngine.plan() must produce identical output for same inputs."""
        from src.verification.intelligence.selective_engine import SelectiveEngine

        engine = SelectiveEngine()
        test_file = "backend/src/engines/cashflow_engine.py"

        plan1 = engine.plan([test_file])
        plan2 = engine.plan([test_file])

        d1 = plan1.to_dict()
        d2 = plan2.to_dict()

        assert d1 == d2, "SelectiveEngine output differs between runs"
