"""Selective Verification Framework Tests.

Validates plan generation, duplicate removal, JSON parsing, and verification matrix output.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"


def test_plan_generation() -> None:
    """SVF must generate selective-plan.md for changed files."""
    result = subprocess.run(
        [
            sys.executable,
            "backend/tools/selective_verify.py",
            "--plan",
            "backend/src/engines/cashflow_engine.py",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"SVF plan failed: {result.stderr}"

    plan_path = GENERATED_DIR / "selective-plan.md"
    assert plan_path.exists(), "selective-plan.md not generated"

    content = plan_path.read_text()
    assert "Changed Files" in content, "Plan missing Changed Files section"
    assert "Execution Plan" in content, "Plan missing Execution Plan section"
    assert "Estimated Runtime" in content, "Plan missing Estimated Runtime"


def test_duplicate_removal() -> None:
    """SVF must remove duplicate test paths."""
    # Import and test duplicate removal logic
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'backend/tools')
from selective_verify import build_selective_plan

# Create a report with duplicates
report = {
    "changes": [
        {
            "file": "backend/src/engines/cashflow_engine.py",
            "capabilities": ["household_cashflow"],
            "affected": {
                "capability_tests": ["tests/capabilities/household_cashflow", "tests/capabilities/household_cashflow"],
                "property_tests": ["tests/properties/cashflow", "tests/properties/cashflow"],
                "golden_tests": ["normal_household", "normal_household"],
                "invariants": ["tests/invariants/test_cashflow.py", "tests/invariants/test_cashflow.py"],
            }
        }
    ]
}

plan = build_selective_plan(report)
assert len(plan.capability_tests) == 1, f"Duplicates not removed: {plan.capability_tests}"
assert len(plan.property_tests) == 1, f"Duplicates not removed: {plan.property_tests}"
assert len(plan.golden_tests) == 1, f"Duplicates not removed: {plan.golden_tests}"
assert len(plan.invariant_tests) == 1, f"Duplicates not removed: {plan.invariant_tests}"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Duplicate removal test failed: {result.stderr}"
    assert "PASS" in result.stdout


def test_invalid_paths_ignored_safely() -> None:
    """SVF must ignore invalid paths without crashing in its logic."""
    result = subprocess.run(
        [
            sys.executable,
            "backend/tools/selective_verify.py",
            "--plan",
            "nonexistent_file.py",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    # Unknown files trigger fallback to full verification
    # The key is that SVF processes the unknown file without crashing in its own logic
    output = result.stdout.lower()
    assert "unknown" in output or "full" in output or "fallback" in output


def test_dry_run_output() -> None:
    """SVF --plan must print plan to stdout."""
    result = subprocess.run(
        [
            sys.executable,
            "backend/tools/selective_verify.py",
            "--plan",
            "backend/src/engines/cashflow_engine.py",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Dry-run failed: {result.stderr}"
    assert "Selective Verification Plan" in result.stdout
    assert "cashflow_engine.py" in result.stdout


def test_json_parsing() -> None:
    """SVF must correctly parse change-report.json structure."""
    report_path = GENERATED_DIR / "change-report.json"

    if report_path.exists():
        with open(report_path) as f:
            data = json.load(f)

        assert "changes" in data, "Missing 'changes' key"
        assert "overall" in data, "Missing 'overall' key"
        assert isinstance(data["changes"], list), "'changes' must be a list"

        for change in data["changes"]:
            assert "file" in change, "Change missing 'file'"
            assert "capabilities" in change, "Change missing 'capabilities'"
            assert "affected" in change, "Change missing 'affected'"


def test_json_summary_flag() -> None:
    """SVF --json must generate selective-summary.json."""
    result = subprocess.run(
        [
            sys.executable,
            "backend/tools/selective_verify.py",
            "--plan",
            "--json",
            "backend/src/engines/cashflow_engine.py",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"JSON summary failed: {result.stderr}"

    summary_path = GENERATED_DIR / "selective-summary.json"
    assert summary_path.exists(), "selective-summary.json not generated"

    with open(summary_path) as f:
        summary = json.load(f)

    assert "mode" in summary, "Summary missing 'mode'"
    assert "runtime_seconds" in summary, "Summary missing 'runtime_seconds'"
    assert "tests_run" in summary, "Summary missing 'tests_run'"
    assert "tests_skipped" in summary, "Summary missing 'tests_skipped'"
    assert "result" in summary, "Summary missing 'result'"


def test_empty_changes_handled() -> None:
    """SVF must handle no changes gracefully."""
    result = subprocess.run(
        [sys.executable, "backend/tools/selective_verify.py", "--plan"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env={"GIT_DIR": "/nonexistent"},  # Force no git diff
    )
    # Should succeed
    assert result.returncode == 0, f"Empty changes handling failed: {result.stderr}"
    assert (
        "No changes detected" in result.stdout
        or "selective-plan.md" in result.stdout.lower()
    )


def test_verification_matrix_generated() -> None:
    """SVF must generate verification-matrix.md."""
    result = subprocess.run(
        [
            sys.executable,
            "backend/tools/selective_verify.py",
            "--plan",
            "backend/src/engines/cashflow_engine.py",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"SVF failed: {result.stderr}"

    matrix_path = GENERATED_DIR / "verification-matrix.md"
    assert matrix_path.exists(), "verification-matrix.md not generated"

    content = matrix_path.read_text()
    assert "Changed Files" in content, "Matrix missing Changed Files section"
    assert "Executed" in content, "Matrix missing Executed section"
    assert "Skipped" in content, "Matrix missing Skipped section"
