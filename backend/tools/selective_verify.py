#!/usr/bin/env python3
"""Selective Verification Framework (SVF).

Executes ONLY the tests impacted by current changes while preserving the full verification pipeline.
Uses change-report.json as primary input, regenerating if stale.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Project root from this file's location (backend/tools → backend → project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"


@dataclass
class SelectivePlan:
    """Plan for selective verification."""
    changed_files: list[str] = field(default_factory=list)
    architecture_tests: list[str] = field(default_factory=lambda: ["tests/architecture"])
    capability_tests: set[str] = field(default_factory=set)
    property_tests: set[str] = field(default_factory=set)
    golden_tests: set[str] = field(default_factory=set)
    invariant_tests: set[str] = field(default_factory=set)
    meta_tests: list[str] = field(default_factory=lambda: ["tests/meta"])

    @property
    def total_test_suites(self) -> int:
        """Count of unique test suites to run."""
        return (
            len(self.capability_tests) +
            len(self.property_tests) +
            len(self.golden_tests) +
            len(self.invariant_tests) +
            (1 if self.architecture_tests else 0)
        )


def get_git_changed_files() -> list[str]:
    """Get changed files from git diff. Returns empty list if git unavailable."""
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
        files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        return files
    except FileNotFoundError:
        return []


def get_git_latest_change_time() -> float:
    """Get the modification time of the most recently changed file."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

        latest_time = 0.0
        for f in files:
            file_path = PROJECT_ROOT / f
            if file_path.exists():
                latest_time = max(latest_time, file_path.stat().st_mtime)
        return latest_time
    except Exception:
        return 0.0


