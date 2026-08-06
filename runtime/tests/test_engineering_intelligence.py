"""Tests for the Engineering Intelligence Layer — Program 14.0.

These tests assert the *constitutional* properties of the intelligence layer,
not just that it produces output:

* ownership is provider-resolved, never inferred from filenames
* blast radius propagation is evidence-backed and deterministic
* verification skips are always justified
* risk never under-reports a High dimension
* CI collection is annotation-first and never downloads log archives
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.intelligence.platform.blast import compute_blast_radius
from runtime.foundation.intelligence.platform.change import analyze_changes
from runtime.foundation.intelligence.platform.changeset import (
    _parse_patch,
)
from runtime.foundation.intelligence.platform.cost import estimate_cost
from runtime.foundation.intelligence.platform.memory import build_memory
from runtime.foundation.intelligence.platform.optimizer import optimize_verification
from runtime.foundation.intelligence.platform.pipeline import (
    ARTIFACTS,
    run_intelligence,
)
from runtime.foundation.intelligence.platform.repair import (
    Defect,
    build_repair_intelligence,
)
from runtime.foundation.intelligence.platform.resolver import get_resolver
from runtime.foundation.intelligence.platform.risk import assess_risk

ENGINE_MODULE = "backend/src/engines/account_engine/balance.py"
ROUTER = "backend/src/routers/accounts.py"


@pytest.fixture(scope="module")
def resolver():
    return get_resolver()


# ---------------------------------------------------------------------------
# Resolver — ownership comes from the provider
# ---------------------------------------------------------------------------


def test_engine_module_resolves_to_module_not_engine(resolver):
    """A file inside an engine is an EngineModule, never an ownership root."""
    refs = resolver.classify_path(ENGINE_MODULE)
    assert refs, "engine module must resolve"
    assert refs[0].kind == "engine_module"


def test_module_owning_engine_is_provider_resolved(resolver):
    owner = resolver.owning_engine(ENGINE_MODULE)
    assert owner is not None
    assert owner.kind == "engine"
    assert owner.key == "account_engine"
    assert owner.path == "backend/src/engines/account_engine"


def test_unknown_path_resolves_to_nothing(resolver):
    """No heuristic fallback: an unknown path must not be force-fitted."""
    assert resolver.classify_path("some/unknown/place/thing.py") == []


def test_graph_nodes_resolve_across_id_forms(resolver):
    """Capabilities use different id forms per graph; both must reconcile."""
    by_name = resolver.resolve_node("capability:useAccountsCapability")
    assert by_name is not None
    assert by_name.kind == "capability"


# ---------------------------------------------------------------------------
# Phase 1 — change intelligence
# ---------------------------------------------------------------------------


def test_change_maps_module_to_owning_engine(resolver):
    change = analyze_changes(resolver=resolver, paths=[ENGINE_MODULE])
    engine_keys = [r.key for r in change.entities["engines"]]
    assert "account_engine" in engine_keys


def test_router_change_yields_endpoints(resolver):
    change = analyze_changes(resolver=resolver, paths=[ROUTER])
    assert change.entities["endpoints"], "router change must surface endpoints"


def test_runtime_path_is_platform_scope_not_unmapped(resolver):
    change = analyze_changes(resolver=resolver, paths=["runtime/verify.py"])
    assert change.platform_paths == ("runtime/verify.py",)
    assert change.unmapped_paths == ()


def test_unknown_production_path_is_unmapped(resolver):
    change = analyze_changes(resolver=resolver, paths=["backend/src/nope/gone.py"])
    assert change.unmapped_paths == ("backend/src/nope/gone.py",)


def test_diff_parser_extracts_symbols_imports_routes():
    patch = (
        "diff --git a/backend/src/routers/x.py b/backend/src/routers/x.py\n"
        "--- a/backend/src/routers/x.py\n"
        "+++ b/backend/src/routers/x.py\n"
        '+@router.get("/things")\n'
        "+def list_things():\n"
        "+from backend.src.services import thing_service\n"
    )
    parsed = _parse_patch(patch)["backend/src/routers/x.py"]
    assert "list_things" in parsed["added_symbols"]
    assert "backend.src.services" in parsed["added_imports"]
    assert "GET /things" in parsed["added_routes"]


# ---------------------------------------------------------------------------
# Phase 2 — blast radius
# ---------------------------------------------------------------------------


def test_blast_radius_is_evidence_backed(resolver):
    change = analyze_changes(resolver=resolver, paths=[ENGINE_MODULE])
    blast = compute_blast_radius(change, resolver=resolver)
    assert blast.indirect
    for node in blast.indirect:
        assert node.graph and node.via and node.relation


def test_blast_radius_propagates_to_dependents(resolver):
    """Changing an engine module must reach the service that uses it."""
    change = analyze_changes(resolver=resolver, paths=[ENGINE_MODULE])
    blast = compute_blast_radius(change, resolver=resolver)
    refs = {n.ref.ref for n in blast.indirect}
    assert "service:backend/src/services/account_service.py" in refs


def test_blast_radius_is_deterministic(resolver):
    def snapshot():
        change = analyze_changes(resolver=resolver, paths=[ENGINE_MODULE])
        data = compute_blast_radius(change, resolver=resolver).to_dict()
        data.pop("generated_at")
        return data

    assert snapshot() == snapshot()


def test_verification_impact_uses_provider_tests(resolver):
    """Test targets must be real provider-recorded paths, not synthesised."""
    change = analyze_changes(resolver=resolver, paths=[ENGINE_MODULE])
    blast = compute_blast_radius(change, resolver=resolver)
    known = set(resolver.tests)
    assert blast.verification
    for ref in blast.verification:
        assert ref.key in known


# ---------------------------------------------------------------------------
# Phase 3 — verification optimizer
# ---------------------------------------------------------------------------


def test_every_skip_is_justified(resolver):
    change = analyze_changes(resolver=resolver, paths=[ENGINE_MODULE])
    plan = optimize_verification(compute_blast_radius(change, resolver=resolver))
    assert plan.skipped
    for skipped in plan.skipped:
        assert skipped.reason and skipped.justification


def test_plan_is_cheaper_than_full_profile(resolver):
    change = analyze_changes(resolver=resolver, paths=[ENGINE_MODULE])
    plan = optimize_verification(compute_blast_radius(change, resolver=resolver))
    assert plan.estimated_seconds < plan.baseline_seconds


def test_playwright_skipped_when_no_workspace_impacted(resolver):
    change = analyze_changes(resolver=resolver, paths=[ENGINE_MODULE])
    plan = optimize_verification(compute_blast_radius(change, resolver=resolver))
    skipped = {s.id for s in plan.skipped}
    assert "playwright-e2e" in skipped


def test_empty_change_selects_no_unit_tests(resolver):
    change = analyze_changes(resolver=resolver, paths=[])
    plan = optimize_verification(compute_blast_radius(change, resolver=resolver))
    assert plan.estimated_seconds == 0
    assert not plan.selected


# ---------------------------------------------------------------------------
# Phase 4 — risk
# ---------------------------------------------------------------------------


def _risk_for(resolver, paths):
    change = analyze_changes(resolver=resolver, paths=paths)
    blast = compute_blast_radius(change, resolver=resolver)
    plan = optimize_verification(blast, resolver=resolver)
    return assess_risk(change, blast, plan, resolver=resolver)


def test_risk_has_seven_dimensions(resolver):
    risk = _risk_for(resolver, [ENGINE_MODULE])
    names = {d.name for d in risk.dimensions}
    assert names == {
        "Architectural Risk",
        "Regression Risk",
        "Dependency Risk",
        "Coverage Risk",
        "Ownership Risk",
        "Contract Risk",
        "CI Risk",
    }


def test_every_risk_dimension_has_evidence(resolver):
    risk = _risk_for(resolver, [ENGINE_MODULE])
    for dim in risk.dimensions:
        assert dim.evidence and all(e.strip() for e in dim.evidence)


def test_overall_risk_never_below_worst_dimension(resolver):
    """A single High dimension must not be averaged away."""
    risk = _risk_for(resolver, [ENGINE_MODULE, ROUTER])
    order = ["Low", "Medium", "High"]
    worst = max((d.level for d in risk.dimensions), key=order.index)
    assert order.index(risk.overall_level) >= order.index(worst)


def test_ownership_risk_flags_unmapped_path(resolver):
    risk = _risk_for(resolver, ["backend/src/nope/gone.py"])
    ownership = next(d for d in risk.dimensions if d.name == "Ownership Risk")
    assert ownership.score > 0


# ---------------------------------------------------------------------------
# Phase 5 — repair
# ---------------------------------------------------------------------------


def test_repair_orders_and_cites_evidence(resolver):
    change = analyze_changes(resolver=resolver, paths=[ENGINE_MODULE])
    blast = compute_blast_radius(change, resolver=resolver)
    defect = Defect(
        id="d1",
        source="test",
        summary="balance regression",
        paths=(ENGINE_MODULE,),
        severity="high",
    )
    plan = build_repair_intelligence(blast, defects=[defect], resolver=resolver)
    item = plan.items[0]
    assert item["repair_order"][0]["step"] == 1
    assert item["affected_tests"]
    assert item["confidence"] == 1.0
    assert plan.rollback["strategy"] == "revert-by-ownership-root"


def test_repair_is_reproducible(resolver):
    change = analyze_changes(resolver=resolver, paths=[ENGINE_MODULE])
    blast = compute_blast_radius(change, resolver=resolver)
    defect = Defect("d1", "test", "x", (ENGINE_MODULE,), "high")

    def order():
        plan = build_repair_intelligence(blast, defects=[defect], resolver=resolver)
        return [s["target"] for s in plan.items[0]["repair_order"]]

    assert order() == order()


# ---------------------------------------------------------------------------
# Phase 6 / 8 — memory and cost
# ---------------------------------------------------------------------------


def test_memory_reports_empty_history_honestly(tmp_path: Path):
    memory = build_memory(generated_dir=tmp_path)
    assert memory.observations == 0
    assert memory.notes


def test_memory_only_counts_recurring_signatures(tmp_path: Path):
    """A one-off failure is not 'recurring'."""
    (tmp_path / "engineering-events.jsonl").write_text(
        json.dumps(
            {
                "event_type": "VerificationCompleted",
                "payload": {"profile": "quick", "status": "failed", "failed": 1},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    memory = build_memory(generated_dir=tmp_path)
    assert memory.recurring_verification_failures == ()


def test_cost_quantifies_avoided_work(resolver):
    change = analyze_changes(resolver=resolver, paths=[ENGINE_MODULE])
    plan = optimize_verification(compute_blast_radius(change, resolver=resolver))
    cost = estimate_cost(plan)
    assert cost.totals["expected_runtime_seconds"] > 0
    assert cost.totals["avoided_seconds"] > 0
    assert cost.totals["reduction_percent"] > 0


# ---------------------------------------------------------------------------
# Phase 7 — CI policy
# ---------------------------------------------------------------------------


def test_ci_module_never_downloads_log_archives():
    source = (
        Path(__file__).resolve().parents[1]
        / "foundation"
        / "intelligence"
        / "platform"
        / "ci.py"
    ).read_text(encoding="utf-8")
    assert "gh run download" not in source
    assert "allow_logs" in source


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def test_pipeline_writes_all_artifacts(tmp_path: Path):
    run = run_intelligence(
        paths=[ENGINE_MODULE], write=True, collect_ci=False, generated_dir=tmp_path
    )
    for name in ARTIFACTS:
        assert (tmp_path / name).exists(), name
    assert len(run.written) == len(ARTIFACTS)


def test_pipeline_output_is_valid_json(tmp_path: Path):
    run_intelligence(
        paths=[ENGINE_MODULE], write=True, collect_ci=False, generated_dir=tmp_path
    )
    for name in ARTIFACTS:
        json.loads((tmp_path / name).read_text(encoding="utf-8"))


def test_platform_state_does_not_rerun_audits(tmp_path: Path):
    run = run_intelligence(
        paths=[ENGINE_MODULE], write=False, collect_ci=False, generated_dir=tmp_path
    )
    assert run.state["audits_rerun"] is False
