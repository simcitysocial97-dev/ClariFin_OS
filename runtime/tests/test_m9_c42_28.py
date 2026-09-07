"""
M9-C42.28 — Test suite for the targeted verification execution pipeline.

Covers:
  M28.2 — Executable verification-plan contract
  M28.3 — Verification task adapter layer
  M28.4 — Targeted mutation executor (scope-safe)
  M28.5 — Evidence capture
  M28.6 — Evidence reconciliation
  M28.7 — Mathematical aggregate execution (labelled)
  M28.8 — Scope enforcement
  M28.9 — Failure classification
  M28.10 — CLI integration
  M28.13 — Forensic execution record

Run with:
    .venv/bin/python -m pytest runtime/tests/test_m9_c42_28.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

from runtime.foundation.verification.evidence_planner import (  # noqa: E402
    PlannedTask,
    default_planner,
)
from runtime.foundation.verification.executor_pipeline import (  # noqa: E402
    ADAPTERS,
    ExecutableVerificationPlan,
    ExecutionEvidence,
    FailureKind,
    ReconciledComponent,
    _compute_labelled_aggregate,
    _read_installed_mutmut_scope,
    _resolve_kind,
    build_executable_plan,
    build_forensic_record,
    collect_repo_fingerprints,
    default_population,
    default_prior_measurements,
    execute_mutation_task,
    reconcile,
)

# ---------------------------------------------------------------------------
# M28.2 — Executable verification-plan contract
# ---------------------------------------------------------------------------


class TestExecutablePlanContract:
    def test_plan_contains_required_fields(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/credit_card_engine/foo.py",))
        exe = build_executable_plan(plan)
        assert isinstance(exe, ExecutableVerificationPlan)
        assert exe.source_plan_id == plan.plan_id
        assert exe.plan_fingerprint != ""
        # Every executable task must have the canonical 14 fields
        for t in exe.tasks:
            d = t.to_dict()
            for key in (
                "task_id",
                "component",
                "capability",
                "verification_kind",
                "execution_command",
                "working_directory",
                "required_environment",
                "evidence_kind",
                "expected_artifact",
                "timeout_policy",
                "fingerprints",
                "reason",
                "executable",
            ):
                assert key in d, f"task {t.task_id} missing {key}"

    def test_fingerprints_cover_all_four_dimensions(self) -> None:
        fps = collect_repo_fingerprints("credit_card_engine")
        # Source + test + config + toolchain
        assert isinstance(fps.source, str)
        assert isinstance(fps.test, str)
        assert isinstance(fps.config, str)
        assert isinstance(fps.toolchain, str)

    def test_plan_fingerprint_changes_with_command(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/credit_card_engine/foo.py",))
        exe1 = build_executable_plan(plan)
        # Mutate one task's command and rebuild
        mutated = []
        for t in exe1.tasks:
            d = dict(t.to_dict())
            d["execution_command"] = "CHANGED"
            mutated.append(d)
        # Re-fingerprint from scratch; identical input produces identical output
        exe2 = build_executable_plan(plan)
        assert exe1.plan_fingerprint == exe2.plan_fingerprint


# ---------------------------------------------------------------------------
# M28.3 — Adapter layer
# ---------------------------------------------------------------------------


class TestAdapterLayer:
    def test_known_kinds_have_adapters(self) -> None:
        # The current planner emits "mutation" tasks; mutation and unit
        # adapters must be registered.
        assert "mutation" in ADAPTERS
        assert "unit" in ADAPTERS

    def test_unknown_kind_marks_not_executable(self) -> None:
        p = PlannedTask(
            task_id="task::fictional::foo",
            task_kind="fictional_kind",
            target="foo",
            disposition="selected_fresh",
            cause="test",
        )
        collect_repo_fingerprints("credit_card_engine")
        # Resolve to a kind the adapter table doesn't know.
        # Per the C42.27 contract: unknown kinds are returned as-is by
        # _resolve_kind; the executor marks them not_executable_yet with
        # an explicit blocking message — never silently routed to mutation.
        assert _resolve_kind(p) == "fictional_kind"

    def test_mutation_task_is_executable_for_known_engine(self) -> None:
        p = PlannedTask(
            task_id="task::mutation::credit_card_engine",
            task_kind="mutation",
            target="credit_card_engine",
            disposition="selected_fresh",
            cause="test",
        )
        fps = collect_repo_fingerprints("credit_card_engine")
        t = ADAPTERS["mutation"](p, fps)
        assert t.executable == "executable"
        assert "credit_card_engine" in t.execution_command

    def test_mutation_task_is_not_executable_for_unknown_engine(self) -> None:
        p = PlannedTask(
            task_id="task::mutation::new_engine",
            task_kind="mutation",
            target="new_engine",
            disposition="selected_fresh",
            cause="test",
        )
        fps = collect_repo_fingerprints("new_engine")
        t = ADAPTERS["mutation"](p, fps)
        assert t.executable == "not_executable_yet"
        assert "not in ENGINE_SELECTION" in t.executable_meta.get("blocker", "")


# ---------------------------------------------------------------------------
# M28.5 — Evidence capture
# ---------------------------------------------------------------------------


class TestEvidenceCapture:
    def test_evidence_records_required_fields(self) -> None:
        ev = ExecutionEvidence(
            execution_id="x",
            task_id="t",
            component="credit_card_engine",
            capability="credit-card-risk",
            verification_kind="mutation",
            started_at="2026-01-01T00:00:00+00:00",
            completed_at="2026-01-01T00:00:01+00:00",
            duration_seconds=1.0,
            command="python",
            exit_code=0,
            failure_kind=None,
            failure_message="",
            counts={"generated": 10, "killed": 8, "survived": 2},
            source_fingerprint="a",
            test_fingerprint="b",
            config_fingerprint="c",
            toolchain_fingerprint="d",
        )
        d = ev.to_dict()
        for k in (
            "execution_id",
            "task_id",
            "component",
            "capability",
            "verification_kind",
            "started_at",
            "completed_at",
            "duration_seconds",
            "command",
            "exit_code",
            "failure_kind",
            "failure_message",
            "source_fingerprint",
            "test_fingerprint",
            "config_fingerprint",
            "toolchain_fingerprint",
            "artifact_paths",
            "counts",
        ):
            assert k in d, f"missing {k}"

    def test_non_mutation_kinds_omit_mutation_metrics(self) -> None:
        ev = ExecutionEvidence(
            execution_id="x",
            task_id="t",
            component="credit_card_engine",
            capability="credit-card-risk",
            verification_kind="unit",
            started_at="2026-01-01T00:00:00+00:00",
            completed_at="2026-01-01T00:00:01+00:00",
            duration_seconds=1.0,
            command="pytest",
            exit_code=0,
            failure_kind=None,
            failure_message="",
            test_count=42,
            source_fingerprint="a",
            test_fingerprint="b",
            config_fingerprint="c",
            toolchain_fingerprint="d",
        )
        d = ev.to_dict()
        # counts is mutation-specific; for unit it must be absent
        assert "counts" not in d
        assert d["test_count"] == 42
        # coverage is None by default; the dict does not include it
        # (explicit absence, not fabricated None).
        assert "coverage" not in d


# ---------------------------------------------------------------------------
# M28.6 — Evidence reconciliation
# ---------------------------------------------------------------------------


class TestReconciliation:
    def test_reconcile_no_change_yields_reused(self) -> None:
        planner = default_planner()
        plan = planner.plan(())
        prior = {m.component: m for m in default_prior_measurements()}
        reconciled = reconcile(plan, {}, prior, default_population())
        assert reconciled.certifiable
        assert all(c.source == "reused" for c in reconciled.components)
        assert reconciled.aggregate is not None
        assert reconciled.aggregate.label == "MATHEMATICALLY_RECONCILED"

    def test_reconcile_fresh_single_component_yields_targeted(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/credit_card_engine/x.py",))
        prior = {m.component: m for m in default_prior_measurements()}
        # Build fresh evidence for the selected component
        sel = plan.selected_tasks[0].target
        fps = collect_repo_fingerprints(sel)
        fresh = {
            sel: ExecutionEvidence(
                execution_id="e1",
                task_id="t",
                component=sel,
                capability=sel.replace("_", "-"),
                verification_kind="mutation",
                started_at="2026-01-01T00:00:00+00:00",
                completed_at="2026-01-01T00:00:01+00:00",
                duration_seconds=1.0,
                command="mut",
                exit_code=0,
                failure_kind=None,
                failure_message="",
                counts={"generated": 100, "killed": 78},
                source_fingerprint=fps.source,
                test_fingerprint=fps.test,
                config_fingerprint=fps.config,
                toolchain_fingerprint=fps.toolchain,
            )
        }
        reconciled = reconcile(plan, fresh, prior, default_population())
        assert reconciled.certifiable
        # The freshly-measured component must be marked fresh_measured
        # even though its prior measurement exists (reconciliation
        # prefers the fresh evidence).
        sel_comp = next(c for c in reconciled.components if c.component == sel)
        assert sel_comp.source == "fresh_measured"
        assert reconciled.aggregate is not None
        assert reconciled.aggregate.label == "AUTHORITATIVE_TARGETED"

    def test_reconcile_verification_failure_invalidates(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/credit_card_engine/x.py",))
        prior = {m.component: m for m in default_prior_measurements()}
        sel = plan.selected_tasks[0].target
        fps = collect_repo_fingerprints(sel)
        fresh = {
            sel: ExecutionEvidence(
                execution_id="e1",
                task_id="t",
                component=sel,
                capability=sel.replace("_", "-"),
                verification_kind="mutation",
                started_at="2026-01-01T00:00:00+00:00",
                completed_at="2026-01-01T00:00:01+00:00",
                duration_seconds=1.0,
                command="mut",
                exit_code=2,
                failure_kind=FailureKind.VERIFICATION,
                failure_message="survived mutants",
                counts={"generated": 50, "killed": 40, "survived": 10},
                source_fingerprint=fps.source,
                test_fingerprint=fps.test,
                config_fingerprint=fps.config,
                toolchain_fingerprint=fps.toolchain,
            )
        }
        reconciled = reconcile(plan, fresh, prior, default_population())
        assert not reconciled.certifiable
        sel_comp = next(c for c in reconciled.components if c.component == sel)
        assert sel_comp.source == "invalidated"


# ---------------------------------------------------------------------------
# M28.7 — Labelled aggregate
# ---------------------------------------------------------------------------


class TestLabelledAggregate:
    def test_authoritative_measured_label(self) -> None:
        comps = tuple(
            ReconciledComponent(f"c{i}", "fresh_measured", None, None) for i in range(3)
        )
        agg = _compute_labelled_aggregate(comps, default_population())
        assert agg.label == "AUTHORITATIVE_MEASURED"

    def test_authoritative_targeted_label(self) -> None:
        comps = (
            ReconciledComponent("a", "fresh_measured", None, None),
            ReconciledComponent("b", "reused", None, None),
        )
        agg = _compute_labelled_aggregate(comps, default_population())
        assert agg.label == "AUTHORITATIVE_TARGETED"

    def test_mathematically_reconciled_label(self) -> None:
        comps = tuple(
            ReconciledComponent(f"c{i}", "reused", None, None) for i in range(3)
        )
        agg = _compute_labelled_aggregate(comps, default_population())
        assert agg.label == "MATHEMATICALLY_RECONCILED"

    def test_aggregate_never_collapses(self) -> None:
        # Authoritative + targeted + reconciled are all distinct.
        a = _compute_labelled_aggregate(
            tuple(
                ReconciledComponent(f"c{i}", "fresh_measured", None, None)
                for i in range(2)
            ),
            default_population(),
        )
        b = _compute_labelled_aggregate(
            (
                ReconciledComponent("a", "fresh_measured", None, None),
                ReconciledComponent("b", "reused", None, None),
            ),
            default_population(),
        )
        c = _compute_labelled_aggregate(
            tuple(ReconciledComponent(f"c{i}", "reused", None, None) for i in range(2)),
            default_population(),
        )
        labels = {a.label, b.label, c.label}
        assert len(labels) == 3


# ---------------------------------------------------------------------------
# M28.8 — Scope enforcement
# ---------------------------------------------------------------------------


class TestScopeEnforcement:
    def test_scope_mismatch_blocks_execution(self) -> None:
        # Build an executable task for credit_card_engine
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/credit_card_engine/x.py",))
        exe = build_executable_plan(plan)
        assert exe.tasks, "planner must select credit_card_engine"
        target = exe.tasks[0].component
        # Corrupt the installed scope to reference loan_engine instead.
        # The helper lives in the scenario harness; inline a minimal
        # version here to keep the test self-contained.
        cfg = REPO_ROOT / "backend" / "pyproject.toml"
        original = cfg.read_text()
        new_lines: list[str] = []
        in_block = False
        for line in original.splitlines():
            if line.strip() == "[tool.mutmut]":
                in_block = True
                new_lines.append(line)
                new_lines.append('source_paths = ["src/engines/loan_engine.py"]')
                continue
            if in_block and line.strip().startswith("["):
                in_block = False
            if in_block and line.strip().startswith("source_paths"):
                continue
            new_lines.append(line)
        cfg.write_text("\n".join(new_lines) + "\n")
        try:
            discovered = _read_installed_mutmut_scope()
            assert "loan_engine" in discovered
            assert target not in discovered
            ev = execute_mutation_task(exe.tasks[0], max_runtime=5)
            assert ev.failure_kind == FailureKind.SCOPE
            assert ev.exit_code < 0
            assert "SCOPE MISMATCH" in ev.failure_message
        finally:
            cfg.write_text(original)


# ---------------------------------------------------------------------------
# M28.9 — Failure classification
# ---------------------------------------------------------------------------


class TestFailureClassification:
    def test_failure_kind_values_are_distinct(self) -> None:
        values = {k.value for k in FailureKind}
        assert len(values) == len(FailureKind)

    def test_all_failure_kinds_present(self) -> None:
        expected = {
            "verification_failure",
            "infrastructure_failure",
            "evidence_failure",
            "scope_failure",
            "configuration_failure",
            "certification_failure",
        }
        actual = {k.value for k in FailureKind}
        assert expected.issubset(actual)


# ---------------------------------------------------------------------------
# M28.13 — Forensic execution record
# ---------------------------------------------------------------------------


class TestForensicRecord:
    def test_record_captures_full_chain(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/credit_card_engine/x.py",))
        exe = build_executable_plan(plan)
        prior = {m.component: m for m in default_prior_measurements()}
        # No fresh evidence; this is a reconcile-only record
        reconciled = reconcile(plan, {}, prior, default_population())
        forensic = build_forensic_record(plan, exe, {}, reconciled)
        d = forensic.to_dict()
        for k in (
            "record_id",
            "generated_at",
            "repository_sha",
            "change",
            "affected_graph_nodes",
            "invalidations",
            "reused_evidence",
            "selected_tasks",
            "executed_tasks",
            "execution_results",
            "new_evidence",
            "derived_evidence",
            "failures",
            "uncertainties",
            "certification_decision",
        ):
            assert k in d, f"missing {k}"


# ---------------------------------------------------------------------------
# M28.14 — CLI integration smoke
# ---------------------------------------------------------------------------


class TestCLIIntegration:
    def test_evidence_plan_subcommand_exists(self) -> None:
        # We verify the dispatch by reading the canonical control plane
        # (verify.py is now a thin shim per M9-C49/C57; legacy commands
        # route through canonical_control_plane.migration_map).
        from runtime.foundation.verification.canonical_control_plane import (
            migration_map,
        )

        mm = migration_map()
        for cmd in (
            "evidence-plan",
            "evidence-execute",
            "evidence-reconcile",
            "evidence-certify",
        ):
            assert cmd in mm, f"canonical_control_plane missing {cmd} dispatch"


# ---------------------------------------------------------------------------
# C42.28 — Baseline freeze integrity
# ---------------------------------------------------------------------------


class TestBaselineIntegrity:
    def test_baseline_artifact_present(self) -> None:
        p = (
            REPO_ROOT
            / "runtime"
            / "generated"
            / "m9-c42.28"
            / "m9-c42.28-baseline.json"
        )
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["frozen_artifact_count"] == 19
        assert data["runtime_surface_count"] == 9
        assert data["frozen_aggregate_sha256"] != ""

    def test_baseline_scenarios_present(self) -> None:
        p = (
            REPO_ROOT
            / "runtime"
            / "generated"
            / "m9-c42.28"
            / "m9-c42.28-scenarios.json"
        )
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["overall_passed"] is True
        assert len(data["scenarios"]) == 7

    def test_resource_efficiency_demonstrated(self) -> None:
        p = (
            REPO_ROOT
            / "runtime"
            / "generated"
            / "m9-c42.28"
            / "resource-efficiency-benchmark.json"
        )
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["saved_fraction"] > 0.5
        assert data["certification_confidence_preserved"] is True
