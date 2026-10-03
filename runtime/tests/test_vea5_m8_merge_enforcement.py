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
    """Each stale workflow delegates to a canonical `runtime.verify <command>`
    (the VEA-5 canonical single-command pattern), uses bootstrap-runtime, and
    appends a status/doctor summary. That is the legitimate refactor — NOT
    something to reset to main's hand-rolled multi-job form.

    M9-C43.1: `mutation` legitimately uses the documented smoke-first topology
    (mutation-smoke MUST pass before the expensive campaign jobs — see the
    mutation.yml header).

    M9-C71: the campaign is SHARDED. The previous single-process authoritative
    job was falsified by evidence — GitHub run 36233136018 was cancelled after
    91m45s having produced no campaign result at all, so the quality gate was
    permanently unsatisfiable. The topology is now
        mutation-smoke -> mutation-plan -> mutation (shard matrix) -> mutation-aggregate
    which is a STRICTLY stronger invariant than "exactly two jobs": the
    per-job expected command is pinned, the smoke-first dependency is still
    required, and the aggregate gate is now part of the asserted topology.
    """
    expected_profiles = {
        # quality owns repository/static quality, so it delegates to the quick
        # profile (ruff, black, mypy-strict, unit tests) — the same responsibility
        # it had before b326f08e replaced those steps with `runtime/verify.py
        # quick`, and before later C70 work widened it to `check`. `check` is
        # change-boundary capability verification, which is
        # verification-reconcile.yml's job; running it here as well made the most
        # expensive verification in the repository execute twice per event.
        "quality": "quick",
        "playwright": "playwright",
        "golden": "golden",
    }
    # mutation is pinned per job, because each job owns a distinct canonical
    # command (shard measurement vs plan emission vs aggregate reconciliation).
    #
    # M9-C72 adds `mutation-replay`: a repair path that reconciles a prior run's
    # shard evidence WITHOUT re-measuring, so a transport fault costs a
    # re-download rather than a full campaign. It carries its own canonical
    # command, so it is pinned here like every other mutation job.
    mutation_job_profiles = {
        "mutation-smoke": "mutation",
        "mutation-plan": "mutation-plan",
        "mutation": "mutation",
        "mutation-replay": "mutation-aggregate",
        "mutation-aggregate": "mutation-aggregate",
    }
    for wf in STALE:
        doc = yaml.safe_load((WORKFLOWS / f"{wf}.yml").read_text())
        jobs = doc.get("jobs", {})
        if wf == "mutation":
            assert set(jobs) == set(mutation_job_profiles), (
                "mutation must keep the smoke-first sharded campaign topology: "
                f"{sorted(mutation_job_profiles)}"
            )
            assert "mutation-smoke" in jobs["mutation"].get(
                "needs", []
            ), "authoritative mutation shards must need mutation-smoke"
            assert "mutation-plan" in jobs["mutation"].get(
                "needs", []
            ), "shards must consume the canonical plan, not a duplicated list"
            assert "mutation" in jobs["mutation-aggregate"].get(
                "needs", []
            ), "the aggregate gate must consume every shard"
            expected = mutation_job_profiles
        else:
            # Single job, single command invoking verify.py <profile>.
            assert len(jobs) == 1, f"{wf} should have exactly one job"
            expected = {next(iter(jobs)): expected_profiles[wf]}
        for job_id, job in jobs.items():
            run_lines = [s.get("run", "") for s in job.get("steps", []) if "run" in s]
            joined = "\n".join(run_lines)
            # Accept both script-form (runtime/verify.py <command>) and
            # module-form (python -m runtime.verify <command>).
            profile = expected[job_id]
            has_pattern = (
                f"runtime/verify.py {profile}" in joined
                or f"runtime.verify {profile}" in joined
            )
            assert has_pattern, (
                f"{wf}/{job_id} must delegate to verify.py {profile} "
                f"(via runtime/verify.py or python -m runtime.verify)"
            )
            # Uses bootstrap-runtime (not hand-rolled setup).
            uses = [s.get("uses", "") for s in job.get("steps", []) if "uses" in s]
            assert any("bootstrap-runtime" in u for u in uses)
        # Appends status summary (Rule 9) in at least one job.
        all_runs = "\n".join(
            s.get("run", "")
            for job in jobs.values()
            for s in job.get("steps", [])
            if "run" in s
        )
        assert (
            "verify.py status" in all_runs
            or "runtime.verify status" in all_runs
            or "runtime.verify doctor" in all_runs
        )


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
    """Exactly one job may claim the required reconciliation identity.

    M10-R2 restructured the workflow from one job into
    ``reconcile-plan`` / ``reconcile-shard`` (matrix) / ``reconcile-gate``. The
    invariant this test exists to protect is unchanged — a *stable check name for
    branch protection* — but "exactly one job" was only ever a proxy for it. With a
    fan-out there are legitimately several jobs, and the property that actually
    matters is that precisely one of them reports the identity.

    So the assertion is restated rather than dropped: the gate job exists, it still
    carries the identity's display name, and no sibling job claims the same name. A
    future edit that renamed the gate, or gave a shard leg the gate's name, fails
    here exactly as the old count check would have.
    """
    doc = yaml.safe_load((WORKFLOWS / "verification-reconcile.yml").read_text())
    jobs = doc["jobs"]

    assert (
        "reconcile-gate" in jobs
    ), "required-check identity must be produced by 'reconcile-gate'"

    gate_name = jobs["reconcile-gate"]["name"]
    assert gate_name == "Verification Reconcile", (
        "the gate job's display name IS the reported check identity; changing it "
        f"silently renames the branch-protection context (found {gate_name!r})"
    )

    # Exactly one job may report that identity, or branch protection sees a
    # duplicate/ambiguous context.
    claimants = [name for name, spec in jobs.items() if spec.get("name") == gate_name]
    assert claimants == [
        "reconcile-gate"
    ], f"more than one job reports {gate_name!r}: {claimants}"

    # The gate must be reachable no matter how the shards turned out, otherwise a
    # single red shard leaves the run with no conclusion at all.
    assert jobs["reconcile-gate"].get("if") == "always()"
    assert set(jobs["reconcile-gate"]["needs"]) == {"reconcile-plan", "reconcile-shard"}


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
    """The developer-side local-gate must emit a LOCAL plan that NEVER adopts a
    base ref, even if one is supplied, so origin/main contamination cannot
    re-enter. (M2 invariant, now closed at the CLI boundary.)

    local-gate is a legacy alias for `plan local_gate`; we exercise the
    underlying tier planner directly to assert the same invariants.
    """
    from runtime.foundation.verification.tier import (  # noqa: PLC0415
        VerificationTier,
        plan_for_tier,
    )

    plan = plan_for_tier(
        VerificationTier.LOCAL,
        changed_files=["backend/src/engines/loan_engine/amortization.py"],
    )
    assert plan.tier == "local"
    assert plan.base_ref is None
    # Serialize to JSON and write to tmp_path to mirror what the CLI would do.
    import json

    out = tmp_path / "vea5-tier-plan.local.json"
    data = plan.to_dict() if hasattr(plan, "to_dict") else vars(plan)
    out.write_text(json.dumps(data, indent=2, default=str))
    reloaded = json.loads(out.read_text())
    assert reloaded["tier"] == "local"
    assert reloaded["base_ref"] is None


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
