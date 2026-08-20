"""Certification arithmetic — meta-invariant for test totals.

M9-C37: a certification system must never be capable of producing
mathematically inconsistent test totals (e.g. "66/50 PASS", or a junit
document claiming ``tests=26`` alongside ``passed=19, failed=0, skipped=0``).

The invariant:

    total = len(all_executed_tests)
    passed = count(PASS); failed = count(FAIL); skipped = count(SKIP)
    passed + failed + skipped == total

This module is the single authority that enforces the invariant. Both the
verification summary model and the JUnit evidence collector route their
arithmetic through it, so no code path can silently emit inconsistent totals.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


class TotalsInconsistentError(ValueError):
    """Raised when recorded totals are mathematically inconsistent."""


@dataclass(frozen=True, slots=True)
class TestTotals:
    total: int
    passed: int
    failed: int
    skipped: int

    @property
    def consistent(self) -> bool:
        return self.passed + self.failed + self.skipped == self.total

    def assert_consistent(self, context: str = "") -> "TestTotals":
        assert_totals_consistent(
            self.total, self.passed, self.failed, self.skipped, context=context
        )
        return self


def assert_totals_consistent(
    total: int,
    passed: int,
    failed: int,
    skipped: int,
    *,
    context: str = "",
) -> None:
    computed = passed + failed + skipped
    if computed != total:
        raise TotalsInconsistentError(
            f"certification arithmetic violated: "
            f"passed({passed}) + failed({failed}) + skipped({skipped}) "
            f"= {computed} != total({total})" + (f" [{context}]" if context else "")
        )


def compute_totals_from_junit(path: Path) -> TestTotals:
    """Derive test totals by counting testcase nodes, never trusting counters."""
    tree = ET.parse(path)
    total = passed = failed = skipped = 0
    for testcase in tree.iter("testcase"):
        total += 1
        if testcase.find("failure") is not None:
            failed += 1
        elif testcase.find("error") is not None:
            failed += 1
        elif testcase.find("skipped") is not None:
            skipped += 1
        else:
            passed += 1
    return TestTotals(total=total, passed=passed, failed=failed, skipped=skipped)


def verify_junit_consistency(path: Path) -> TestTotals:
    """Parse a JUnit XML, cross-check the declared counters against the actual
    testcase nodes, and enforce the meta-invariant.

    Raises ``TotalsInconsistentError`` when the functions attribute counters do
    not match the enumerated testcases, or when the arithmetic is broken.
    """
    totals = compute_totals_from_junit(path)
    declared_total = declared_failures = declared_errors = declared_skipped = 0
    tree = ET.parse(path)
    for testsuite in tree.iter("testsuite"):
        declared_total += int(testsuite.get("tests", "0"))
        declared_failures += int(testsuite.get("failures", "0"))
        declared_errors += int(testsuite.get("errors", "0"))
        declared_skipped += int(testsuite.get("skipped", "0"))
    declared_passed = (
        declared_total - declared_failures - declared_errors - declared_skipped
    )
    if (
        declared_total != totals.total
        or declared_passed != totals.passed
        or (declared_failures + declared_errors) != totals.failed
        or declared_skipped != totals.skipped
    ):
        raise TotalsInconsistentError(
            f"junit counters disagree with enumerated testcases in {path}: "
            f"declared tests={declared_total} (passed={declared_passed}, "
            f"failed={declared_failures}+{declared_errors}, skipped={declared_skipped}) "
            f"vs enumerated total={totals.total} (passed={totals.passed}, "
            f"failed={totals.failed}, skipped={totals.skipped})"
        )
    return totals.assert_consistent(context=str(path))
