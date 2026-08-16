"""VEA-5 M8R — CLI integration tests for the reconciliation gate (D-02).

These tests exercise the ACTUAL production CLI entry point
``runtime/verify.py reconcile`` via ``subprocess`` — using the same argument
shape as ``.github/workflows/verification-reconcile.yml`` — and prove the M5-E
exit contract through the real executable path. They do NOT call the internal
``reconcile``/``reconcile_from_artifacts`` helper functions, so a defect like
D-01 (CI-only reconcile always returning ``environment-divergence``) cannot hide
behind a passing unit test of an internal helper.

Run:
    python3 -m pytest runtime/tests/test_vea5_m8r_cli_reconcile.py -q
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PY = "python3"
VERIFY = str(REPO / "runtime" / "verify.py")

ENGINE_CHANGE = ["backend/src/engines/loan_engine/amortization.py"]
FRONTEND_CHANGE = ["frontend/src/App.tsx"]


def _verify(*args: str, cwd: Path = REPO) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, VERIFY, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _make_plan(path: Path, tier: str, changed: list[str], *, base: str | None = None) -> None:
    """Emit a plan manifest via the real CLI (the CI workflow's plan step)."""
    args = [PY, VERIFY, "plan", "--tier", tier, "--no-write", "--head", "sha"] + [
        "--changed"
    ] + changed
    if base:
        args += ["--base", base]
    r = subprocess.run(args, cwd=str(REPO), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    Path(path).write_text(r.stdout)


def _make_evidence(
    plan_path: Path, out_path: Path, status: str, exit_code: int
) -> None:
    """Emit an execution-evidence artifact via the real CLI (M5-C / M6-A)."""
    r = subprocess.run(
        [
            PY, VERIFY, "exec-evidence",
            "--plan", str(plan_path),
            "--profile", "runtime",
            "--status", status,
            "--exit", str(exit_code),
            "--duration", "0",
            "--commit", "sha",
            "--out", str(out_path),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr


def _run_reconcile(*args: str) -> subprocess.CompletedProcess:
    return _verify("reconcile", *args)


def _classification(res: subprocess.CompletedProcess) -> tuple[str, str]:
    try:
        d = json.loads(res.stdout)
        return d["classification"]["status"], d["classification"]["reason"]
    except Exception:
        return "UNPARSEABLE", (res.stdout.strip() or res.stderr.strip())


def _make_evidence_literal(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")

# ---------------------------------------------------------------------------
# Option A — CI-only gate (the verification-reconcile.yml argument shape:
#   reconcile --plan X --evidence Y --report Z --commit S ; no --local)
# ---------------------------------------------------------------------------


def test_reconcile_ci_valid_pass_is_same_plan_exit_0(tmp_path: Path) -> None:
    """A valid, fully-passing CI execution must be same-plan / exit 0.

    This is the exact D-01 regression: previously this invocation produced
    environment-divergence / exit 1 merely because --local was omitted.
    """
    plan = tmp_path / "vea5-tier-plan.pr.json"
    evidence = tmp_path / "vea5-execution.pr.json"
    report = tmp_path / "vea5-reconciliation.pr.json"
    _make_plan(plan, "pr", ENGINE_CHANGE, base="main")
    _make_evidence(plan, evidence, "pass", 0)

    res = _run_reconcile(
        "--plan", str(plan), "--evidence", str(evidence),
        "--report", str(report), "--commit", "sha",
    )
    status, reason = _classification(res)
    assert res.returncode == 0, f"expected exit 0, got {res.returncode}: {res.stderr}"
    assert status == "same-plan", f"expected same-plan, got {status}: {reason}"
    assert report.exists()


def test_reconcile_ci_missing_evidence_is_explicit_no_evidence_nonzero(tmp_path: Path) -> None:
    """A selected unit with no evidence must be explicit, never a silent PASS."""
    plan = tmp_path / "plan.json"
    evidence = tmp_path / "empty-evidence.json"
    _make_plan(plan, "pr", ENGINE_CHANGE, base="main")
    # No units at all -> every selected unit is missing evidence; empty
    # fingerprint means the consistency check is defensively skipped.
    _make_evidence_literal(
        evidence,
        {"schema": "vea5-execution-evidence/v2", "tier": "pr",
         "plan_fingerprint": "", "commit": "sha", "units": []},
    )

    res = _run_reconcile("--plan", str(plan), "--evidence", str(evidence), "--commit", "sha")
    status, reason = _classification(res)
    assert res.returncode != 0, "missing evidence must not PASS"
    assert ("no evidence" in reason.lower()) or ("no-evidence" in reason.lower())
    assert status == "environment-divergence"


def test_reconcile_ci_failed_execution_is_preserved_nonzero(tmp_path: Path) -> None:
    """A genuine execution failure must be preserved and never appear successful."""
    plan = tmp_path / "plan.json"
    evidence = tmp_path / "evidence.json"
    _make_plan(plan, "pr", ENGINE_CHANGE, base="main")
    _make_evidence(plan, evidence, "fail", 1)

    res = _run_reconcile("--plan", str(plan), "--evidence", str(evidence), "--commit", "sha")
    status, reason = _classification(res)
    assert res.returncode != 0, "failed execution must not PASS"
    assert "failure" in reason.lower()
    assert status == "environment-divergence"


def test_reconcile_ci_malformed_evidence_is_rejected_nonzero(tmp_path: Path) -> None:
    """Malformed evidence must be rejected (non-zero), never a silent PASS."""
    plan = tmp_path / "plan.json"
    evidence = tmp_path / "evidence.json"
    _make_plan(plan, "pr", ENGINE_CHANGE, base="main")
    evidence.write_text("{ not valid json", encoding="utf-8")

    res = _run_reconcile("--plan", str(plan), "--evidence", str(evidence), "--commit", "sha")
    assert res.returncode != 0, "malformed evidence must not PASS"
    status, reason = _classification(res)
    assert "malformed" in reason.lower() or "unreadable" in reason.lower()


def test_reconcile_ci_wrong_fingerprint_is_planning_divergence_exit_2(tmp_path: Path) -> None:
    """Evidence recorded for a different plan must be a structural failure."""
    plan_a = tmp_path / "plan-a.json"
    plan_b = tmp_path / "plan-b.json"
    evidence_a = tmp_path / "evidence-a.json"
    _make_plan(plan_a, "pr", ENGINE_CHANGE, base="main")
    _make_plan(plan_b, "pr", FRONTEND_CHANGE, base="main")
    _make_evidence(plan_a, evidence_a, "pass", 0)

    # Supply plan_b's path but evidence recorded for plan_a (different fp).
    res = _run_reconcile("--plan", str(plan_b), "--evidence", str(evidence_a), "--commit", "sha")
    status, _ = _classification(res)
    assert res.returncode == 2, f"expected exit 2, got {res.returncode}"
    assert status == "planning-divergence"


# ---------------------------------------------------------------------------
# Option B — true LOCAL-vs-CI reconciliation
# ---------------------------------------------------------------------------


def test_reconcile_expected_tier_difference_exit_0(tmp_path: Path) -> None:
    """LOCAL vs CI with only tier-eligible units differing --> exit 0."""
    local_plan = tmp_path / "local.json"
    ci_plan = tmp_path / "ci.json"
    # Same change set; LOCAL tier omits mutation-run, PR tier includes it.
    _make_plan(local_plan, "local", ENGINE_CHANGE)
    _make_plan(ci_plan, "pr", ENGINE_CHANGE, base="main")

    res = _run_reconcile("--local", str(local_plan), "--plan", str(ci_plan), "--commit", "sha")
    status, _ = _classification(res)
    assert res.returncode == 0, f"expected exit 0, got {res.returncode}"
    assert status == "expected-tier-difference"


def test_reconcile_planning_divergence_exit_2(tmp_path: Path) -> None:
    """Incompatible plans (different change sets) --> planning-divergence / exit 2."""
    local_plan = tmp_path / "local.json"
    ci_plan = tmp_path / "ci.json"
    _make_plan(local_plan, "pr", FRONTEND_CHANGE, base="main")
    _make_plan(ci_plan, "pr", ENGINE_CHANGE, base="main")

    res = _run_reconcile("--local", str(local_plan), "--plan", str(ci_plan), "--commit", "sha")
    status, _ = _classification(res)
    assert res.returncode == 2, f"expected exit 2, got {res.returncode}"
    assert status == "planning-divergence"


def test_reconcile_environment_divergence_exit_1(tmp_path: Path) -> None:
    """Same plan, differing LOCAL/CI evidence --> environment-divergence / exit 1."""
    plan_path = tmp_path / "plan.json"
    local_ev = tmp_path / "local-ev.json"
    ci_ev = tmp_path / "ci-ev.json"
    _make_plan(plan_path, "pr", ENGINE_CHANGE, base="main")
    _make_evidence(plan_path, local_ev, "pass", 0)
    _make_evidence(plan_path, ci_ev, "fail", 1)

    res = _run_reconcile(
        "--local", str(plan_path), "--plan", str(plan_path),
        "--local-evidence", str(local_ev), "--evidence", str(ci_ev),
        "--commit", "sha",
    )
    status, _ = _classification(res)
    assert res.returncode == 1, f"expected exit 1, got {res.returncode}"
    assert status == "environment-divergence"

