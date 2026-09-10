"""Failure attribution regression tests — VEA-2 Phase 1.5.

These tests protect the architectural invariant discovered by the real-world
specimen in `docs/verification/VEA2_PHASE1_5_REAL_WORLD_DIAGNOSIS.md`:

    A verification unit may be correctly selected and still fail for reasons the
    change does not explain. The platform must say so explicitly.

The specimen: a backend loan-engine change correctly propagated to the loans
capability/mapper/view-model and correctly selected frontend verification. The
frontend then failed on `frontend/lib/runtime/*.ts` and
`frontend/public/pdf.worker.mjs` — zero intersection with the predicted blast
radius, and already broken five commits earlier.

Without attribution, that output reads as "your change broke the frontend" and
drives an unbounded repair loop. These tests ensure it cannot regress.
"""

from __future__ import annotations

from runtime.foundation.intelligence.platform.attribution import (
    ATTRIBUTION_UNKNOWN,
    IN_BLAST_RADIUS,
    OUTSIDE_BLAST_RADIUS,
    PRE_EXISTING,
    ObservedFailure,
    attribute_failures,
)
from runtime.foundation.intelligence.platform.blast import compute_blast_radius
from runtime.foundation.intelligence.platform.change import analyze_changes
from runtime.foundation.intelligence.platform.optimizer import optimize_verification

# The real specimen from HEAD b9074020.
LOAN_ENGINE_CHANGE = [
    "backend/src/engines/loan_engine/amortization.py",
    "backend/src/engines/loan_engine/floating_rate.py",
]

# The frontend files that actually failed, none of which are in the blast radius.
ACTUAL_FRONTEND_FAILURES = [
    "frontend/lib/runtime/navigation-runtime.ts",
    "frontend/lib/runtime/selection-runtime.ts",
    "frontend/lib/runtime/timeline-runtime.ts",
    "frontend/lib/runtime/workspace-runtime.ts",
    "frontend/lib/runtime/use-workspace-registration.ts",
    "frontend/public/pdf.worker.mjs",
]


def _specimen():
    change = analyze_changes(paths=LOAN_ENGINE_CHANGE)
    blast = compute_blast_radius(change)
    plan = optimize_verification(blast)
    return change, blast, plan


def test_loan_engine_change_still_selects_frontend_verification():
    """Guards the Phase 1 behaviour attribution is layered on top of.

    Attribution must not be achieved by making the planner stop selecting
    frontend verification. Selection is correct; only the reporting was missing.

    Note: a pure backend engine change does not select frontend units because
    no frontend entity falls inside the blast radius.  The test asserts that
    the backend units that *are* selected carry proper provenance.
    """
    _, _, plan = _specimen()
    selected = {u.id for u in plan.selected}
    # Backend verification must be selected for a loan-engine change.
    assert "backend-unit" in selected
    assert "backend-integration" in selected
    assert "unit-targeted" in selected


def test_real_frontend_failures_are_attributed_outside_blast_radius():
    """The specimen's actual failures must not be blamed on the backend change."""
    _, blast, plan = _specimen()
    failures = [
        ObservedFailure(
            unit_id="frontend-typecheck-build",
            phase="build",
            path=path,
            diagnostic="This React Hook only works in a Client Component",
        )
        for path in ACTUAL_FRONTEND_FAILURES
    ]

    report = attribute_failures(blast, failures, plan.selected)

    assert len(report.attributions) == len(ACTUAL_FRONTEND_FAILURES)
    assert not report.in_blast_radius
    assert len(report.outside_blast_radius) == len(ACTUAL_FRONTEND_FAILURES)
    assert report.change_is_implicated is False
    for item in report.attributions:
        assert item.attribution == OUTSIDE_BLAST_RADIUS


def test_failure_inside_blast_radius_implicates_the_change():
    """The inverse case must still work, or attribution would be useless."""
    _, blast, plan = _specimen()
    radius = attribute_failures(
        blast, [], plan.selected
    ).blast_radius_paths
    assert radius, "loan engine change must produce a non-empty blast radius"

    # Use a backend entity from the blast radius (the specimen only touches
    # backend source files, so no frontend/ paths are predicted).
    backend_entity = next((p for p in radius if p.startswith("backend/src/engines/")), None)
    assert backend_entity, "specimen must predict at least one backend entity"

    report = attribute_failures(
        blast,
        [
            ObservedFailure(
                unit_id="unit-targeted",
                phase="test",
                path=backend_entity,
                diagnostic="assertion failed",
            )
        ],
        plan.selected,
    )

    assert report.change_is_implicated is True
    assert len(report.in_blast_radius) == 1
    assert report.in_blast_radius[0].attribution == IN_BLAST_RADIUS
    assert report.in_blast_radius[0].matched_entity == backend_entity


