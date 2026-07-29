#!/usr/bin/env python3
"""Mutation Verification Tool.

Programmatically modifies one file from each capability to verify that
the change intelligence layer correctly identifies affected capabilities,
tests, and CI jobs.

Part B of Phase 3.2 — Capability Validation & Real-World Verification.

Usage:
    python backend/tools/mutation_verification.py --all
    python backend/tools/mutation_verification.py --capability debt_management
    python backend/tools/mutation_verification.py --report
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"


@dataclass
class MutationResult:
    """Result of a single mutation verification."""

    capability: str
    mutated_file: str
    affected_capabilities: list[str] = field(default_factory=list)
    affected_tests: list[str] = field(default_factory=list)
    skipped_tests: list[str] = field(default_factory=list)
    ci_jobs_must_run: list[str] = field(default_factory=list)
    ci_jobs_skipped: list[str] = field(default_factory=list)
    dependency_graph_consistent: bool = True
    false_positives: int = 0
    false_negatives: int = 0
    passed: bool = False
    error: str = ""


def _load_registry() -> dict[str, Any]:
    """Load the capability registry."""
    import yaml

    registry_path = GENERATED_DIR / "capability-registry.yaml"
    if not registry_path.exists():
        return {"capabilities": []}
    with open(registry_path) as f:
        return yaml.safe_load(f) or {"capabilities": []}


def _get_mutation_target(cap: dict[str, Any]) -> str | None:
    """Select one representative engine file to mutate for a capability."""
    engines = cap.get("engines", [])
    if not engines:
        return None
    # Pick the first engine file
    return engines[0]


def _apply_mutation(file_path: Path) -> str:
    """Apply a temporary mutation to a file and return the original content.

    The mutation changes a simple return value or constant to simulate a bug.
    """
    original_content = file_path.read_text()

    # Try to find a simple mutation point
    lines = original_content.split("\n")
    mutated_lines = list(lines)

    # Find a line with a return statement or a simple assignment
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Mutate a return statement with a numeric literal
        if stripped.startswith("return ") and any(
            c.isdigit() for c in stripped
        ):
            # Replace the return value with a different number
            mutated_lines[i] = line.replace(
                stripped, stripped.replace("return ", "return 0  # MUTATED")
            )
            break
        # Mutate a simple assignment with a numeric literal
        if "=" in stripped and any(c.isdigit() for c in stripped):
            if not stripped.startswith("#") and not stripped.startswith("def"):
                mutated_lines[i] = line + "  # MUTATED"
                break

    mutated_content = "\n".join(mutated_lines)
    file_path.write_text(mutated_content)
    return original_content


def _restore_file(file_path: Path, original_content: str) -> None:
    """Restore a file to its original content."""
    file_path.write_text(original_content)


def _analyze_impact(changed_file: str) -> dict[str, Any]:
    """Analyze the impact of a changed file using the ImpactEngine."""
    from src.verification.intelligence.impact_engine import ImpactEngine

    engine = ImpactEngine()
    impact = engine.analyze([changed_file])
    return impact.to_dict()


def _generate_ci_plan(changed_file: str) -> dict[str, Any]:
    """Generate a CI execution plan for a changed file."""
    from src.verification.intelligence.selective_engine import SelectiveEngine

    engine = SelectiveEngine()
    plan = engine.plan([changed_file])
    return plan.to_dict()


def _get_dependency_graph() -> dict[str, Any]:
    """Get the current dependency graph."""
    from runtime.discovery import discover_dependencies

    return discover_dependencies()


def _get_all_tests() -> list[str]:
    """Get all test file paths in the project."""
    tests_dir = BACKEND_DIR / "tests"
    test_files: list[str] = []
    for py_file in tests_dir.rglob("test_*.py"):
        rel = py_file.relative_to(BACKEND_DIR)
        test_files.append(str(rel))
    return test_files


def _get_required_tests_for_capability(cap_id: str, dep_map: dict[str, Any]) -> set[str]:
    """Get all test files required for a capability from the dependency graph."""
    edges = dep_map.get("edges", [])
    required: set[str] = set()
    for edge in edges:
        if edge.get("source") == cap_id:
            target = edge.get("target", "")
            target_type = edge.get("target_type", "")
            if target_type in ("property_test", "invariant_test", "capability_test"):
                required.add(target)
    return required


def _get_all_required_tests_for_capabilities(
    cap_ids: list[str], dep_map: dict[str, Any]
) -> set[str]:
    """Get all test files required for a set of capabilities."""
    required: set[str] = set()
    for cap_id in cap_ids:
        required.update(_get_required_tests_for_capability(cap_id, dep_map))
    return required


def verify_mutation(cap: dict[str, Any]) -> MutationResult:
    """Verify a single capability mutation.

    Mutates one engine file, analyzes impact, and checks correctness.
    """
    result = MutationResult(
        capability=cap.get("id", ""),
        mutated_file="",
    )

    target = _get_mutation_target(cap)
    if not target:
        result.error = "No engine file to mutate"
        result.passed = False
        return result

    file_path = BACKEND_DIR / target
    if not file_path.exists():
        result.error = f"File not found: {target}"
        result.passed = False
        return result

    result.mutated_file = target

    # Apply mutation
    original_content = _apply_mutation(file_path)

    try:
        # Analyze impact
        impact = _analyze_impact(target)
        result.affected_capabilities = [
            c["id"] for c in impact.get("affected_capabilities", [])
        ]

        # Generate CI plan
        ci_plan = _generate_ci_plan(target)
        result.ci_jobs_must_run = ci_plan.get("must_run_jobs", [])
        result.ci_jobs_skipped = ci_plan.get("skipped_jobs", [])

        # Get dependency graph
        dep_map = _get_dependency_graph()

        # Check dependency graph consistency
        all_cap_ids = set(dep_map.get("capabilities", {}).keys())
        for cap_id in result.affected_capabilities:
            if cap_id not in all_cap_ids:
                result.dependency_graph_consistent = False
                result.error = f"Affected capability {cap_id} not in dependency graph"

        # Get required tests
        required_tests = _get_all_required_tests_for_capabilities(
            result.affected_capabilities, dep_map
        )

        # Get scheduled tests from CI plan
        scheduled_tests: set[str] = set()
        for job in ci_plan.get("jobs", []):
            if job.get("must_run"):
                for target_path in job.get("targets", []):
                    if "tests/" in target_path:
                        scheduled_tests.add(target_path)

        # False positives: tests scheduled but not required
        false_positives = scheduled_tests - required_tests
        result.false_positives = len(false_positives)

        # False negatives: required tests not scheduled
        false_negatives = required_tests - scheduled_tests
        result.false_negatives = len(false_negatives)

        result.affected_tests = sorted(required_tests)
        result.skipped_tests = sorted(scheduled_tests - required_tests)

        # Determine pass/fail
        result.passed = (
            result.false_negatives == 0
            and result.dependency_graph_consistent
            and len(result.affected_capabilities) > 0
        )

    finally:
        # Always restore the file
        _restore_file(file_path, original_content)

    return result


def verify_all_mutations() -> list[MutationResult]:
    """Verify mutations for all capabilities."""
    registry = _load_registry()
    results: list[MutationResult] = []

    for cap in registry.get("capabilities", []):
        result = verify_mutation(cap)
        results.append(result)
        print(
            f"  {result.capability}: {'PASS' if result.passed else 'FAIL'} "
            f"(affected: {len(result.affected_capabilities)}, "
            f"false_pos: {result.false_positives}, "
            f"false_neg: {result.false_negatives})"
        )

    return results


def generate_report(results: list[MutationResult]) -> str:
    """Generate a mutation verification report."""
    lines = [
        "# Mutation Verification Report",
        "",
        "Part B of Phase 3.2 — Capability Validation & Real-World Verification",
        "",
        "## Summary",
        "",
        f"- Total capabilities: {len(results)}",
        f"- Passed: {sum(1 for r in results if r.passed)}",
        f"- Failed: {sum(1 for r in results if not r.passed)}",
        f"- Total false positives: {sum(r.false_positives for r in results)}",
        f"- Total false negatives: {sum(r.false_negatives for r in results)}",
        "",
        "## Detailed Results",
        "",
        "| Capability | Mutated File | Affected Caps | False Positives | False Negatives | Result |",
        "|------------|-------------|---------------|-----------------|-----------------|--------|",
    ]

    for r in results:
        lines.append(
            f"| {r.capability} | `{r.mutated_file}` | {len(r.affected_capabilities)} | "
            f"{r.false_positives} | {r.false_negatives} | {'PASS' if r.passed else 'FAIL'} |"
        )

    lines.extend(
        [
            "",
            "## Per-Capability Details",
            "",
        ]
    )

    for r in results:
        lines.extend(
            [
                f"### {r.capability}",
                "",
                f"**Mutated file:** `{r.mutated_file}`",
                "",
                f"**Affected capabilities:** {', '.join(r.affected_capabilities) if r.affected_capabilities else 'None'}",
                "",
                f"**CI jobs (must run):** {', '.join(r.ci_jobs_must_run) if r.ci_jobs_must_run else 'None'}",
                "",
                f"**CI jobs (skipped):** {', '.join(r.ci_jobs_skipped) if r.ci_jobs_skipped else 'None'}",
                "",
                f"**False positives:** {r.false_positives}",
                "",
                f"**False negatives:** {r.false_negatives}",
                "",
                f"**Result:** {'✓ PASS' if r.passed else '✗ FAIL'}",
                "",
            ]
        )

        if r.error:
            lines.append(f"**Error:** {r.error}")
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mutation Verification Tool")
    parser.add_argument("--all", action="store_true", help="Verify all capabilities")
    parser.add_argument(
        "--capability", type=str, help="Verify a specific capability"
    )
    parser.add_argument("--report", action="store_true", help="Generate report")
    args = parser.parse_args()

    if args.capability:
        registry = _load_registry()
        cap = next(
            (c for c in registry.get("capabilities", []) if c.get("id") == args.capability),
            None,
        )
        if not cap:
            print(f"Capability not found: {args.capability}")
            sys.exit(1)
        results = [verify_mutation(cap)]
    else:
        print("Verifying all capability mutations...")
        results = verify_all_mutations()

    report = generate_report(results)

    if args.report:
        output_path = PROJECT_ROOT / "MUTATION_VERIFICATION_REPORT.md"
        output_path.write_text(report)
        print(f"\nReport written to: {output_path}")

    print(f"\n{report}")

    # Exit with error if any mutation failed
    if any(not r.passed for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
