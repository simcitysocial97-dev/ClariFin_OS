#!/usr/bin/env python3
"""
.github/scripts/check_coverage_threshold.py

Reads coverage.json and enforces minimum thresholds.
Exits with code 1 if any threshold is not met.

Usage:
    python check_coverage_threshold.py --coverage-file path/to/coverage.json
"""

import json
import sys
import argparse
from pathlib import Path


# ── Thresholds per phase ──────────────────────────────────────────────────────
# Update these as you progress through phases
THRESHOLDS = {
    # Phase 1 thresholds (current)
    "overall": 60,  # Will increase to 80 in Phase 3
    "engines": 70,  # Critical path — higher threshold
    "repositories": 50,  # Will increase in Phase 2
    "services": 50,  # Will increase in Phase 2
}


def load_coverage(coverage_file: Path) -> dict:
    """Load coverage.json produced by pytest-cov."""
    with open(coverage_file) as f:
        return json.load(f)


def extract_coverage_by_module(coverage_data: dict) -> dict[str, float]:
    """
    Extract coverage percentage per module group.

    coverage.json structure:
    {
        "totals": {"percent_covered": 72.5, ...},
        "files": {
            "src/engines/loan_engine.py": {
                "summary": {"percent_covered": 85.0}
            },
            ...
        }
    }
    """
    results = {}

    # Overall coverage
    totals = coverage_data.get("totals", {})
    results["overall"] = totals.get("percent_covered", 0.0)

    # Per-module-group coverage
    files = coverage_data.get("files", {})

    module_groups = {
        "engines": [],
        "repositories": [],
        "services": [],
    }

    for filepath, file_data in files.items():
        pct = file_data.get("summary", {}).get("percent_covered", 0.0)

        if "engine" in filepath.lower():
            module_groups["engines"].append(pct)
        elif "repositor" in filepath.lower():
            module_groups["repositories"].append(pct)
        elif "service" in filepath.lower():
            module_groups["services"].append(pct)

    # Average per group
    for group, percentages in module_groups.items():
        if percentages:
            results[group] = sum(percentages) / len(percentages)
        else:
            results[group] = None  # No files in this group

    return results


def check_thresholds(
    coverage_results: dict[str, float], thresholds: dict[str, int]
) -> tuple[bool, list[str]]:
    """
    Compare coverage results against thresholds.

    Returns:
        (passed: bool, failures: list[str])
    """
    failures = []

    for module, threshold in thresholds.items():
        actual = coverage_results.get(module)

        if actual is None:
            # No files in this module group — skip
            print(f"  {module:20s}: NO FILES (skipped)")
            continue

        status = "✓" if actual >= threshold else "✗"
        print(f"  {module:20s}: {actual:5.1f}% (threshold: {threshold}%) {status}")

        if actual < threshold:
            failures.append(f"{module}: {actual:.1f}% is below threshold {threshold}%")

    return len(failures) == 0, failures


def main():
    parser = argparse.ArgumentParser(
        description="Check coverage against phase thresholds"
    )
    parser.add_argument(
        "--coverage-file",
        type=Path,
        default=Path("backend/tests/generated/coverage.json"),
        help="Path to coverage.json",
    )
    parser.add_argument(
        "--phase", type=int, default=1, help="Current phase (1-4), affects thresholds"
    )

    args = parser.parse_args()

    # Adjust thresholds by phase
    phase_multipliers = {1: 1.0, 2: 1.2, 3: 1.4, 4: 1.6}
    multiplier = phase_multipliers.get(args.phase, 1.0)

    adjusted_thresholds = {
        k: min(100, int(v * multiplier)) for k, v in THRESHOLDS.items()
    }

    print("=" * 50)
    print(f"  Coverage Threshold Check (Phase {args.phase})")
    print("=" * 50)

    # Load coverage data
    if not args.coverage_file.exists():
        print(f"ERROR: Coverage file not found: {args.coverage_file}")
        print("Run pytest with --cov-report=json first")
        sys.exit(1)

    coverage_data = load_coverage(args.coverage_file)
    coverage_results = extract_coverage_by_module(coverage_data)

    print("\nCoverage Results:")
    passed, failures = check_thresholds(coverage_results, adjusted_thresholds)

    print("")
    if passed:
        print("✓ All thresholds met!")
        sys.exit(0)
    else:
        print("✗ Threshold violations:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)


if __name__ == "__main__":
    main()
