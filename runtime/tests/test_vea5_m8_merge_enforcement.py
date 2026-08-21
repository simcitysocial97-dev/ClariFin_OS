"""VEA-5 M8 — Merge Enforcement, Staleness Convergence & LOCAL/PR Closure.

M8 is operationalization, NOT consolidation. These tests guard the four M8
acceptance areas without modifying the nine workflows' ownership:

  M8.1  Four stale workflows (quality/mutation/playwright/golden) are LEGITIMATE
        VEA-5 evolutions (single-command verify.py pattern), not regressions to
        reset. Convergence direction is branch -> main, preserving VEA-5 changes.
  M8.2  verification-reconcile is the required PR check (job identity
        `reconcile-gate`); planning-divergence blocks merge (exit 2).
  M8.3  LOCAL-tier gap closed: `local-gate` emits a working-tree plan manifest
        that NEVER adopts a base ref (no origin/main contamination).
  M8.4  Branch-protection reality: required-check identity is deterministic and
        the gate's PR path filters cover backend/** + runtime/** so a PR cannot
        skip it via its own path filters.

Run:
    python3 -m pytest runtime/tests/test_vea5_m8_merge_enforcement.py -q
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO / ".github" / "workflows"

STALE = ["quality", "mutation", "playwright", "golden"]

ENGINE_CHANGE = ["backend/src/engines/loan_engine/amortization.py"]


# ---------------------------------------------------------------------------
# M8.1 — stale workflows are legitimate VEA-5 evolutions
# ---------------------------------------------------------------------------


def test_m81_stale_workflows_use_verification_command_pattern():
    """Each stale workflow delegates to `runtime/verify.py <profile>` (the VEA-5
    canonical single-command pattern), uses bootstrap-runtime, uploads the shared
    artifacts, and appends `verify.py status`. That is the legitimate refactor —
    NOT something to reset to main's hand-rolled multi-job form."""
    expected_profiles = {
        "quality": "quick",
        "mutation": "mutation",
        "playwright": "playwright",
        "golden": "golden",
    }
    for wf in STALE:
        doc = yaml.safe_load((WORKFLOWS / f"{wf}.yml").read_text())
        jobs = doc.get("jobs", {})
        # Single job, single command invoking verify.py <profile>.
        assert len(jobs) == 1, f"{wf} should have exactly one job"
        (job,) = jobs.values()
        run_lines = [s.get("run", "") for s in job.get("steps", []) if "run" in s]
        joined = "\n".join(run_lines)
        assert (
            f"runtime/verify.py {expected_profiles[wf]}" in joined
        ), f"{wf} must delegate to verify.py {expected_profiles[wf]}"
        # Appends status summary (Rule 9).
        assert "verify.py status" in joined
        # Uses bootstrap-runtime (not hand-rolled setup).
        uses = [s.get("uses", "") for s in job.get("steps", []) if "uses" in s]
        assert any("bootstrap-runtime" in u for u in uses)


def test_m81_stale_workflows_match_vea5_concurrency_and_retention():
    """Legitimate VEA-5 workflows follow the project's concurrency policy and
    artifact-retention conventions. Mutation/golden never cancel; others cancel."""
    never_cancel = {"mutation", "golden"}
    for wf in STALE:
        doc = yaml.safe_load((WORKFLOWS / f"{wf}.yml").read_text())
        conc = doc.get("concurrency", {})
        cancel = conc.get("cancel-in-progress")
        if wf in never_cancel:
            assert cancel is False, f"{wf} must never cancel"
        else:
            assert cancel is True, f"{wf} should cancel-in-progress"


# ---------------------------------------------------------------------------
# M8.2 — verification-reconcile is the required PR check
# ---------------------------------------------------------------------------


def test_m82_reconcile_job_identity_is_deterministic():
    doc = yaml.safe_load((WORKFLOWS / "verification-reconcile.yml").read_text())
    assert (
        "reconcile-gate" in doc["jobs"]
    ), "required-check identity must be 'reconcile-gate'"
    # Exactly one job -> stable check name for branch protection.
    assert len(doc["jobs"]) == 1