def load_change_report() -> dict[str, Any]:
    """Load change-report.json, regenerating if stale or missing."""
    report_path = GENERATED_DIR / "change-report.json"

    # Check if report exists and is fresh
    if report_path.exists():
        report_mtime = report_path.stat().st_mtime
        git_mtime = get_git_latest_change_time()

        # If git has newer changes, regenerate
        if git_mtime > report_mtime and git_mtime > 0:
            print("Regenerating stale change-report.json...")
            regenerate_result = subprocess.run(
                [sys.executable, str(BACKEND_DIR / "tools" / "change_intelligence.py")],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            if regenerate_result.returncode != 0:
                print(f"Warning: CIF regeneration failed: {regenerate_result.stderr}")

    # If still missing, generate fresh report
    if not report_path.exists():
        changed_files = get_git_changed_files()
        if changed_files:
            print("Generating change-report.json...")
            file_args = [sys.executable, str(BACKEND_DIR / "tools" / "change_intelligence.py")] + changed_files
            regenerate_result = subprocess.run(
                file_args,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            if regenerate_result.returncode != 0:
                raise RuntimeError(f"CIF generation failed: {regenerate_result.stderr}")
        else:
            # No changes, create empty report
            empty_report = {
                "generated_at": datetime.now(UTC).isoformat(),
                "git_sha": "unknown",
                "changes": [],
                "overall": {"risk": "LOW", "score": 0},
            }
            GENERATED_DIR.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w") as f:
                json.dump(empty_report, f, indent=2)

    with open(report_path) as f:
        return json.load(f)


def build_selective_plan(change_report: dict[str, Any]) -> SelectivePlan:
    """Build selective plan from change report."""
    plan = SelectivePlan()

    changes = change_report.get("changes", [])
    plan.changed_files = [c.get("file", "") for c in changes if c.get("file")]

    # Collect unique test references
    for change in changes:
        capabilities = change.get("capabilities", [])

        # Skip UNKNOWN capabilities - they indicate untracked files
        if "UNKNOWN" in capabilities and len(capabilities) == 1:
            continue

        affected = change.get("affected", {})

        # Capability smoke tests
        for cap_test in affected.get("capability_tests", []):
            if cap_test.startswith("tests/capabilities/"):
                cap_name = cap_test.replace("tests/capabilities/", "")
                plan.capability_tests.add(cap_name)

        # Property tests (directory paths) - use full path
        for prop_test in affected.get("property_tests", []):
            if prop_test.startswith("tests/properties"):
                plan.property_tests.add(prop_test)
            elif "/" in prop_test and prop_test.rsplit("/", 1)[0].startswith("tests/properties"):
                plan.property_tests.add(prop_test.rsplit("/", 1)[0])

        # Golden tests (dataset names)
        for golden_test in affected.get("golden_tests", []):
            plan.golden_tests.add(golden_test)

        # Invariants
        for inv in affected.get("invariants", []):
            plan.invariant_tests.add(inv)

    return plan


def estimate_runtime(plan: SelectivePlan) -> float:
    """Estimate runtime in seconds based on test suites."""
    # Base estimates per test suite type
    estimates = {
        "architecture": 8.0,
        "capability": 5.0,
        "property": 12.0,
        "golden": 6.0,
        "invariant": 4.0,
    }

    total = 0.0
    if plan.architecture_tests:
        total += estimates["architecture"]
    total += len(plan.capability_tests) * estimates["capability"]
    total += len(plan.property_tests) * estimates["property"]
    total += len(plan.golden_tests) * estimates.get("golden", 1) if plan.golden_tests else 0
    total += len(plan.invariant_tests) * estimates["invariant"]

    return round(total, 1)


def generate_plan_md(plan: SelectivePlan) -> str:
    """Generate human-readable plan markdown."""
    lines = [
        "# Selective Verification Plan",
        "",
        f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
    ]

    if plan.changed_files:
        lines.extend([
            "## Changed Files",
            "",
        ])
        for f in plan.changed_files:
            lines.append(f"- `{f}`")
        lines.append("")

    lines.extend([
        "## Execution Plan",
        "",
    ])

    # Count unique items
    counts = {
        "architecture": 1 if plan.architecture_tests else 0,
        "capability": len(plan.capability_tests),
        "property": len(plan.property_tests),
        "golden": len(plan.golden_tests),
        "invariant": len(plan.invariant_tests),
    }

    idx = 1
    if counts["architecture"]:
        lines.append(f"{idx}. Architecture tests (1)")
        idx += 1
    if counts["capability"]:
        lines.append(f"{idx}. Capability smoke tests ({counts['capability']})")
        idx += 1
    if counts["property"]:
        lines.append(f"{idx}. Property tests ({counts['property']})")
        idx += 1
    if counts["golden"]:
        lines.append(f"{idx}. Golden tests ({counts['golden']})")
        idx += 1
    if counts["invariant"]:
        lines.append(f"{idx}. Invariant tests ({counts['invariant']})")
        idx += 1

    lines.extend([
        "",
        f"## Estimated Runtime: {estimate_runtime(plan)} seconds",
        "",
    ])

    if not plan.changed_files:
        lines.extend([
            "*No changes detected - no targeted verification needed.*",
            "",
        ])

    return "\n".join(lines)


def generate_summary_json(plan: SelectivePlan, runtime_seconds: float, tests_run: int, result: str) -> dict[str, Any]:
    """Generate machine-readable summary."""
    return {
        "mode": "selective",
        "generated_at": datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC'),
        "runtime_seconds": runtime_seconds,
        "tests_run": tests_run,
        "tests_skipped": get_all_test_count() - tests_run,
        "result": result,
        "suites": {
            "architecture": len(plan.architecture_tests) > 0,
            "capability": list(plan.capability_tests),
            "property": list(plan.property_tests),
            "golden": list(plan.golden_tests),
            "invariant": list(plan.invariant_tests),
        },
        "changed_files": plan.changed_files,
    }


def generate_verification_matrix(plan: SelectivePlan, result: str) -> str:
    """Generate verification matrix markdown."""
    # Load capability registry for all capabilities
    all_capabilities = get_all_capabilities()
    executed_caps = set(plan.capability_tests)

    lines = [
        "# Verification Matrix",
        "",
        f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
    ]

    if plan.changed_files:
        lines.extend([
            "## Changed Files",
            "",
        ])
        for f in plan.changed_files:
            lines.append(f"- `{f}`")
        lines.append("")

    lines.extend([
        "## Executed",
        "",
    ])

    if plan.architecture_tests:
        lines.append("| Suite | Status |")
        lines.append("|-------|--------|")
        lines.append("| Architecture | ✓ |")
    else:
        lines.append("| Suite | Status |")
        lines.append("|-------|--------|")

    for cap in sorted(plan.capability_tests):
        lines.append(f"| {cap} (capability) | ✓ |")

    for prop in sorted(plan.property_tests):
        lines.append(f"| {prop.replace('tests/properties/', '')} (property) | ✓ |")

    for golden in sorted(plan.golden_tests):
        lines.append(f"| {golden} (golden) | ✓ |")

    for inv in sorted(plan.invariant_tests):
        lines.append(f"| {inv} (invariant) | ✓ |")

    lines.extend([
        "",
        "## Skipped",
        "",
    ])

    skipped_caps = all_capabilities - executed_caps - {"UNKNOWN"}
    for cap in sorted(skipped_caps):
        lines.append(f"| {cap} | ✓ |")

    lines.extend([
        "",
        f"## Result: {result}",
        "",
        f"## Runtime Saved: ~{calculate_savings(plan)}%",
        "",
    ])

    return "\n".join(lines)


def get_all_capabilities() -> set[str]:
    """Get all capability IDs from registry."""
    import yaml
    registry_path = GENERATED_DIR / "capability-registry.yaml"
    if not registry_path.exists():
        return set()

    with open(registry_path) as f:
        data = yaml.safe_load(f) or {"capabilities": []}

    return {cap.get("id", "") for cap in data.get("capabilities", []) if cap.get("id")}


def get_all_test_count() -> int:
    """Count all test files for skipped metric."""
    import os
    count = 0
    for _root, _dirs, files in os.walk(BACKEND_DIR / "tests"):
        count += len([f for f in files if f.startswith("test_") and f.endswith(".py")])
    return count


def calculate_savings(plan: SelectivePlan) -> int:
    """Calculate percentage of tests skipped."""
    all_count = get_all_test_count()
    if all_count == 0:
        return 0
    # Estimate skipped based on suites not run
    skipped = max(0, all_count - plan.total_test_suites * 3)  # Rough estimate
    return int((skipped / all_count) * 100) if all_count > 0 else 0


def load_history() -> list[dict[str, Any]]:
    """Load selective history, keeping last 100 runs."""
    history_path = GENERATED_DIR / "selective-history.json"
    if history_path.exists():
        with open(history_path) as f:
            return json.load(f)
    return []


def save_history(history: list[dict[str, Any]]) -> None:
    """Save history, keeping only last 100 runs."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    # Keep only last 100
    history = history[-100:]
    with open(GENERATED_DIR / "selective-history.json", "w") as f:
        json.dump(history, f, indent=2)


def run_tests_sequential(plan: SelectivePlan) -> tuple[int, float]:
    """Run tests sequentially, stopping on first failure.

    Returns (exit_code, runtime_seconds).
    """
    start_time = time.time()

    # Architecture tests
    if plan.architecture_tests:
        result = subprocess.run(
            ["pytest", "tests/architecture", "-q", "--tb=short"],
            cwd=BACKEND_DIR,
        )
        if result.returncode != 0:
            return result.returncode, time.time() - start_time

    # Capability smoke tests
    for cap in sorted(plan.capability_tests):
        result = subprocess.run(
            ["pytest", f"tests/capabilities/{cap}", "-q", "--tb=short"],
            cwd=BACKEND_DIR,
        )
        if result.returncode != 0:
            return result.returncode, time.time() - start_time

    # Property tests
    for prop in sorted(plan.property_tests):
        result = subprocess.run(
            ["pytest", prop, "-q", "--tb=short"],
            cwd=BACKEND_DIR,
        )
        if result.returncode != 0:
            return result.returncode, time.time() - start_time

    # Golden tests
    if plan.golden_tests:
        keywords = ",".join(sorted(plan.golden_tests)[:5])
        result = subprocess.run(
            ["pytest", "tests/golden", "-k", keywords, "-q", "--tb=short"],
            cwd=BACKEND_DIR,
        )
        if result.returncode != 0:
            return result.returncode, time.time() - start_time

    # Invariant tests
    for inv in sorted(plan.invariant_tests):
        result = subprocess.run(
            ["pytest", inv, "-q", "--tb=short"],
            cwd=BACKEND_DIR,
        )
        if result.returncode != 0:
            return result.returncode, time.time() - start_time

    return 0, time.time() - start_time


def run_full_verification() -> tuple[int, float]:
    """Run full verification pipeline.

    Returns (exit_code, runtime_seconds).
    """
    start_time = time.time()

    # Run via verify-local.sh equivalent but without spawning
    result = subprocess.run(
        [sys.executable, str(BACKEND_DIR / "tools" / "change_intelligence.py")],
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:
        return result.returncode, time.time() - start_time

    # Run all test suites
    result = subprocess.run(
        ["pytest", "tests/architecture", "-q", "--tb=short", "--maxfail=3"],
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        return result.returncode, time.time() - start_time

    result = subprocess.run(
        ["pytest", "tests/capabilities", "-q", "--tb=short", "--maxfail=3"],
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        return result.returncode, time.time() - start_time

    result = subprocess.run(
        ["pytest", "tests/properties", "-q", "--tb=short", "--maxfail=3"],
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        return result.returncode, time.time() - start_time

    result = subprocess.run(
        ["pytest", "tests/golden", "-q", "--tb=short", "--maxfail=3"],
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        return result.returncode, time.time() - start_time

    return 0, time.time() - start_time


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Selective Verification Framework")
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Generate and print selective plan only",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute selective verification",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable summary",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Force full verification",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to analyze (default: git diff)",
    )
    args = parser.parse_args()

    # Load capability registry first
    registry_path = GENERATED_DIR / "capability-registry.yaml"
    if not registry_path.exists():
        print("ERROR: capability-registry.yaml not found. Run check_coverage.py first.")
        sys.exit(1)

    # Get changed files
    changed_files = args.files if args.files else get_git_changed_files()

    # No git repo or no changes - handle appropriately
    if not changed_files and not args.full:
        print("No changes detected - nothing to verify selectively.")
        # Generate empty artifacts
        plan = SelectivePlan()
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)

        with open(GENERATED_DIR / "selective-plan.md", "w") as f:
            f.write(generate_plan_md(plan))

        if args.json:
            summary = generate_summary_json(plan, 0.0, 0, "PASS")
            print(json.dumps(summary, indent=2))

        sys.exit(0)

    # Handle --full
    if args.full:
        print("=== Running Full Verification ===")
        exit_code, runtime = run_full_verification()

        if args.json:
            summary = {
                "mode": "full",
                "runtime_seconds": runtime,
                "tests_run": get_all_test_count(),
                "tests_skipped": 0,
                "result": "PASS" if exit_code == 0 else "FAIL",
            }
            print(json.dumps(summary, indent=2))

        sys.exit(exit_code)

    # Load or regenerate change report
    # If files were explicitly provided, generate report directly; otherwise use git diff
    if args.files:
        # Generate report for specific files
        file_args = [sys.executable, str(BACKEND_DIR / "tools" / "change_intelligence.py")] + args.files
        result = subprocess.run(
            file_args,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"CIF generation failed: {result.stderr}")
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        with open(GENERATED_DIR / "change-report.json") as f:
            change_report = json.load(f)
    else:
        change_report = load_change_report()

    # Build plan
    plan = build_selective_plan(change_report)

    # Generate artifacts
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # Check for UNKNOWN capabilities - fall back to full
    has_unknown = any("UNKNOWN" in str(c.get("capabilities", [])) for c in change_report.get("changes", []))
    if has_unknown and len(plan.changed_files) > 0:
        print("Unknown capability detected - falling back to full verification...")
        exit_code, runtime = run_full_verification()

        # Generate summary for full run
        summary = generate_summary_json(plan, runtime, get_all_test_count(), "PASS" if exit_code == 0 else "FAIL")
        with open(GENERATED_DIR / "selective-summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # Save history
        history = load_history()
        history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "changed_files": plan.changed_files,
            "executed_suites": ["full"],
            "runtime_seconds": runtime,
            "pass": exit_code == 0,
        })
        save_history(history)

        if args.json:
            print(json.dumps(summary, indent=2))

        sys.exit(exit_code)

    # Handle --plan
    if args.plan:
        print(generate_plan_md(plan))

        # Also write to file
        with open(GENERATED_DIR / "selective-plan.md", "w") as f:
            f.write(generate_plan_md(plan))
            f.write(f"\nFile saved: {GENERATED_DIR / 'selective-plan.md'}\n")

        # Generate verification matrix
        with open(GENERATED_DIR / "verification-matrix.md", "w") as f:
            f.write(generate_verification_matrix(plan, "PLANNED"))

        sys.exit(0)

    # Default: execute if --run specified
    if args.run:
        print("=== Running Selective Verification ===")
        print(f"Test suites to execute: {plan.total_test_suites}")

        exit_code, runtime = run_tests_sequential(plan)

        # Generate summary
        summary = generate_summary_json(plan, runtime, plan.total_test_suites, "PASS" if exit_code == 0 else "FAIL")
        with open(GENERATED_DIR / "selective-summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # Generate verification matrix
        with open(GENERATED_DIR / "verification-matrix.md", "w") as f:
            f.write(generate_verification_matrix(plan, "PASS" if exit_code == 0 else "FAIL"))

        # Save history
        history = load_history()
        history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "changed_files": plan.changed_files,
            "executed_suites": {
                "architecture": len(plan.architecture_tests) > 0,
                "capability": list(plan.capability_tests),
                "property": list(plan.property_tests),
                "golden": list(plan.golden_tests),
                "invariant": list(plan.invariant_tests),
            },
            "runtime_seconds": runtime,
            "pass": exit_code == 0,
        })
        save_history(history)

        if args.json:
            print(json.dumps(summary, indent=2))

        print(f"\nResult: {'PASS' if exit_code == 0 else 'FAIL'}")
        print(f"Runtime: {runtime:.1f} seconds")

        sys.exit(exit_code)

    # Default behavior if no flags: print plan
    print(generate_plan_md(plan))
    print("\nUse --run to execute, --json for machine-readable summary.")


if __name__ == "__main__":
    main()
