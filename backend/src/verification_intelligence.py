"""Verification Intelligence CLI — stub for Program 1.

This module provides the command-line interface expected by
.github/workflows/backend.yml. It delegates to the intelligence
layer when available, and falls back to a default plan when not.

Program 2 will replace this with a full implementation.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    """Entry point for python -m verification_intelligence."""
    selective = "--selective" in sys.argv
    output_json = "--json" in sys.argv

    plan = {
        "strategy": "full" if not selective else "selective",
        "overall_risk": "UNKNOWN",
        "affected_capabilities": [],
        "must_run_jobs": [
            "property-tests",
            "contract-tests",
            "capability-tests",
            "integration-tests",
            "invariant-tests",
            "migration-tests",
            "capability-validation",
        ],
        "skipped_jobs": [],
        "mutation_targets": [],
        "regression_suites": [],
        "estimated_runtime_seconds": 0,
    }

    if output_json:
        print(json.dumps(plan, indent=2))
    else:
        print(f"Strategy: {plan['strategy']}")
        print(f"Must run: {', '.join(plan['must_run_jobs'])}")
        print(f"Skipped: {', '.join(plan['skipped_jobs'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
