"""M9-C37: certification arithmetic is a meta-invariant.

Regression tests that pin the rule no certification system may violate:
given every executed test, passed + failed + skipped == total.

These tests assert the framework raises instead of emitting inconsistent
totals such as "66/50 PASS", both for the VerificationSummary model and for
the JUnit evidence collector that feeds the EvidenceAggregator.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from runtime.foundation.verification.models import VerificationSummary
from runtime.foundation.verification.totals import (
    TotalsInconsistentError,
    assert_totals_consistent,
    compute_totals_from_junit,
    verify_junit_consistency,
)
from runtime.system.evidence.collectors.test_results import TestResultCollector


def _summary(**overrides):
    base = dict(
        profile="test",
        total_tasks=4,
        passed=3,
        failed=1,
        skipped=0,
        duration_seconds=1.0,
        report_path="",
        cache_path="",
    )
    base.update(overrides)
    return VerificationSummary(**base)


class TestVerificationSummaryTotalsInvariant:
    def test_consistent_totals_construct(self) -> None:
        s = _summary(total_tasks=10, passed=9, failed=0, skipped=1)
        assert s.total_tasks == 10

    def test_inconsistent_totals_raise(self) -> None:
        with pytest.raises(ValueError, match="certification arithmetic"):
            _summary(total_tasks=50, passed=66, failed=0, skipped=0)

    def test_missing_tests_raise(self) -> None:
        # Buckets understating the total are equally invalid.
        with pytest.raises(ValueError, match="certification arithmetic"):
            _summary(total_tasks=4, passed=1, failed=1, skipped=1)

    def test_negative_buckets_unrepresentable_as_ints_but_mismatch_total(self) -> None:
        with pytest.raises(ValueError):
            _summary(total_tasks=0, passed=1, failed=0, skipped=0)


class TestTotalsModule:
    def test_assert_consistent_ok(self) -> None:
        assert_totals_consistent(26, 26, 0, 0, context="health-check")

    def test_assert_consistent_violation(self) -> None:
        with pytest.raises(TotalsInconsistentError):
            assert_totals_consistent(50, 66, 0, 0, context="66/50")

    def test_test_totals_assert(self) -> None:
        from runtime.foundation.verification.totals import TestTotals

        with pytest.raises(TotalsInconsistentError):
            TestTotals(total=50, passed=66, failed=0, skipped=0).assert_consistent()


_JUNIT_OK = textwrap.dedent("""\
    <?xml version="1.0" encoding="utf-8"?>
    <testsuites>
      <testsuite name="suite" tests="4" failures="1" errors="1" skipped="1" time="3.5">
        <testcase classname="t" name="pass_one"/>
        <testcase classname="t" name="fail_one"><failure message="boom"/></testcase>
        <testcase classname="t" name="err_one"><error message="kapow"/></testcase>
        <testcase classname="t" name="skip_one"><skipped/></testcase>
      </testsuite>
    </testsuites>
    """)

_JUNIT_LYING_COUNTERS = textwrap.dedent("""\
    <?xml version="1.0" encoding="utf-8"?>
    <testsuites>
      <testsuite name="suite" tests="5" failures="0" errors="0" skipped="0" time="1.0">
        <testcase classname="t" name="one"/>
        <testcase classname="t" name="two"/>
      </testsuite>
    </testsuites>
    """)


class TestJunitEnumeration:
    def test_totals_computed_from_testcases(self, tmp_path: Path) -> None:
        p = tmp_path / "junit.xml"
        p.write_text(_JUNIT_OK, encoding="utf-8")
        t = compute_totals_from_junit(p)
        assert (t.total, t.passed, t.failed, t.skipped) == (4, 1, 2, 1)
        assert assert_totals_consistent(t.total, t.passed, t.failed, t.skipped) is None

    def test_verify_detects_lying_counters(self, tmp_path: Path) -> None:
        p = tmp_path / "junit.xml"
        p.write_text(_JUNIT_LYING_COUNTERS, encoding="utf-8")
        with pytest.raises(TotalsInconsistentError, match="counters disagree"):
            verify_junit_consistency(p)

    def test_verify_accepts_honest_counters(self, tmp_path: Path) -> None:
        p = tmp_path / "junit.xml"
        p.write_text(_JUNIT_OK, encoding="utf-8")
        t = verify_junit_consistency(p)
        assert t.total == 4

    def test_collector_enumerates_and_convicts_arithmetic(self, tmp_path: Path) -> None:
        backend = tmp_path / "backend" / "tests" / "generated"
        backend.mkdir(parents=True)
        (backend / "junit.xml").write_text(_JUNIT_OK, encoding="utf-8")
        collector = TestResultCollector(workspace_root=tmp_path)
        evidence = collector.collect()
        assert evidence.passed == 1
        assert evidence.failed == 1
        assert evidence.error == 1
        assert evidence.skipped == 1
        # 4-way identity: every testcase enumerated into exactly one bucket
        assert (
            evidence.passed + evidence.failed + evidence.error + evidence.skipped == 4
        )
