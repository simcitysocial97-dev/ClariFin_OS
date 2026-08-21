"""Failure Attribution — VEA-2 Phase 1.5.

Answers the one question the verification platform could not previously answer:

    A selected verification unit failed. Is that failure *inside* the blast
    radius that justified selecting the unit, or *outside* it?

Motivation (real specimen, not speculation)
-------------------------------------------
A backend loan-engine change correctly propagated to
``capability:useLoansCapability`` / ``mapper:frontend/lib/mappers/loans-mapper.ts``
/ ``view_model:AmortizationEntryViewModel`` and correctly selected the
``frontend-unit`` and ``frontend-typecheck-build`` units.

Those units then failed — on ``frontend/lib/runtime/*.ts`` and
``frontend/public/pdf.worker.mjs``, which have **zero** intersection with the
predicted blast radius and were already broken five commits earlier.

The platform reported "frontend verification failed" for a change that did not
break the frontend. An agent reading that output reasonably concludes the change
is guilty and begins an unbounded repair loop. This module makes the distinction
explicit and machine-readable.

Design constraints
------------------
* Consumes the objects the platform already computes (``BlastRadius``,
  ``VerificationUnit``). It does not re-derive dependency analysis.
* Pure and deterministic: no subprocess, no clock, no I/O. Callers supply the
  observed failures.
* ``ATTRIBUTION_UNKNOWN`` is an explicit outcome. The module never guesses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from runtime.foundation.intelligence.platform.blast import BlastRadius
from runtime.foundation.intelligence.platform.optimizer import VerificationUnit

__all__ = [
    "ObservedFailure",
    "FailureAttribution",
    "AttributionReport",
    "attribute_failures",
    "build_observed_failures",
    "IN_BLAST_RADIUS",
    "OUTSIDE_BLAST_RADIUS",
    "ATTRIBUTION_UNKNOWN",
    "PRE_EXISTING",
    "UNMAPPED_UNIT",
]

# Mirrors ``EvidenceAggregator.UNMAPPED_SENTINEL`` in the evidence package. A
# failure that resolves to this unit_id was never joined to a verification unit
# by the M3 manifest, so it cannot be tied to the impact analysis that justified
# running its unit. The two values MUST stay equal; ``test_evidence_frontend_units.py``
# asserts they are, and ``TestBuildObservedFailures`` below compares against it.
UNMAPPED_UNIT = "UNMAPPED"

#: The failing file is an entity the blast radius predicted. The change is a
#: credible cause and remediation should start from the dependency chain.
IN_BLAST_RADIUS = "IN_BLAST_RADIUS"

#: The failing file is not in the blast radius. The change is not a demonstrated
#: cause; the failure is incidental to this verification run.
OUTSIDE_BLAST_RADIUS = "OUTSIDE_BLAST_RADIUS"

#: The failing file is outside the blast radius *and* was proven to fail before
#: the change. Strictly stronger than OUTSIDE_BLAST_RADIUS.
PRE_EXISTING = "PRE_EXISTING"

#: Not enough information to attribute. Never inferred away.
ATTRIBUTION_UNKNOWN = "ATTRIBUTION_UNKNOWN"


def _normalise(path: str) -> str:
    """Normalise a repo path for comparison.

    Entity paths and diagnostic paths disagree on leading ``./`` and on
    separator style, so both are flattened before comparison.
    """
    cleaned = str(path).strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned.strip("/")


@dataclass(frozen=True, slots=True)
class ObservedFailure:
    """One failure actually observed while executing a verification unit.

    ``unit_id`` ties the failure to the plan, which is what makes attribution
    possible. ``phase`` keeps eslint/tsc/vitest/build distinguishable instead of
    collapsing them into a single exit code.
    """

    unit_id: str
    phase: str
    path: str
    diagnostic: str = ""
    code: str = ""
    pre_existing: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "phase": self.phase,
            "path": self.path,
            "diagnostic": self.diagnostic,
            "code": self.code,
            "pre_existing": self.pre_existing,
        }


@dataclass(frozen=True, slots=True)
class FailureAttribution:
    """An observed failure plus the verdict on whether the change explains it."""

    failure: ObservedFailure
    attribution: str
    reason: str
    matched_entity: str | None = None
    unit_provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure": self.failure.to_dict(),
            "attribution": self.attribution,
            "reason": self.reason,
            "matched_entity": self.matched_entity,
            "unit_provenance": self.unit_provenance,
        }


@dataclass(frozen=True, slots=True)
class AttributionReport:
    """Attribution verdicts for every observed failure in one verification run."""

    attributions: tuple[FailureAttribution, ...]
    blast_radius_paths: tuple[str, ...]

    @property
    def in_blast_radius(self) -> tuple[FailureAttribution, ...]:
        return tuple(a for a in self.attributions if a.attribution == IN_BLAST_RADIUS)

    @property
    def outside_blast_radius(self) -> tuple[FailureAttribution, ...]:
        return tuple(
            a
            for a in self.attributions
            if a.attribution in (OUTSIDE_BLAST_RADIUS, PRE_EXISTING)
        )

    @property
    def unknown(self) -> tuple[FailureAttribution, ...]:
        return tuple(
            a for a in self.attributions if a.attribution == ATTRIBUTION_UNKNOWN
        )

    @property
    def change_is_implicated(self) -> bool:
        """True only when at least one failure lies inside the blast radius.

        When this is False and failures exist, the verification run is red for
        reasons the change does not explain. That is the signal that prevents an
        agent from "fixing" the change.
        """
        return bool(self.in_blast_radius)

    def clusters(self) -> dict[str, tuple[FailureAttribution, ...]]:
        """Group attributions by (attribution, phase) to compress cascades."""
        grouped: dict[str, list[FailureAttribution]] = {}
        for item in self.attributions:
            key = f"{item.attribution}:{item.failure.phase}"
            grouped.setdefault(key, []).append(item)
        return {k: tuple(v) for k, v in sorted(grouped.items())}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "failure-attribution/v1",
            "blast_radius_paths": list(self.blast_radius_paths),
            "totals": {
                "observed": len(self.attributions),
                "in_blast_radius": len(self.in_blast_radius),
                "outside_blast_radius": len(self.outside_blast_radius),
                "unknown": len(self.unknown),
            },
            "change_is_implicated": self.change_is_implicated,
            "attributions": [a.to_dict() for a in self.attributions],
        }


def _blast_radius_paths(blast: BlastRadius) -> tuple[str, ...]:
    """Every repo path the blast radius predicts, normalised and deduplicated."""
    paths: set[str] = set()
    for node in blast.all_impacted:
        path = getattr(node.ref, "path", None)
        if path:
            paths.add(_normalise(path))
    return tuple(sorted(paths))


def _match(failure_path: str, radius: Sequence[str]) -> str | None:
    """Return the blast-radius path explaining ``failure_path``, if any.

    Exact match first. Directory containment is accepted because the provider
    records some entities (notably engines) as directories rather than files.
    """
    target = _normalise(failure_path)
    if not target:
        return None
    for candidate in radius:
        if target == candidate:
            return candidate
    for candidate in radius:
        if candidate and target.startswith(candidate + "/"):
            return candidate
    return None


def attribute_failures(
    blast: BlastRadius,
    failures: Iterable[ObservedFailure],
    units: Iterable[VerificationUnit] = (),
) -> AttributionReport:
    """Correlate observed failures against the blast radius that selected the units.

    Args:
        blast: The blast radius already computed for the change.
        failures: Failures observed while executing the plan.
        units: The selected units, used to attach C11 provenance to each verdict.

    Returns:
        An :class:`AttributionReport`. Failures whose path cannot be resolved are
        reported as ``ATTRIBUTION_UNKNOWN`` rather than assumed to be unrelated.
    """
    radius = _blast_radius_paths(blast)
    unit_index = {u.id: u for u in units}

    results: list[FailureAttribution] = []
    for failure in failures:
        unit = unit_index.get(failure.unit_id)
        provenance: dict[str, Any] = {}
        if unit is not None:
            provenance = {
                "capabilities": list(unit.capabilities),
                "impact_kinds": list(unit.impact_kinds),
                "source": unit.source,
                "reason": unit.reason,
            }

        if not _normalise(failure.path):
            results.append(
                FailureAttribution(
                    failure=failure,
                    attribution=ATTRIBUTION_UNKNOWN,
                    reason="failure has no resolvable file path",
                    unit_provenance=provenance,
                )
            )
            continue

        matched = _match(failure.path, radius)
        if matched is not None:
            results.append(
                FailureAttribution(
                    failure=failure,
                    attribution=IN_BLAST_RADIUS,
                    reason=(
                        f"{_normalise(failure.path)} is in the blast radius "
                        f"(matched {matched}); the change is a credible cause"
                    ),
                    matched_entity=matched,
                    unit_provenance=provenance,
                )
            )
            continue

        if failure.pre_existing:
            results.append(
                FailureAttribution(
                    failure=failure,
                    attribution=PRE_EXISTING,
                    reason=(
                        f"{_normalise(failure.path)} is not in the blast radius and "
                        f"was observed failing before the change"
                    ),
                    unit_provenance=provenance,
                )
            )
            continue

        results.append(
            FailureAttribution(
                failure=failure,
                attribution=OUTSIDE_BLAST_RADIUS,
                reason=(
                    f"{_normalise(failure.path)} is not in the blast radius; the "
                    f"change is not a demonstrated cause"
                ),
                unit_provenance=provenance,
            )
        )

    return AttributionReport(attributions=tuple(results), blast_radius_paths=radius)


def build_observed_failures(
    unit_failures: Iterable[dict[str, Any]],
) -> list[ObservedFailure]:
    """Adapt M5 evidence into :class:`ObservedFailure` records — VEA-2 Phase 2, M6.

    This is the seam that removes the Phase 1.5 dependency on hand-parsed log
    files. The ``unit_id`` is taken verbatim from the evidence, which itself
    inherited it from the M3 run manifest via the M5 join. **No string matching
    against commands or test names happens here** — that is the E-4 defect class
    and it is prohibited by the §1 invariant.

    Behaviour:

    * A failure that could not be joined to a unit (``unit_id == UNMAPPED``) has
      no verification scope it can be tied to. It is reported as
      ``ATTRIBUTION_UNKNOWN`` — its file path is blanked so ``attribute_failures``
      classifies it honestly rather than guessing an ``OUTSIDE_BLAST_RADIUS`` it
      cannot support. The real evidence path is preserved in ``code``.
    * ``pre_existing`` is populated **only** when the evidence records it. Absent
      evidence leaves it ``None``, which classifies as ``OUTSIDE_BLAST_RADIUS`` —
      never ``PRE_EXISTING``. We do not infer pre-existence (UNKNOWN over GUESSED).
    """
    failures: list[ObservedFailure] = []
    for entry in unit_failures:
        unit_id = entry.get("unit_id") or ""

        if unit_id == UNMAPPED_UNIT:
            failures.append(
                ObservedFailure(
                    unit_id=UNMAPPED_UNIT,
                    phase=entry.get("phase", ""),
                    path="",
                    diagnostic=entry.get("diagnostic", ""),
                    code=entry.get("path", ""),
                )
            )
            continue

        failures.append(
            ObservedFailure(
                unit_id=unit_id,
                phase=entry.get("phase", ""),
                path=entry.get("path", ""),
                diagnostic=entry.get("diagnostic", ""),
                pre_existing=entry.get("pre_existing"),
            )
        )
    return failures
