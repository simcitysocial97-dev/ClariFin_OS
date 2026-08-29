"""
M9-C42.27 — Test suite for evidence reuse, population snapshots,
verification graph, evidence-aware planner, and correlation layer.

Includes the C42.24 architectural regression test (Phase 7) that
makes the behaviour-engine discovery defect a permanent guard.

Run with:
    .venv/bin/python -m pytest runtime/tests/test_m9_c42_27.py -v
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.correlation import correlate  # noqa: E402
from runtime.foundation.verification.evidence_planner import (  # noqa: E402
    EvidenceAwarePlanner,
    default_planner,
    describe_change,
)
from runtime.foundation.verification.evidence_reuse import (  # noqa: E402
    C42_26_COMPONENTS,
    C42_26_POPULATION_ID,
    INVALIDATION_RULES,
    Change,
    ComponentMeasurement,
    InvalidationVerdict,
    PopulationSnapshot,
    aggregate_invalidation,
    c42_24_b_measurements,
    c42_25_measurements,
    c42_26_population,
    decide_reuse,
    evaluate_rule,
    load_snapshot,
    save_snapshot,
)
from runtime.foundation.verification.graph_model import (  # noqa: E402
    CapabilityNode,
    SourceNode,
    TestSurfaceNode,
    VerificationGraph,
    capability_id,
    source_id,
    surface_id,
)

# ---------------------------------------------------------------------------
# M27.4 — Invalidation rules
# ---------------------------------------------------------------------------


class TestInvalidationRules:
    def test_all_rules_have_unique_ids(self) -> None:
        ids = [r.rule_id for r in INVALIDATION_RULES]
        assert len(ids) == len(set(ids)), "duplicate rule ids"

    def test_source_change_invalidates_component(self) -> None:
        rule = next(r for r in INVALIDATION_RULES if r.rule_id == "R-SRC-001")
        v = evaluate_rule(rule, Change(kind="source_change", target="foo"), "foo")
        assert v.triggered is True
        assert v.scope == "INVALIDATES_COMPONENT"

    def test_unrelated_source_change_does_not_invalidate(self) -> None:
        rule = next(r for r in INVALIDATION_RULES if r.rule_id == "R-SRC-001")
        v = evaluate_rule(rule, Change(kind="source_change", target="foo"), "bar")
        assert v.triggered is False

    def test_test_change_invalidates_evidence_only(self) -> None:
        rule = next(r for r in INVALIDATION_RULES if r.rule_id == "R-SRC-003")
        v = evaluate_rule(rule, Change(kind="test_change", target="foo"), "foo")
        assert v.triggered is True
        assert v.scope == "INVALIDATES_EVIDENCE_ONLY"

    def test_new_component_does_not_invalidate_existing(self) -> None:
        rule = next(r for r in INVALIDATION_RULES if r.rule_id == "R-POP-001")
        v = evaluate_rule(rule, Change(kind="population_add", target="new"), "existing")
        assert v.triggered is False

    def test_aggregate_invalidation_precedence(self) -> None:
        # evidence-only + component → component
        verdicts = [
            InvalidationVerdict("R-A", "INVALIDATES_EVIDENCE_ONLY", True, ""),
            InvalidationVerdict("R-B", "INVALIDATES_COMPONENT", True, ""),
        ]
        assert aggregate_invalidation(verdicts) == "INVALIDATES_COMPONENT"

    def test_aggregate_invalidation_no_trigger(self) -> None:
        verdicts = [
            InvalidationVerdict("R-A", "INVALIDATES_COMPONENT", False, ""),
            InvalidationVerdict("R-B", "INVALIDATES_TASK", False, ""),
        ]
        assert aggregate_invalidation(verdicts) == "DOES_NOT_INVALIDATE"


# ---------------------------------------------------------------------------
# M27.4 — Population snapshots + measurements
# ---------------------------------------------------------------------------


class TestPopulationSnapshot:
    def test_c42_26_population_has_14_components(self) -> None:
        pop = c42_26_population()
        assert len(pop.components) == 14
        assert pop.components == C42_26_COMPONENTS

    def test_population_fingerprint_changes_with_config(self) -> None:
        pop1 = c42_26_population()
        pop2 = PopulationSnapshot(
            population_id=pop1.population_id,
            created_at=pop1.created_at,
            components=pop1.components,
            component_fingerprints=pop1.component_fingerprints,
            config_hash="DIFFERENT",
            toolchain_hash=pop1.toolchain_hash,
            repository_sha=pop1.repository_sha,
            notes=pop1.notes,
        )
        assert pop1.fingerprint() != pop2.fingerprint()

    def test_snapshot_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "snap"
            save_snapshot.__globals__["SNAPSHOT_DIR"] = target  # type: ignore[attr-defined]
            snap = c42_26_population()
            meas = c42_24_b_measurements() + c42_25_measurements()
            save_snapshot(snap, meas)
            loaded_snap, loaded_meas = load_snapshot(snap.population_id)
            assert loaded_snap.population_id == snap.population_id
            assert loaded_snap.components == snap.components
            assert len(loaded_meas) == len(meas)
            for m in meas:
                lm = next(
                    x for x in loaded_meas if x.measurement_id == m.measurement_id
                )
                assert lm.component == m.component
                assert lm.summary == m.summary
            # Reset
            save_snapshot.__globals__["SNAPSHOT_DIR"] = (  # type: ignore[attr-defined]
                REPO_ROOT / "runtime" / "generated" / "m9-c42.27" / "snapshots"
            )

    def test_derived_aggregate_matches_c42_26(self) -> None:
        from runtime.foundation.verification.evidence_reuse import (
            c42_26_derived_aggregate,
        )

        measurements = c42_24_b_measurements() + c42_25_measurements()
        agg = c42_26_derived_aggregate(measurements)
        assert agg.population_id == C42_26_POPULATION_ID
        assert agg.formula == "sum(killed)/sum(scored) * 100"
        # C42.26 certification reports ~60.3%
        assert 59.5 <= agg.result <= 61.0

    def test_measurement_fingerprint_includes_all_validity_components(self) -> None:
        m = ComponentMeasurement(
            measurement_id="x",
            component="foo",
            population_id="p",
            kind="mutation",
            run_id="r",
            measured_at="2026-01-01T00:00:00Z",
            repository_sha="abc",
            source_fingerprint="s",
            test_fingerprint="t",
            config_hash="c",
            toolchain_hash="tk",
        )
        # Changing any input changes the fingerprint.
        base = m.fingerprint()
        assert m.fingerprint() == base
        m2 = ComponentMeasurement(
            measurement_id="x",
            component="foo",
            population_id="p",
            kind="mutation",
            run_id="r",
            measured_at="2026-01-01T00:00:00Z",
            repository_sha="abc",
            source_fingerprint="s",
            test_fingerprint="t",
            config_hash="c-DIFFERENT",
            toolchain_hash="tk",
        )
        assert m2.fingerprint() != base


# ---------------------------------------------------------------------------
# M27.4 — Reuse decision
# ---------------------------------------------------------------------------


class TestReuseDecision:
    def test_unchanged_component_is_reusable(self) -> None:
        pop = c42_26_population()
        meas = c42_24_b_measurements()[0]
        r = decide_reuse(
            meas.component, Change(kind="no_change", target=meas.component), meas, pop
        )
        assert r.disposition in ("reusable", "reusable_aggregate")

    def test_source_change_invalidates_only_affected(self) -> None:
        pop = c42_26_population()
        m_credit = next(
            m for m in c42_24_b_measurements() if m.component == "credit_card_engine"
        )
        m_loan = next(
            m for m in c42_24_b_measurements() if m.component == "loan_engine"
        )
        r_credit = decide_reuse(
            "credit_card_engine",
            Change(kind="source_change", target="credit_card_engine"),
            m_credit,
            pop,
        )
        r_loan = decide_reuse(
            "loan_engine",
            Change(kind="no_change", target="loan_engine"),
            m_loan,
            pop,
        )
        assert r_credit.disposition in (
            "invalidated_component",
            "invalidated_capability",
        )
        assert r_loan.disposition in ("reusable", "reusable_aggregate")

    def test_no_evidence_for_new_component(self) -> None:
        pop = c42_26_population()
        r = decide_reuse(
            "new_component",
            Change(kind="population_add", target="new_component"),
            None,
            pop,
        )
        assert r.disposition == "no_evidence"

    def test_test_change_only_invalidates_evidence(self) -> None:
        pop = c42_26_population()
        m = c42_24_b_measurements()[0]
        r = decide_reuse(
            m.component,
            Change(kind="test_change", target=m.component),
            m,
            pop,
        )
        # Per R-SRC-003 a test change invalidates evidence only,
        # not the production component measurement at capability or
        # component scope. The invalidation rule is the narrowest
        # possible scope.
        assert r.disposition == "invalidated_evidence_only"
        # The rule is R-SRC-003 specifically.
        assert "R-SRC-003" in r.invalidations

    def test_toolchain_change_invalidates_measurement(self) -> None:
        pop = c42_26_population()
        m = c42_24_b_measurements()[0]
        r = decide_reuse(
            m.component,
            Change(kind="toolchain_change", target="mutmut"),
            m,
            pop,
        )
        assert r.disposition in ("invalidated_component", "invalidated_capability")


# ---------------------------------------------------------------------------
# M27.5 — Evidence-aware planner
# ---------------------------------------------------------------------------


class TestEvidenceAwarePlanner:
    def test_no_op_plan_excludes_all_with_reuse(self) -> None:
        planner = default_planner()
        plan = planner.plan(())
        assert plan.affected_components == ()
        assert len(plan.selected_tasks) == 0
        assert len(plan.excluded_tasks) == 14
        assert all(
            t.disposition == "excluded_reusable_evidence" for t in plan.excluded_tasks
        )
        assert len(plan.derived_aggregates) == 1

    def test_source_change_only_invalidates_affected_component(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/credit_card_engine/foo.py",))
        assert plan.affected_components == ("credit_card",)
        assert len(plan.selected_tasks) == 1
        assert plan.selected_tasks[0].target == "credit_card_engine"
        assert plan.selected_tasks[0].disposition == "selected_fresh"
        assert len(plan.excluded_tasks) == 13

    def test_test_only_change_reuses_production_evidence(self) -> None:
        planner = default_planner()
        plan = planner.plan(
            ("backend/tests/unit/engines/credit_card_engine/test_x.py",)
        )
        # All components except credit_card should reuse their
        # production measurement. The credit_card engine gets a
        # selected_revalidation because its test surface changed.
        excluded_targets = {t.target for t in plan.excluded_tasks}
        assert "credit_card_engine" not in excluded_targets
        assert "loan_engine" in excluded_targets
        assert "reconciliation_engine" in excluded_targets

    def test_behaviour_engine_change_does_not_invalidate_others(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/behaviour_engine/some.py",))
        # Only behaviour_engine should be selected_fresh
        fresh = [t for t in plan.selected_tasks if t.disposition == "selected_fresh"]
        assert len(fresh) == 1
        assert fresh[0].target == "behaviour_engine"

    def test_every_selected_task_has_cause(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/credit_card_engine/foo.py",))
        for t in plan.selected_tasks:
            assert t.cause, f"task {t.task_id} has no cause"
            assert t.disposition.startswith("selected_")

    def test_every_excluded_task_has_cause(self) -> None:
        planner = default_planner()
        plan = planner.plan(())
        for t in plan.excluded_tasks:
            assert t.cause, f"task {t.task_id} has no cause"
            assert t.disposition.startswith("excluded_")

    def test_plan_is_deterministic(self) -> None:
        p1 = default_planner().plan(("backend/src/engines/loan_engine/x.py",))
        p2 = default_planner().plan(("backend/src/engines/loan_engine/x.py",))
        assert p1.plan_id == p2.plan_id
        assert len(p1.selected_tasks) == len(p2.selected_tasks)
        assert len(p1.excluded_tasks) == len(p2.excluded_tasks)

    def test_plan_does_not_silently_expand_scope(self) -> None:
        # A test-only change to one engine should not select tasks
        # for any other engine.
        planner = default_planner()
        plan = planner.plan(("backend/tests/unit/engines/cashflow_engine/test_x.py",))
        for t in plan.selected_tasks:
            # Only test-evidence re-measurement for cashflow is permitted.
            assert (
                t.target == "cashflow_engine"
            ), f"planner silently expanded scope to {t.target}"

    def test_describe_change_recognises_engine_source(self) -> None:
        d = describe_change("backend/src/engines/loan_engine/foo.py")
        assert d.kind == "source_change"
        assert d.component == "loan"
        assert d.capability == "loan-management"

    def test_describe_change_recognises_test_file(self) -> None:
        d = describe_change("backend/tests/unit/test_x.py")
        assert d.kind == "test_change"

    def test_describe_change_recognises_config(self) -> None:
        d = describe_change("pyproject.toml")
        assert d.kind == "config_change"


# ---------------------------------------------------------------------------
# M27.6 — C42.24 architectural regression test (MANDATORY)
# ---------------------------------------------------------------------------


class TestC4224DriftRegression:
    """
    The C42.24 behaviour-engine discovery failure became a permanent
    architectural regression test.

    A capability must not claim coverage that the executable test
    surface cannot actually reach. The planner must detect the
    discrepancy and block certification.
    """

    def test_drift_detected_when_capability_has_no_source_binding(self) -> None:
        g = VerificationGraph()
        g.add_capability(
            CapabilityNode(
                id=capability_id("phantom"),
                name="phantom",
                layer="domain",
            )
        )
        g.add_test_surface(
            TestSurfaceNode(
                id=surface_id("unit", "backend/tests/unit/phantom"),
                path="backend/tests/unit/phantom",
                kind="unit",
            )
        )
        g.link_capability_surface(
            capability_id("phantom"),
            surface_id("unit", "backend/tests/unit/phantom"),
        )
        # No source nodes linked to the capability.
        # The capability name "phantom" must also be in the
        # population for the planner to consult its drift status.
        pop = PopulationSnapshot(
            population_id="pop-test",
            created_at="2026-01-01T00:00:00+00:00",
            components=("phantom",),
        )
        m = ComponentMeasurement(
            measurement_id="meas::phantom::test",
            component="phantom",
            population_id="pop-test",
            kind="mutation",
            run_id="r",
            measured_at="2026-01-01T00:00:00+00:00",
            repository_sha="x",
            source_fingerprint="",
            test_fingerprint="",
            config_hash="c",
            toolchain_hash="tk",
        )
        planner = EvidenceAwarePlanner(g, pop, [m])
        plan = planner.plan(("backend/src/engines/phantom/foo.py",))
        assert any(
            "phantom" in blocker for blocker in plan.drift_blockers
        ), f"drift not detected: {plan.drift_blockers}"

    def test_drift_detected_when_surface_does_not_reach_source(self) -> None:
        g = VerificationGraph()
        cap = capability_id("test-cap")
        g.add_capability(CapabilityNode(id=cap, name="test-cap", layer="domain"))
        # Observation-only surface (not in executable_kinds).
        surface = surface_id("audit", "backend/tests/audits/test-cap")
        g.add_test_surface(
            TestSurfaceNode(
                id=surface,
                path="backend/tests/audits/test-cap",
                kind="audit",
            )
        )
        g.link_capability_surface(cap, surface)
        src = source_id("backend/src/engines/test_cap/foo.py")
        g.add_source(
            SourceNode(
                id=src,
                path="backend/src/engines/test_cap/foo.py",
                kind="engine",
                component="test_cap",
                fingerprint="",
            )
        )
        g.link_source_capability(src, cap)

        pop = PopulationSnapshot(
            population_id="pop-test",
            created_at="2026-01-01T00:00:00+00:00",
            components=("test_cap",),
        )
        planner = EvidenceAwarePlanner(g, pop, [])
        plan = planner.plan(())
        assert any(
            "test-cap" in blocker for blocker in plan.drift_blockers
        ), f"drift not detected: {plan.drift_blockers}"

    def test_no_drift_when_capability_is_well_bound(self) -> None:
        g = VerificationGraph()
        cap = capability_id("ok-cap")
        g.add_capability(CapabilityNode(id=cap, name="ok-cap", layer="domain"))
        surface = surface_id("unit", "backend/tests/unit/ok")
        g.add_test_surface(
            TestSurfaceNode(
                id=surface,
                path="backend/tests/unit/ok",
                kind="unit",
            )
        )
        g.link_capability_surface(cap, surface)
        src = source_id("backend/src/ok/x.py")
        g.add_source(
            SourceNode(
                id=src,
                path="backend/src/ok/x.py",
                kind="other",
                component=None,
                fingerprint="",
            )
        )
        g.link_source_capability(src, cap)
        pop = PopulationSnapshot(
            population_id="pop-test",
            created_at="2026-01-01T00:00:00+00:00",
            components=("ok-cap",),
        )
        planner = EvidenceAwarePlanner(g, pop, [])
        plan = planner.plan(())
        assert plan.drift_blockers == ()


# ---------------------------------------------------------------------------
# M27.8 — Capability-level impact resolution
# ---------------------------------------------------------------------------


class TestCapabilityLevelImpact:
    def test_helper_change_does_not_escalate_to_full_repopulation(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/credit_card_engine/_helpers.py",))
        # Only credit_card is selected for fresh measurement; the
        # other 13 components reuse certified evidence.
        assert len(plan.selected_tasks) == 1
        assert plan.selected_tasks[0].target == "credit_card_engine"
        assert len(plan.excluded_tasks) == 13
        # The aggregate is still derivable from reusable components.
        assert len(plan.derived_aggregates) == 1

    def test_capability_explanation_is_present(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/cashflow_engine/cashflow.py",))
        assert plan.affected_capabilities
        assert "cashflow" in plan.affected_capabilities[0]


# ---------------------------------------------------------------------------
# M27.9 — Correlation layer
# ---------------------------------------------------------------------------


class TestCorrelation:
    def test_correlation_answers_canonical_questions(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/credit_card_engine/foo.py",))
        corr = correlate(plan)
        assert corr.changed_files
        assert corr.affected_capabilities
        assert corr.affected_components
        assert corr.derived_aggregates  # at least the C42.26 aggregate
        assert isinstance(corr.certifiable, bool)
        assert corr.rationale

    def test_correlation_for_noop_is_certifiable(self) -> None:
        planner = default_planner()
        plan = planner.plan(())
        corr = correlate(plan)
        assert corr.certifiable is True
        assert len(corr.uncertain_components) == 0

    def test_correlation_distinguishes_reused_vs_fresh(self) -> None:
        planner = default_planner()
        plan = planner.plan(("backend/src/engines/credit_card_engine/foo.py",))
        corr = correlate(plan)
        # credit_card should be in fresh
        assert "credit_card_engine" in corr.fresh_evidence_targets
        # others should be in reused
        assert any(r.scope_id == "loan_engine" for r in corr.reused_evidence)


# ---------------------------------------------------------------------------
# M27.3 — Graph model
# ---------------------------------------------------------------------------


class TestGraphModel:
    def test_graph_holds_all_node_kinds(self) -> None:
        g = VerificationGraph()
        g.add_source(
            SourceNode(
                id=source_id("x"),
                path="x",
                kind="engine",
                component="x",
                fingerprint="",
            )
        )
        g.add_capability(
            CapabilityNode(id=capability_id("x"), name="x", layer="domain")
        )
        assert len(g.sources) == 1
        assert len(g.capabilities) == 1

    def test_edges_are_idempotent(self) -> None:
        g = VerificationGraph()
        g.link_source_capability(source_id("a"), capability_id("b"))
        g.link_source_capability(source_id("a"), capability_id("b"))
        assert g.source_to_capability[source_id("a")] == (capability_id("b"),)