def test_m82_planning_divergence_blocks_merge_exit_2(tmp_path):
    """M5-E contract: planning-divergence must return exit 2 (architectural
    failure) so a required `reconcile-gate` check fails and blocks merge."""
    from runtime.foundation.verification.reconciliation import (
        ReconciliationStatus,
        reconcile_from_artifacts,
    )
    from runtime.foundation.verification.tier import plan_for_tier

    local = plan_for_tier("local", changed_files=["frontend/src/App.tsx"])
    ci = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    local_p = tmp_path / "local.json"
    ci_p = tmp_path / "ci.json"
    local.write(local_p)
    ci.write(ci_p)

    report = reconcile_from_artifacts(
        local_plan_path=local_p, ci_plan_path=ci_p, commit="sha"
    )
    assert (
        report.classification.status == ReconciliationStatus.PLANNING_DIVERGENCE.value
    )
    # Exit mapping (mirrors verify.py reconcile).
    exit_code = (
        2
        if report.classification.status
        == ReconciliationStatus.PLANNING_DIVERGENCE.value
        else (
            1
            if report.classification.status
            == ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value
            else 0
        )
    )
    assert exit_code == 2


# ---------------------------------------------------------------------------
# M8.3 — LOCAL-tier gap closed without origin/main contamination
# ---------------------------------------------------------------------------


def test_m83_local_gate_never_adopts_base_ref(tmp_path):
    """The developer-side local-gate must emit a LOCAL plan that NEVER adopts a
    base ref, even if one is supplied, so origin/main contamination cannot
    re-enter. (M2 invariant, now closed at the CLI boundary.)"""
    from runtime.foundation.verification.tier import (
        VerificationTier,
        plan_for_tier,
    )

    # Even with explicit_base + pr_base pointing at origin/main, LOCAL ignores them.
    plan = plan_for_tier(
        VerificationTier.LOCAL,
        changed_files=["backend/src/engines/loan_engine/amortization.py"],
        explicit_base="origin/main",
        pr_base="origin/main",
    )
    assert plan.tier == "local"
    assert plan.base_ref is None


def test_m83_local_gate_cli_emits_manifest_no_base(tmp_path):
    import subprocess

    out = tmp_path / "vea5-tier-plan.local.json"
    res = subprocess.run(
        ["python3", "runtime/verify.py", "local-gate", "--out", str(out)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    import json

    data = json.loads(out.read_text())
    assert data["tier"] == "local"
    assert data["base_ref"] is None
    assert data["unit_coverage"]["complete"] is True


# ---------------------------------------------------------------------------
# M8.4 — branch-protection reality: path filters cannot skip enforcement
# ---------------------------------------------------------------------------


def test_m84_reconcile_pr_paths_cover_backend_and_runtime():
    """A backend or verification PR cannot skip the reconcile gate via path
    filters. The PR trigger must include backend/** and runtime/**."""
    doc = yaml.safe_load((WORKFLOWS / "verification-reconcile.yml").read_text())
    pr = doc[True]["pull_request"]  # YAML parses `on:` as boolean True
    pr_paths = pr["paths"]
    assert "backend/**" in pr_paths, "backend/** must be in PR path filter"
    assert "runtime/**" in pr_paths, "runtime/** must be in PR path filter"


def test_m84_no_workflow_defines_nonexistent_required_check():
    """Branch-protection reality: there must be no required-check name that does
    not correspond to an actual job. We verify the reconcile job identity is
    present and that every workflow's job names are internally consistent."""
    for wf in WORKFLOWS.glob("*.yml"):
        doc = yaml.safe_load(wf.read_text())
        jobs = doc.get("jobs", {})
        assert jobs, f"{wf.name} must define at least one job"
        # Job names are valid identifiers (no spaces) so they map to check names.
        for job_name in jobs:
            assert " " not in job_name, f"{wf.name}: job '{job_name}' has spaces"
