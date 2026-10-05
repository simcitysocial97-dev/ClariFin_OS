# runtime/tests/test_m11_r4_playwright_leg_results.py
#
# M11-R4 — the Playwright leg result document must be real evidence.
#
# WHAT WAS WRONG
# --------------
# 1. `playwright_shards.read_leg_results` delegated to `read_shard_results`, which
#    globs `shard-*.json`. Playwright legs are named `leg-<leg_id>.json`, so the glob
#    matched nothing and every run reported "no shard-*.json files found". The gate
#    then declared all ten legs absent and returned NOT CERTIFIED whatever the tests
#    had done — a run whose only real failure was one stale baseline still reported
#    `legs_reported: 0`.
#
# 2. `playwright.yml` built the document inline with a `jq -n` whose
#    `passed`/`failed`/`errors`/`duration_seconds` were literals. Every leg reported
#    zero of everything.
#
# 3. Nothing could read real counts anyway: both passes ran
#    `npx playwright test --reporter=list`, and a command-line `--reporter` REPLACES
#    the config's reporter list, so the configured `json` reporter never ran and
#    `frontend/test-results/results.json` was never written.
#
# 4. Even with counts, `verify_legs` requires a fingerprint bracket and treats its
#    absence as *not certified*. The inline document had none, so it could never have
#    been certified.

import json

import pytest

from runtime.foundation.verification.playwright_shards import (
    expected_leg_ids,
    parse_playwright_results,
    read_leg_results,
    verify_legs,
)
from runtime.foundation.verification.runtime_shards import LEG_RESULT_SCHEMAS


def _leg_doc(leg_id: str, **overrides) -> dict:
    doc = {
        "schema": next(iter(LEG_RESULT_SCHEMAS)),
        "shard_id": leg_id,
        "status": "passed",
        "exit_code": 0,
        "duration_seconds": 12.5,
        "file_count": 3,
        "passed": 41,
        "failed": 0,
        "errors": 0,
        "decision": "certified",
        "decision_reason": "",
        "fingerprint_before": {"fingerprint": "abc123"},
        "fingerprint_after": {"fingerprint": "abc123"},
        "fingerprint_stable": True,
    }
    doc.update(overrides)
    return doc


def _write(directory, leg_id: str, **overrides) -> None:
    (directory / f"leg-{leg_id}.json").write_text(
        json.dumps(_leg_doc(leg_id, **overrides)), encoding="utf-8"
    )


class TestLegReaderFindsLegs:
    def test_leg_documents_are_read(self, tmp_path):
        """The regression: the glob was `shard-*.json`, so this read nothing."""
        _write(tmp_path, "chromium-visual")
        _write(tmp_path, "chromium-functional-0")

        results, absent, malformed, rejected = read_leg_results(tmp_path)

        assert absent == []
        assert malformed == []
        assert rejected == []
        assert sorted(r.shard_id for r in results) == [
            "chromium-functional-0",
            "chromium-visual",
        ]

    def test_real_ci_document_now_parses(self, tmp_path):
        """The exact document CI published for the red chromium-visual leg.

        Fetched from `playwright-result-chromium-visual` in run 37261663442. Before
        the fix the gate could not see this file at all; after the transport fix it is
        read, and it must be read as a genuine failure — not as a pass, and not as a
        malformed producer fault.
        """
        (tmp_path / "leg-chromium-visual.json").write_text(
            json.dumps(
                {
                    "shard_id": "chromium-visual",
                    "status": "failed",
                    "exit_code": 1,
                    "duration_seconds": 0,
                    "file_count": 0,
                    "passed": 0,
                    "failed": 0,
                    "errors": 0,
                }
            ),
            encoding="utf-8",
        )
        results, absent, malformed, rejected = read_leg_results(tmp_path)

        assert absent == []
        assert malformed == []
        assert rejected == []
        assert len(results) == 1
        assert results[0].status == "failed"
        assert not results[0].ok
        # No bracket, so the gate must refuse to certify it even setting aside the
        # failure. That is the pre-existing fail-closed rule, not a new one.
        assert not results[0].fingerprint_stable

    def test_no_documents_is_a_transport_fault_not_a_pass(self, tmp_path):
        results, absent, malformed, rejected = read_leg_results(tmp_path)
        assert results == []
        assert absent, "an empty directory must be reported as a transport fault"
        assert "leg-*.json" in absent[0]

    def test_shard_named_documents_are_not_silently_ignored(self, tmp_path):
        """A producer that renames its output must be visible, not invisible."""
        (tmp_path / "shard-0.json").write_text(
            json.dumps(_leg_doc("shard-0")), encoding="utf-8"
        )
        results, absent, _, _ = read_leg_results(tmp_path)
        assert results == []
        assert absent


