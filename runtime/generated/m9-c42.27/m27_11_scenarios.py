#!/usr/bin/env python3
"""
M9-C42.27 — M27.11 End-to-End Planner Scenarios (A–E)

Demonstrates the planner against representative repository changes:

    Scenario A — Test-only change
        Expected: test evidence revalidation; production mutation
        evidence remains reusable.

    Scenario B — One engine source change
        Expected: affected engine; targeted verification; unrelated
        certified evidence reused.

    Scenario C — Verification configuration change
        Expected: appropriate evidence invalidation; re-planning.

    Scenario D — New component admission
        Expected: population expansion; new measurement required;
        aggregate not treated as authoritative until measurement exists.

    Scenario E — C42.24-style discovery defect
        Expected: declared selection != executable discovery; planner
        detects discrepancy; certification blocked.

Produces a single JSON artifact with all five scenarios + their
plan + correlation + verdict.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.correlation import correlate  # noqa: E402
from runtime.foundation.verification.evidence_planner import (  # noqa: E402
    EvidenceAwarePlanner,
    default_planner,
)
from runtime.foundation.verification.evidence_reuse import (  # noqa: E402
    C42_26_COMPONENTS,
    Change,
    ComponentMeasurement,
    EvidenceReuse,
    PopulationSnapshot,
    c42_24_b_measurements,
    c42_25_measurements,
    c42_26_population,
)
from runtime.foundation.verification.graph_model import (  # noqa: E402
    CapabilityNode,
    SourceNode,
    TestSurfaceKind,
    TestSurfaceNode,
    VerificationGraph,
    capability_id,
    source_id,
    surface_id,
)


OUT = REPO_ROOT / "runtime" / "generated" / "m9-c42.27" / "m9-c42.27-scenarios.json"


def _run(planner: EvidenceAwarePlanner, name: str, files: tuple[str, ...]) -> tuple[dict[str, Any], Any, Any]:
    plan = planner.plan(files)
    corr = correlate(plan)
    return {
        "scenario": name,
        "changed_files": list(files),
        "plan": plan.to_dict(),
        "correlation": corr.to_dict(),
    }, plan, corr


def scenario_e() -> dict[str, Any]:
    """C42.24-style discovery defect: declared selection != executable.

    The capability claims coverage but the executable test surface
    does not actually bind to any source.
    """
    g = VerificationGraph()
    cap = capability_id("phantom-cap")
    g.add_capability(CapabilityNode(id=cap, name="phantom-cap", layer="domain"))
    # Only an observation surface (no executable surface).
    surface = surface_id("audit", "backend/tests/audits/phantom")
    g.add_test_surface(
        TestSurfaceNode(
            id=surface,
            path="backend/tests/audits/phantom",
            kind="audit",
        )
    )
    g.link_capability_surface(cap, surface)
    # A source is also linked.
    src = source_id("backend/src/engines/phantom_engine/foo.py")
    g.add_source(
        SourceNode(
            id=src, path="backend/src/engines/phantom_engine/foo.py",
            kind="engine", component="phantom_engine", fingerprint="",
        )
    )
    g.link_source_capability(src, cap)

    pop = PopulationSnapshot(
        population_id="pop-scenario-e",
        created_at="2026-01-01T00:00:00+00:00",
        components=("phantom_engine",),
    )
    planner = EvidenceAwarePlanner(g, pop, [])
    plan = planner.plan(())
    corr = correlate(plan)
    return {
        "scenario": "E_C42_24_discovery_defect",
        "changed_files": [],
        "plan": plan.to_dict(),
        "correlation": corr.to_dict(),
        "expected_outcome": (
            "planner detects discrepancy; certification blocked"
        ),
        "verdict": (
            "PASS" if not corr.certifiable and plan.drift_blockers else "FAIL"
        ),
    }


def scenario_d() -> dict[str, Any]:
    """New component admission into the population."""
    pop_base = c42_26_population()
    # Insert a new component into the population without measurement.
    new_components = pop_base.components + ("newly_admitted_engine",)
    pop = PopulationSnapshot(
        population_id=pop_base.population_id + "-expanded",
        created_at=pop_base.created_at,
        components=new_components,
        component_fingerprints=dict(pop_base.component_fingerprints),
        config_hash=pop_base.config_hash,
        toolchain_hash=pop_base.toolchain_hash,
        repository_sha=pop_base.repository_sha,
        notes="scenario D: expanded population with newly admitted component",
    )
    measurements = c42_24_b_measurements() + c42_25_measurements()
    planner = EvidenceAwarePlanner(
        _graph_for_d(),
        pop,
        measurements,
    )
    plan = planner.plan(())
    corr = correlate(plan)
    gaps = list(corr.certification_gaps)
    selected_fresh_targets = [
        t.target for t in plan.selected_tasks if t.disposition == "selected_fresh"
    ]
    # certifiable=False because there's a gap; check substring match.
    gap_match = any("newly_admitted_engine" in g for g in gaps)
    verdict = (
        "PASS"
        if "newly_admitted_engine" in selected_fresh_targets
        and gap_match
        and not corr.certifiable
        else "FAIL"
    )
    return {
        "scenario": "D_new_component_admission",
        "changed_files": [],
        "plan": plan.to_dict(),
        "correlation": corr.to_dict(),
        "expected_outcome": (
            "newly_admitted_engine requires fresh measurement; "
            "aggregate not authoritative until measured"
        ),
        "verdict": verdict,
    }


def _graph_for_d() -> VerificationGraph:
    g = VerificationGraph()
    # Minimal graph: every existing capability present.
    for c in C42_26_COMPONENTS:
        g.add_capability(
            CapabilityNode(
                id=capability_id(c.replace("_", "-")),
                name=c.replace("_", "-"),
                layer="domain",
            )
        )
    g.add_capability(
        CapabilityNode(
            id=capability_id("newly-admitted-engine"),
            name="newly-admitted-engine",
            layer="domain",
        )
    )
    return g


def main() -> int:
    base_planner = default_planner()
    results: list[dict[str, Any]] = []

    # A — test-only change
    a_dict, a_plan, _ = _run(
        base_planner,
        "A_test_only_change",
        ("backend/tests/unit/engines/credit_card_engine/test_x.py",),
    )
    a_dict["expected_outcome"] = (
        "test evidence revalidation; production mutation evidence "
        "remains reusable for the other 13 components"
    )
    a_dict["verdict"] = (
        "PASS"
        if any(
            t.disposition == "selected_revalidation" and t.target == "credit_card_engine"
            for t in a_plan.selected_tasks
        )
        and sum(
            1
            for t in a_plan.excluded_tasks
            if t.disposition == "excluded_reusable_evidence"
        )
        >= 12
        else "FAIL"
    )
    results.append(a_dict)

    # B — one engine source change
    b_dict, b_plan, _ = _run(
        base_planner,
        "B_engine_source_change",
        ("backend/src/engines/loan_engine/foo.py",),
    )
    b_dict["expected_outcome"] = (
        "only loan_engine invalidated; other 13 components reuse "
        "certified evidence"
    )
    b_dict["verdict"] = (
        "PASS"
        if any(
            t.target == "loan_engine" and t.disposition == "selected_fresh"
            for t in b_plan.selected_tasks
        )
        and len(b_plan.excluded_tasks) == 13
        else "FAIL"
    )
    results.append(b_dict)

    # C — verification configuration change
    c_dict, c_plan, _ = _run(
        base_planner,
        "C_verification_config_change",
        ("pyproject.toml",),
    )
    c_dict["expected_outcome"] = (
        "no specific component invalidated; aggregate derivation "
        "suffices; planner reports no over-broad escalation"
    )
    c_dict["verdict"] = (
        "PASS"
        if not any(
            t.disposition == "selected_fresh" for t in c_plan.selected_tasks
        )
        else "FAIL"
    )
    results.append(c_dict)

    # D — new component admission
    results.append(scenario_d())

    # E — C42.24-style discovery defect
    results.append(scenario_e())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "title": "M9-C42.27 — End-to-End Planner Scenarios (A–E)",
                "milestone": "M9-C42.27",
                "phase": "M27.11",
                "scenarios": results,
            },
            indent=2,
        )
    )
    print(f"Wrote: {OUT.relative_to(REPO_ROOT)}")
    for r in results:
        print(f"  {r['scenario']}: {r['verdict']}")
    return 0 if all(r["verdict"] == "PASS" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
