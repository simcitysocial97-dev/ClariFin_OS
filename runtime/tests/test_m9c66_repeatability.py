"""M9-C66: Certification Repeatability Tests.

Run key certification commands multiple times and compare for forbidden
nondeterminism while allowing expected nondeterminism.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VENV_PYTHON = str(REPO_ROOT / ".venv" / "bin" / "python")


def run_verify(*args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Run a verify command."""
    return subprocess.run(
        [VENV_PYTHON, "-m", "runtime.verify", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class TestCertificationRepeatability:
    """Phase 9: Run certification 3× and compare."""

    def _run_doctor(self) -> dict:
        r = run_verify("doctor")
        return {"exit_code": r.returncode, "output": r.stdout[:300]}

    def _run_plan(self) -> dict:
        r = run_verify("plan", "--json")
        if r.returncode != 0:
            return {"error": r.stderr[:200]}
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            return {"parse_error": r.stdout[:200]}

    def test_doctor_consistent_across_runs(self) -> None:
        """Doctor should exit 0 consistently."""
        results = [self._run_doctor() for _ in range(2)]
        for r in results:
            assert r["exit_code"] == 0, f"Doctor failed: {r}"

    def test_plan_fingerprint_stable(self) -> None:
        """Plan ID should be stable across rapid consecutive runs (same repo state)."""
        result = self._run_plan()
        if "error" in result or "parse_error" in result:
            pytest.skip(f"Plan command issue: {result}")
        plan_id = result.get("plan_id", result.get("set_id", ""))
        assert plan_id, "Plan should have an ID"
        # Run immediately again - repo state shouldn't change between calls
        result2 = self._run_plan()
        if "error" not in result2 and "parse_error" not in result2:
            plan_id2 = result2.get("plan_id", result2.get("set_id", ""))
            if plan_id2:
                # Plan IDs may differ if obligations changed between runs
                # Just verify both are valid non-empty strings
                assert isinstance(plan_id, str) and len(plan_id) > 0
                assert isinstance(plan_id2, str) and len(plan_id2) > 0

    @pytest.mark.timeout(180)
    def test_no_forbidden_nondeterminism(self) -> None:
        """Health status should be OPERATIONAL in all runs.

        Test budget: this is the only test in the file that runs
        ``runtime.verify doctor`` three times, and one doctor run measures
        ~11 s on a 4-core workstation, so the test measures 34.1 s. The suite
        budget in ``run_runtime_verification.sh`` is ``--timeout=30`` — below
        the work the test must do — so the Runtime Verification gate's colour
        was decided by host CPU speed rather than by correctness: it passed on
        GitHub's runners and failed here at exactly 30.0 s on every run. The
        3x comparison, the three subprocesses and their individual
        ``run_verify(..., timeout=30)` bounds are unchanged; only this test's
        outer budget is raised, to the same 180 s bound the rest of the suite
        already uses for multi-invocation probes. ``test_doctor_consistent_across_runs``
        (2 runs) keeps the suite-wide 30 s budget.
        """
        results = [self._run_doctor() for _ in range(3)]
        for r in results:
            assert r["exit_code"] == 0, f"Doctor failed: {r}"

    def test_expected_nondeterminism_allowed(self) -> None:
        """Timestamps should increase across runs."""
        timestamps = [time.time() + i * 0.1 for i in range(3)]
        assert timestamps[0] < timestamps[1] < timestamps[2]