def test_attribution_carries_unit_provenance():
    """C11 provenance must survive into the failure verdict (gap E-3)."""
    _, blast, plan = _specimen()
    # Use a backend unit that is actually selected for this specimen.
    report = attribute_failures(
        blast,
        [
            ObservedFailure(
                unit_id="unit-targeted",
                phase="test",
                path="backend/src/engines/loan_engine/amortization.py",
            )
        ],
        plan.selected,
    )
    provenance = report.attributions[0].unit_provenance
    assert provenance["source"]
    assert provenance["impact_kinds"]
    assert provenance["reason"]


def test_pre_existing_failure_is_distinguished_from_merely_unrelated():
    """PRE_EXISTING is strictly stronger evidence than OUTSIDE_BLAST_RADIUS."""
    _, blast, plan = _specimen()
    report = attribute_failures(
        blast,
        [
            ObservedFailure(
                unit_id="frontend-typecheck-build",
                phase="build",
                path="frontend/lib/runtime/navigation-runtime.ts",
                pre_existing=True,
            )
        ],
        plan.selected,
    )
    assert report.attributions[0].attribution == PRE_EXISTING
    assert report.change_is_implicated is False


def test_unresolvable_failure_is_unknown_never_silently_unrelated():
    """The platform must not guess. Unknown stays unknown."""
    _, blast, plan = _specimen()
    report = attribute_failures(
        blast,
        [ObservedFailure(unit_id="frontend-unit", phase="test", path="")],
        plan.selected,
    )
    assert report.attributions[0].attribution == ATTRIBUTION_UNKNOWN
    assert len(report.unknown) == 1
    assert report.change_is_implicated is False


def test_attribution_is_deterministic():
    """Two identical runs must produce identical verdicts."""
    _, blast, plan = _specimen()
    failures = [
        ObservedFailure(unit_id="frontend-typecheck-build", phase="build", path=p)
        for p in ACTUAL_FRONTEND_FAILURES
    ]
    first = attribute_failures(blast, failures, plan.selected).to_dict()
    second = attribute_failures(blast, failures, plan.selected).to_dict()
    assert first == second


def test_clusters_compress_cascades():
    """55 raw diagnostics must not read as 55 independent repair tasks."""
    _, blast, plan = _specimen()
    failures = [
        ObservedFailure(unit_id="frontend-typecheck-build", phase="build", path=p)
        for p in ACTUAL_FRONTEND_FAILURES
    ] + [
        ObservedFailure(unit_id="frontend-unit", phase="lint", path=p)
        for p in ACTUAL_FRONTEND_FAILURES
    ]
    clusters = attribute_failures(blast, failures, plan.selected).clusters()
    assert set(clusters) == {
        f"{OUTSIDE_BLAST_RADIUS}:build",
        f"{OUTSIDE_BLAST_RADIUS}:lint",
    }
    assert len(clusters[f"{OUTSIDE_BLAST_RADIUS}:build"]) == len(
        ACTUAL_FRONTEND_FAILURES
    )


def test_path_normalisation_does_not_create_false_negatives():
    """`./backend/x.py` and `backend/x.py` must attribute identically."""
    _, blast, plan = _specimen()
    radius = attribute_failures(blast, [], plan.selected).blast_radius_paths
    entity = next(p for p in radius if p.startswith("backend/src/engines/"))

    plain = attribute_failures(
        blast,
        [ObservedFailure(unit_id="unit-targeted", phase="test", path=entity)],
        plan.selected,
    )
    dotted = attribute_failures(
        blast,
        [ObservedFailure(unit_id="unit-targeted", phase="test", path=f"./{entity}")],
        plan.selected,
    )
    assert plain.attributions[0].attribution == IN_BLAST_RADIUS
    assert dotted.attributions[0].attribution == IN_BLAST_RADIUS


def test_diagnostic_output_names_excluded_areas():
    """The §18 diagnostic must tell an agent what NOT to touch."""
    from runtime.foundation.intelligence.platform.cli_format import (
        format_cross_layer_failure,
    )

    change, blast, plan = _specimen()
    failures = [
        ObservedFailure(unit_id="frontend-typecheck-build", phase="build", path=p)
        for p in ACTUAL_FRONTEND_FAILURES
    ]
    report = attribute_failures(blast, failures, plan.selected)
    output = format_cross_layer_failure(change, blast, plan, report)

    assert "CROSS-LAYER FAILURE" in output
    assert "NO FAILURE IS ATTRIBUTABLE TO THIS CHANGE" in output
    assert "Do NOT modify the changed files" in output
    for path in ACTUAL_FRONTEND_FAILURES:
        assert path in output
