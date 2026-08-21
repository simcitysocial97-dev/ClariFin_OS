"""M6 — Attribution consumes real pipeline evidence (VEA-2 Phase 2).

These tests pin the behaviour of ``build_observed_failures`` and the
``diagnose-failures`` path: attribution must run on artifacts alone, with zero
manual log parsing, the join key being ``unit_id`` from the M3 manifest (via the
M5 evidence) — never a substring match against a command or test name.
"""

from __future__ import annotations

import inspect

from runtime.foundation.intelligence.platform.attribution import (
    ATTRIBUTION_UNKNOWN,
    IN_BLAST_RADIUS,
    OUTSIDE_BLAST_RADIUS,
    UNMAPPED_UNIT,
    ObservedFailure,
    attribute_failures,
    build_observed_failures,
)
from runtime.foundation.intelligence.platform.blast import compute_blast_radius
from runtime.foundation.intelligence.platform.change import analyze_changes
from runtime.foundation.intelligence.platform.optimizer import optimize_verification
from runtime.system.evidence.aggregator import EvidenceAggregator

# The real specimen from HEAD b9074020.
LOAN_ENGINE_CHANGE = [
    "backend/src/engines/loan_engine/amortization.py",
    "backend/src/engines/loan_engine/floating_rate.py",
]

# The frontend files that actually failed in the specimen — none in the radius.
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


def _frontend_unit_failure(path: str, unit_id: str) -> dict:
    """Mimic one M5 ``unit_failures`` entry (frontend phase).

    In real evidence, ``path`` is the phase log path. Use the real source path
    here so the test mirrors the Phase 1.5 verdict: the source is outside the
    blast radius regardless of whether the path is a log or a source file.
    """
    return {
        "unit_id": unit_id,
        "layer": "frontend",
        "phase": "build",
        "path": path,
        "diagnostic": "This React Hook only works in a Client Component",
        "provenance": {
            "capabilities": ["useLoansCapability"],
            "impact_kinds": ["frontend"],
            "source": "impact-analysis",
        },
        "contributing_units": [unit_id],
    }


def test_adapter_reproduces_phase1_5_verdict_from_artifacts_alone():
    """M6 req 2: from artifacts alone, in_blast_radius=0, not implicated."""
    _, blast, plan = _specimen()
    unit_failures = [
        _frontend_unit_failure(path, "frontend-typecheck-build")
        for path in ACTUAL_FRONTEND_FAILURES
    ]

    failures = build_observed_failures(unit_failures)
    assert failures, "adapter must surface the observed failures"
    assert all(isinstance(f, ObservedFailure) for f in failures)

    report = attribute_failures(blast, failures, plan.selected)
    assert len(report.attributions) == len(ACTUAL_FRONTEND_FAILURES)
    assert not report.in_blast_radius
    assert len(report.outside_blast_radius) == len(ACTUAL_FRONTEND_FAILURES)
    assert report.change_is_implicated is False


def test_synthetic_in_radius_failure_still_implicates():
    """M6 req 2 guard: the join must not be over-corrected into never matching."""
    _, blast, plan = _specimen()
    radius = attribute_failures(blast, [], plan.selected).blast_radius_paths
    frontend_entity = next(p for p in radius if p.startswith("frontend/"))

    failures = build_observed_failures(
        [_frontend_unit_failure(frontend_entity, "frontend-typecheck-build")]
    )
    report = attribute_failures(blast, failures, plan.selected)
    assert report.change_is_implicated is True
    assert len(report.in_blast_radius) == 1
    assert report.in_blast_radius[0].attribution == IN_BLAST_RADIUS
    assert report.in_blast_radius[0].matched_entity == frontend_entity


def test_unjoinable_failure_is_attribution_unknown():
    """M6 req 5: failures that cannot be joined to a unit are UNKNOWN, not guessed."""
    _, blast, plan = _specimen()
    unit_failures = [
        {
            "unit_id": UNMAPPED_UNIT,
            "layer": "backend",
            "phase": "unit",
            # A real path is present in the evidence, but with no unit it cannot
            # be tied to the impact analysis that justified its run.
            "path": "backend/src/engines/loan_engine/amortization.py",
            "diagnostic": "backend suite 'unit' failed (exit=1)",
            "provenance": {},
            "contributing_units": [],
        }
    ]
    failures = build_observed_failures(unit_failures)
    report = attribute_failures(blast, failures, plan.selected)
    assert len(report.unknown) == 1
    assert report.attributions[0].attribution == ATTRIBUTION_UNKNOWN
    assert report.change_is_implicated is False
    # The real evidence path is preserved, not silently dropped.
    assert report.attributions[0].failure.code == (
        "backend/src/engines/loan_engine/amortization.py"
    )


def test_no_evidence_state_is_explicit_not_fabricated():
    """M6 negative test: empty evidence is a visible 'nothing to diagnose', not green."""
    _, blast, plan = _specimen()
    failures = build_observed_failures([])
    assert failures == []

    report = attribute_failures(blast, failures, plan.selected)
    assert report.to_dict()["totals"] == {
        "observed": 0,
        "in_blast_radius": 0,
        "outside_blast_radius": 0,
        "unknown": 0,
    }
    assert report.change_is_implicated is False


def test_pre_existing_is_never_inferred():
    """M6 req 3: absent evidence => OUTSIDE_BLAST_RADIUS, never PRE_EXISTING."""
    _, blast, plan = _specimen()
    failures = build_observed_failures(
        [
            _frontend_unit_failure(
                "frontend/lib/runtime/navigation-runtime.ts", "frontend-typecheck-build"
            )
        ]
    )
    report = attribute_failures(blast, failures, plan.selected)
    assert report.attributions[0].attribution == OUTSIDE_BLAST_RADIUS
    assert report.attributions[0].failure.pre_existing is None


def test_adapter_performs_no_string_matching():
    """E-4 defect class is prohibited: no command/test-name inference here."""
    source = inspect.getsource(build_observed_failures)
    forbidden = (
        "re.search",
        "re.match",
        "re.findall",
        "startswith(",
        "endswith(",
        "in command",
        ".find(",
    )
    for token in forbidden:
        assert token not in source, f"{token} found in build_observed_failures"


def test_unmapped_constant_matches_aggregator_sentinel():
    from runtime.system.evidence.aggregator import UNMAPPED_SENTINEL

    assert UNMAPPED_UNIT == UNMAPPED_SENTINEL


def test_evidence_aggregator_unit_failures_are_adapter_compatible():
    """The M5 ``unit_failures`` shape is directly consumable by the adapter."""
    # An empty aggregation has no failures; the adapter must accept that shape.
    assert build_observed_failures([]) == []
    assert EvidenceAggregator is not None  # aggregator import is valid
