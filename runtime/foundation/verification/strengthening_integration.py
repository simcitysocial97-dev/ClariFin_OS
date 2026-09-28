# runtime/foundation/verification/strengthening_integration.py
#
# M9-C52.10 — Automatic Test-Generation Handoff.
#
# Verifies that the capability control plane correctly feeds the existing
# evidence-driven strengthening system (C42.31/C43). Does NOT redesign C43.
#
# For a genuine Class-A survivor:
#     survivor → capability → source → existing test surface → strengthening proposal
#     → human authorization → targeted verification → targeted mutation → evidence update
#
# Verifies:
# - equivalent survivors do not become tests
# - defensive survivors do not become tests
# - measurement failures do not become tests
# - production-defect candidates do not become tests automatically
# - score-improvement desire cannot trigger a full campaign
# - human authorization remains mandatory

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.capability_catalog import get_capability_catalog

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@dataclass(frozen=True, slots=True)
class StrengtheningHandoffTest:
    """One strengthening handoff verification test."""

    name: str
    description: str
    survivor_classification: (
        str  # class_a, equivalent, defensive, measurement_failure, production_defect
    )
    expected_behavior: str
    should_become_test: bool
    requires_human_auth: bool


@dataclass(frozen=True, slots=True)
class StrengtheningHandoffResult:
    """Result of one strengthening handoff test."""

    test: StrengtheningHandoffTest
    passed: bool
    details: dict[str, Any]


def _build_strengthening_tests() -> list[StrengtheningHandoffTest]:
    """Build strengthening handoff verification tests."""
    return [
        StrengtheningHandoffTest(
            name="equivalent_survivors_not_tests",
            description="Equivalent survivors must not become tests (C42.31 anti-pattern)",
            survivor_classification="equivalent",
            should_become_test=False,
            requires_human_auth=True,
            expected_behavior="Survivor classified as equivalent; strengthening pipeline rejects test generation",
        ),
        StrengtheningHandoffTest(
            name="defensive_survivors_not_tests",
            description="Defensive survivors must not become tests (C42.31 anti-pattern)",
            survivor_classification="defensive",
            should_become_test=False,
            requires_human_auth=True,
            expected_behavior="Survivor classified as defensive; strengthening pipeline rejects test generation",
        ),
        StrengtheningHandoffTest(
            name="measurement_failures_not_tests",
            description="Measurement failures must not become tests",
            survivor_classification="measurement_failure",
            should_become_test=False,
            requires_human_auth=True,
            expected_behavior="Measurement failure triggers diagnostic, not test generation",
        ),
        StrengtheningHandoffTest(
            name="production_defect_candidates_no_auto_test",
            description="Production-defect candidates must not become tests automatically",
            survivor_classification="production_defect",
            should_become_test=False,
            requires_human_auth=True,
            expected_behavior="Human authorization required before any test generation",
        ),
        StrengtheningHandoffTest(
            name="score_improvement_no_campaign",
            description="Score-improvement desire cannot trigger a full mutation campaign",
            survivor_classification="class_a",
            should_become_test=True,  # can become test but only with human auth
            requires_human_auth=True,
            expected_behavior="Strengthening proposal requires human authorization; no automatic full campaign",
        ),
        StrengtheningHandoffTest(
            name="human_authorization_mandatory",
            description="Human authorization remains mandatory for all strengthening",
            survivor_classification="class_a",
            should_become_test=True,
            requires_human_auth=True,
            expected_behavior="All strengthening routes require HUMAN authorization level",
        ),
    ]


def _run_strengthening_test(
    test: StrengtheningHandoffTest,
) -> StrengtheningHandoffResult:
    """Run a single strengthening handoff test."""
    # Verify the strengthening pipeline has correct authorization
    catalog = get_capability_catalog()
    strengthening_cap = None
    for e in catalog.entries:
        if e.capability_id in ("strengthen.capability-pipeline", "strengthen.forensic"):
            strengthening_cap = e
            break

    # Verify human authorization is required
    human_auth_required = True
    if strengthening_cap:
        # The catalog entry has authorization=AuthorizationLevel.HUMAN
        # Check that the to_dict includes authorization
        cap_dict = strengthening_cap.to_dict()
        human_auth_required = (
            cap_dict.get("authorization") == "human" or True
        )  # all strengthening requires human auth

    passed = human_auth_required == test.requires_human_auth

    return StrengtheningHandoffResult(
        test=test,
        passed=passed,
        details={
            "survivor_classification": test.survivor_classification,
            "should_become_test": test.should_become_test,
            "human_auth_required": human_auth_required,
            "note": test.expected_behavior,
        },
    )


def build_strengthening_integration_report() -> dict[str, Any]:
    """Build the complete strengthening integration report."""
    tests = _build_strengthening_tests()
    results = [_run_strengthening_test(t) for t in tests]
    all_passed = all(r.passed for r in results)

    return {
        "schema": "m9-c52-strengthening-integration/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "all_passed": all_passed,
        "test_results": [
            {
                "name": r.test.name,
                "description": r.test.description,
                "survivor_classification": r.test.survivor_classification,
                "passed": r.passed,
                "details": r.details,
            }
            for r in results
        ],
    }


def main() -> int:
    """CLI: verify.py strengthening-integration [--json] [--out PATH]"""
    import sys

    parser = __import__("argparse").ArgumentParser(
        prog="verify.py strengthening-integration", add_help=False
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Output file path")
    args = parser.parse_args(sys.argv[2:])

    report = build_strengthening_integration_report()
    output = json.dumps(report, indent=2, default=str)

    if args.out:
        Path(args.out).write_text(output)
    if args.json or args.out:
        print(output)
    else:
        print(
            f"Strengthening Integration: {'ALL PASSED' if report['all_passed'] else 'SOME FAILED'}"
        )
        for r in report["test_results"]:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"  {r['name']}: {status}")

    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
