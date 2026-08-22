#!/usr/bin/env python3
"""
.github/scripts/generate_mutation_report.py

Reads mutmut results and generates a markdown report.
Saves to tests/generated/mutation/mutation-report.md

Usage:
    python generate_mutation_report.py
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve paths relative to repository root, not script location or cwd.
# The script may be invoked from backend/, repo root, or any directory.
_SCRIPT_DIR = Path(__file__).resolve().parent  # .github/scripts/
_REPO_ROOT = _SCRIPT_DIR.parent.parent  # repo root
_OUTPUT_DIR = _REPO_ROOT / "backend" / "tests" / "generated" / "mutation"


def run_command(cmd: list[str]) -> tuple[str, int]:
    """Run a shell command and return output + exit code."""
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(_REPO_ROOT / "backend")
    )
    return result.stdout + result.stderr, result.returncode


def get_mutation_results() -> dict:
    """Parse mutmut results into structured data."""
    output, _ = run_command(["mutmut", "results"])

    results = {
        "killed": 0,
        "survived": 0,
        "timeout": 0,
        "suspicious": 0,
        "skipped": 0,
    }

    for line in output.splitlines():
        line = line.strip()
        if "Killed:" in line:
            try:
                results["killed"] = int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
        elif "Survived:" in line:
            try:
                results["survived"] = int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
        elif "Timeout:" in line:
            try:
                results["timeout"] = int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass

    total = results["killed"] + results["survived"]
    results["total"] = total
    results["score"] = round(results["killed"] / total * 100, 1) if total > 0 else 0.0

    return results


def get_surviving_mutants() -> list[str]:
    """Get list of surviving mutants."""
    output, _ = run_command(["mutmut", "show"])
    return [line for line in output.splitlines() if line.strip()]


def generate_report(results: dict, survivors: list[str]) -> str:
    """Generate markdown report."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    score = results["score"]

    # Determine status
    if score >= 80:
        status = "✅ PASSING"
    elif score >= 60:
        status = "⚠️ BELOW TARGET"
    else:
        status = "❌ FAILING"

    report = f"""# Mutation Testing Report

**Generated:** {timestamp}  
**Status:** {status}  
**Mutation Score:** {score}%

---

## Summary

| Metric | Count |
|--------|-------|
| Total Mutants | {results["total"]} |
| Killed | {results["killed"]} |
| Survived | {results["survived"]} |
| Timeout | {results["timeout"]} |
| Score | {score}% |

---

## Phase Targets

| Phase | Target | Current | Status |
|-------|--------|---------|--------|
| Phase 1 | ≥60% | {score}% | {"✅" if score >= 60 else "❌"} |
| Phase 3 | ≥80% | {score}% | {"✅" if score >= 80 else "❌"} |

---

## Surviving Mutants

These mutants were NOT killed by your tests.
Each one represents a gap in test effectiveness.

"""

    if survivors:
        report += "```\n"
        report += "\n".join(survivors[:50])  # Limit to 50
        if len(survivors) > 50:
            report += f"\n... and {len(survivors) - 50} more"
        report += "\n```\n"
    else:
        report += "_No surviving mutants! All mutants killed._\n"

    report += """
---

## Action Items

"""

    if results["survived"] > 0:
        report += f"""- [ ] Review {results["survived"]} surviving mutants above
- [ ] Add targeted tests for each surviving mutant
- [ ] Re-run mutation testing after adding tests
"""
    else:
        report += "- ✅ No action items — all mutants killed\n"

    return report


def main():
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Gathering mutation results...")
    results = get_mutation_results()

    print("Getting surviving mutants...")
    survivors = get_surviving_mutants()

    print("Generating report...")
    report = generate_report(results, survivors)

    # Save markdown report
    report_path = _OUTPUT_DIR / "mutation-report.md"
    report_path.write_text(report)
    print(f"Report saved: {report_path}")

    # Save JSON for downstream processing
    json_path = _OUTPUT_DIR / "mutation-summary.json"
    json_path.write_text(json.dumps(results, indent=2))
    print(f"JSON saved: {json_path}")

    # Print summary
    print(f"\nMutation Score: {results['score']}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
