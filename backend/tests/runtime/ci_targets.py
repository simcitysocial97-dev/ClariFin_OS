"""CI target derivation for GitHub Actions.

Outputs machine-readable target lists for test execution:
- Property test directories
- Contract test paths
- Capability test directories
- Invariant test paths
- Golden test directories
- Mutation engine targets

Usage:
    python -m runtime.ci_targets --property
    python -m runtime.ci_targets --contract
    python -m runtime.ci_targets --capability
    python -m runtime.ci_targets --invariant
    python -m runtime.ci_targets --golden
    python -m runtime.ci_targets --mutation
    python -m runtime.ci_targets --all
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
TESTS_DIR = BACKEND_DIR / "tests"


def get_property_targets() -> list[str]:
    """Get all property test directory paths."""
    props_dir = TESTS_DIR / "properties"
    targets = []
    if props_dir.exists():
        for subdir in sorted(props_dir.iterdir()):
            if subdir.is_dir() and not subdir.name.startswith("__"):
                targets.append(str(subdir.relative_to(BACKEND_DIR)))
    return targets


def get_contract_targets() -> list[str]:
    """Get all contract test file paths."""
    contract_dir = TESTS_DIR / "contract" / "generated"
    targets = []
    if contract_dir.exists():
        for py_file in sorted(contract_dir.glob("test_*.py")):
            targets.append(str(py_file.relative_to(BACKEND_DIR)))
    return targets


def get_capability_targets() -> list[str]:
    """Get all capability test directory paths."""
    caps_dir = TESTS_DIR / "capability"
    targets = []
    if caps_dir.exists():
        for subdir in sorted(caps_dir.iterdir()):
            if subdir.is_dir() and not subdir.name.startswith("__"):
                targets.append(str(subdir.relative_to(BACKEND_DIR)))
    return targets


def get_invariant_targets() -> list[str]:
    """Get all invariant test file paths."""
    inv_dir = TESTS_DIR / "invariants"
    targets = []
    if inv_dir.exists():
        for py_file in sorted(inv_dir.glob("test_*.py")):
            targets.append(str(py_file.relative_to(BACKEND_DIR)))
    return targets


def get_golden_targets() -> list[str]:
    """Get all golden test directory path."""
    golden_dir = TESTS_DIR / "golden"
    targets = []
    if golden_dir.exists():
        for py_file in sorted(golden_dir.glob("test_*.py")):
            targets.append(str(py_file.relative_to(BACKEND_DIR)))
    return targets


def get_mutation_targets() -> list[str]:
    """Get all engine file paths for mutation testing."""
    engines_dir = BACKEND_DIR / "src" / "engines"
    targets = []
    if engines_dir.exists():
        for py_file in sorted(engines_dir.rglob("*.py")):
            if py_file.name != "__init__.py":
                targets.append(str(py_file.relative_to(BACKEND_DIR)))
    return targets


def get_intelligent_targets(
    changed_files: list[str] | None = None,
) -> dict[str, Any]:
    """Get intelligence-driven CI targets.

    Uses the Verification Intelligence Layer to determine
    which targets must run based on what changed.
    """
    try:
        from verification.intelligence.impact_engine import ImpactEngine
        from verification.intelligence.selective_engine import SelectiveEngine

        impact_engine = ImpactEngine()
        files = changed_files if changed_files else _get_git_changed_files()
        impact = impact_engine.analyze(files)

        selective_engine = SelectiveEngine()
        plan = selective_engine.plan(files, impact.to_dict())

        targets: dict[str, Any] = {
            "strategy": plan.strategy,
            "overall_risk": plan.overall_risk,
            "affected_capabilities": plan.affected_capabilities,
            "must_run_jobs": [j.job_id for j in plan.must_run_jobs],
            "skipped_jobs": [j.job_id for j in plan.skipped_jobs],
            "mutation_targets": [e.id for e in impact.affected_engines],
            "regression_suites": [
                c.id
                for c in impact.affected_capabilities
                if c.risk in ("HIGH", "CRITICAL")
            ],
            "estimated_runtime_seconds": sum(
                j.estimated_runtime_seconds for j in plan.must_run_jobs
            ),
        }

        return targets
    except Exception:
        return {
            "strategy": "full",
            "overall_risk": "UNKNOWN",
            "affected_capabilities": [],
            "must_run_jobs": [],
            "skipped_jobs": [],
            "mutation_targets": [],
            "regression_suites": [],
            "estimated_runtime_seconds": 0,
        }


def _get_git_changed_files() -> list[str]:
    """Get changed files from git diff."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except FileNotFoundError:
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description="CI Target Derivation")
    parser.add_argument(
        "--property", action="store_true", help="Output property test targets"
    )
    parser.add_argument(
        "--contract", action="store_true", help="Output contract test targets"
    )
    parser.add_argument(
        "--capability", action="store_true", help="Output capability test targets"
    )
    parser.add_argument(
        "--invariant", action="store_true", help="Output invariant test targets"
    )
    parser.add_argument(
        "--golden", action="store_true", help="Output golden test targets"
    )
    parser.add_argument(
        "--mutation", action="store_true", help="Output mutation targets"
    )
    parser.add_argument("--all", action="store_true", help="Output all targets")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not any(
        [
            args.property,
            args.contract,
            args.capability,
            args.invariant,
            args.golden,
            args.mutation,
            args.all,
        ]
    ):
        parser.print_help()
        sys.exit(1)

    result: dict[str, list[str]] = {}

    if args.all or args.property:
        result["property"] = get_property_targets()
    if args.all or args.contract:
        result["contract"] = get_contract_targets()
    if args.all or args.capability:
        result["capability"] = get_capability_targets()
    if args.all or args.invariant:
        result["invariant"] = get_invariant_targets()
    if args.all or args.golden:
        result["golden"] = get_golden_targets()
    if args.all or args.mutation:
        result["mutation"] = get_mutation_targets()

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for key, targets in result.items():
            print(f"# {key.upper()} TARGETS")
            for target in targets:
                print(target)


if __name__ == "__main__":
    main()