class TestGateSeesRealCounts:
    def test_certifies_a_full_green_fanout(self, tmp_path):
        for leg_id in expected_leg_ids():
            _write(tmp_path, leg_id)

        results, absent, malformed, rejected = read_leg_results(tmp_path)
        problems = verify_legs(expected_leg_ids(), results)

        assert absent == [] and malformed == [] and rejected == []
        assert problems == []
        assert sum(r.passed for r in results) == 10 * 41

    def test_a_leg_without_a_bracket_cannot_certify(self, tmp_path):
        for leg_id in expected_leg_ids():
            _write(tmp_path, leg_id)
        (tmp_path / "leg-chromium-visual.json").write_text(
            json.dumps(
                {
                    "shard_id": "chromium-visual",
                    "status": "passed",
                    "exit_code": 0,
                }
            ),
            encoding="utf-8",
        )
        results, _, _, _ = read_leg_results(tmp_path)
        problems = verify_legs(expected_leg_ids(), results)

        assert any("no fingerprint bracket" in p for p in problems)


class TestCountParsing:
    def _report(self, tmp_path, stats) -> "object":
        path = tmp_path / "results.json"
        path.write_text(json.dumps({"stats": stats}), encoding="utf-8")
        return path

    def test_passing_run(self, tmp_path):
        counts = parse_playwright_results(
            self._report(
                tmp_path,
                {
                    "startTime": "2026-10-05T05:03:06.035Z",
                    "duration": 15089.845,
                    "expected": 18,
                    "skipped": 2,
                    "unexpected": 0,
                    "flaky": 0,
                },
            )
        )
        assert counts == {
            "passed": 18,
            "failed": 0,
            "skipped": 2,
            "flaky": 0,
            "duration_seconds": 15.09,
        }

    def test_failing_run_is_not_read_as_zero(self, tmp_path):
        """The defect: the workflow reported `passed: 0, failed: 0` for a leg that
        had 11 failures. The runner's own counts must survive."""
        counts = parse_playwright_results(
            self._report(
                tmp_path,
                {
                    "duration": 72000,
                    "expected": 10,
                    "skipped": 0,
                    "unexpected": 11,
                    "flaky": 1,
                },
            )
        )
        assert counts["failed"] == 11
        assert counts["passed"] == 11  # 10 expected + 1 flaky, which passed on retry
        assert counts["flaky"] == 1
        assert counts["duration_seconds"] == 72.0

    def test_missing_report_is_none_not_zero(self, tmp_path):
        """`None` (the runner reported nothing) must be distinguishable from zeros."""
        assert parse_playwright_results(tmp_path / "absent.json") is None

    @pytest.mark.parametrize(
        "payload",
        [
            "not json at all",
            json.dumps([1, 2, 3]),
            json.dumps({"no": "stats"}),
            json.dumps({"stats": "not an object"}),
        ],
    )
    def test_unusable_report_is_none(self, tmp_path, payload):
        path = tmp_path / "results.json"
        path.write_text(payload, encoding="utf-8")
        assert parse_playwright_results(path) is None


class TestScriptDoesNotSuppressTheJsonReporter:
    """`npx playwright test --reporter=list` REPLACES the configured reporters, so
    the JSON report the counts come from was never produced. The script must not pass
    a command-line `--reporter`."""

    def test_no_command_line_reporter_override(self):
        script = (
            __import__("pathlib")
            .Path(".github/scripts/run_playwright_tests.sh")
            .read_text(encoding="utf-8")
        )
        # Comments legitimately discuss `--reporter`; only the commands matter.
        commands = [
            line
            for line in script.splitlines()
            if line.strip().startswith("npx playwright test")
            or line.strip().startswith("--grep")
            or line.strip().startswith("--reporter")
        ]
        assert commands, "expected to find the playwright invocations"
        assert not any("--reporter" in line for line in commands), (
            "a command-line --reporter replaces the config's json reporter, which is "
            "the only source of real pass/fail/skip counts"
        )
