"""Boundary classification and the deterministic bounded fallback strategy.

A verification boundary is the set of repository-relative files a run considers
changed. Small boundaries resolve to a focused plan: only the capabilities the
changed files touch are verified. That is the whole point of boundary-scoped
verification, and it is what makes the common case cheap.

Very large boundaries break that model. The plan grows with the boundary — a
244-commit branch produced 246 tasks and roughly 50 minutes of execution — and
the only previous response was a warning printed to stderr followed by
*continuing into that same plan*. A warning that does not change behaviour is
not a control, and a run that reports success after 50 minutes of expanding work
is not a bounded strategy.

This module replaces the warning with a decision:

    NORMAL      -> incremental verification of the affected capabilities
    AT_LIMIT    -> incremental verification, recorded explicitly
    OVERSIZED   -> deterministic bounded fallback: a fixed, whole-repository
                   capability sweep with a known task count

The fallback is deterministic on purpose. It does not sample, does not truncate
the file list, and does not lower any threshold. It trades *focus* for
*coverage*: instead of a large set of narrowly-scoped tasks it runs a smaller
set of repository-wide capability checks. That is a real change in what is
verified and it is reported as such, rather than being presented as equivalent.

Every run emits a :class:`BoundaryEvidence` record stating the boundary size, its
classification, the strategy selected, which capabilities were covered, and what
scope was intentionally given up. A run that cannot describe its own scope is
not acceptable evidence.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BoundaryClass(str, Enum):
    """How a boundary is treated, relative to the configured size limits."""

    #: Below the limit: incremental, boundary-scoped verification.
    NORMAL = "NORMAL"
    #: Exactly at the limit: still incremental, but recorded explicitly because
    #: it is the largest boundary that is still treated incrementally.
    AT_LIMIT = "AT_LIMIT"
    #: Above the limit: bounded fallback instead of an expanding plan.
    OVERSIZED = "OVERSIZED"
    #: No files at all: certified no-op.
    EMPTY = "EMPTY"


class Strategy(str, Enum):
    """The verification strategy selected for a boundary."""

    INCREMENTAL = "incremental-capability"
    BOUNDED_FALLBACK = "bounded-repository-fallback"
    NO_OP = "certified-no-op"


#: Above this many changed files the incremental plan is replaced by the
#: bounded fallback. Chosen because the incremental plan grows roughly linearly
#: with the boundary and each task carries its own process startup; a boundary
#: this size already means the change is repository-wide in practice.
DEFAULT_OVERSIZED_THRESHOLD = 500

#: Profiles executed by the bounded fallback, in order. This is the whole set,
#: not a sample: the point of the fallback is that coverage is complete at the
#: capability level even though it is not scoped to individual files.
#:
#: These are the repository's existing profiles. The fallback introduces no new
#: verification architecture — it selects a fixed, already-defined set.
FALLBACK_PROFILE_ORDER: tuple[str, ...] = ("backend", "frontend", "contracts")

#: Environment overrides. Kept explicit and validated so a misconfiguration
#: fails loudly instead of silently disabling the control.
ENV_THRESHOLD = "VERIFY_OVERSIZED_BOUNDARY_THRESHOLD"
ENV_FALLBACK_DISABLED = "VERIFY_BOUNDARY_FALLBACK_DISABLED"


def oversized_threshold(default: int = DEFAULT_OVERSIZED_THRESHOLD) -> int:
    """Read the oversized boundary threshold, rejecting nonsense values.

    A non-positive or non-numeric value would make the control unreachable or
    make every boundary oversized. Neither is a safe default, so both raise.
    """

    raw = os.environ.get(ENV_THRESHOLD)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{ENV_THRESHOLD} must be an integer, got {raw!r}") from exc
    if value <= 0:
        raise ValueError(f"{ENV_THRESHOLD} must be positive, got {value}")
    return value


def fallback_disabled() -> bool:
    """Whether the operator has explicitly disabled the bounded fallback.

    Disabling is possible but is reported as such in the evidence, because an
    oversized boundary executed incrementally is exactly the uncontrolled
    behaviour this module exists to prevent, and it must never be mistaken for
    the bounded strategy having run.
    """

    raw = os.environ.get(ENV_FALLBACK_DISABLED, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def classify_boundary_size(
    file_count: int, *, threshold: int | None = None
) -> BoundaryClass:
    """Classify a boundary by size."""

    if file_count <= 0:
        return BoundaryClass.EMPTY
    limit = oversized_threshold() if threshold is None else threshold
    if file_count > limit:
        return BoundaryClass.OVERSIZED
    if file_count == limit:
        return BoundaryClass.AT_LIMIT
    return BoundaryClass.NORMAL


def select_strategy(
    boundary_class: BoundaryClass,
) -> Strategy:
    """Choose the verification strategy for a classified boundary."""

    if boundary_class is BoundaryClass.EMPTY:
        return Strategy.NO_OP
    if boundary_class is BoundaryClass.OVERSIZED and not fallback_disabled():
        return Strategy.BOUNDED_FALLBACK
    return Strategy.INCREMENTAL


@dataclass(frozen=True)
class BoundaryEvidence:
    """What a run did about its boundary, and what it gave up.

    Emitted for every run so that a reader never has to infer scope from a
    warning in a log.
    """

    boundary_size: int
    threshold: int
    boundary_class: BoundaryClass
    strategy: Strategy
    #: Capabilities the selected strategy verified.
    capabilities_covered: tuple[str, ...] = ()
    #: What the strategy deliberately did not verify, stated plainly.
    intentionally_bounded_scope: str = ""
    #: True when an oversized boundary was executed incrementally because the
    #: operator disabled the fallback. Recorded so it can never be mistaken for
    #: the bounded strategy having run.
    fallback_disabled: bool = False
    #: Task counts, before and after strategy selection, when known.
    incremental_task_count: int | None = None
    fallback_task_count: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_size": self.boundary_size,
            "threshold": self.threshold,
            "boundary_class": self.boundary_class.value,
            "strategy": self.strategy.value,
            "capabilities_covered": list(self.capabilities_covered),
            "intentionally_bounded_scope": self.intentionally_bounded_scope,
            "fallback_disabled": self.fallback_disabled,
            "incremental_task_count": self.incremental_task_count,
            "fallback_task_count": self.fallback_task_count,
            **({"extra": self.extra} if self.extra else {}),
        }

    def render(self) -> str:
        """Human-readable evidence block, printed to stdout by `verify check`."""

        lines = [
            f"[boundary] size={self.boundary_size} threshold={self.threshold} class={self.boundary_class.value} strategy={self.strategy.value}"
        ]
        if self.capabilities_covered:
            lines.append(
                "[boundary] capabilities covered: {}".format(
                    ", ".join(self.capabilities_covered)
                )
            )
        if self.incremental_task_count is not None:
            lines.append(
                f"[boundary] incremental plan tasks: {self.incremental_task_count}"
            )
        if self.fallback_task_count is not None:
            lines.append(
                f"[boundary] bounded fallback tasks: {self.fallback_task_count}"
            )
        if self.intentionally_bounded_scope:
            lines.append(
                f"[boundary] intentionally bounded scope: {self.intentionally_bounded_scope}"
            )
        if self.fallback_disabled:
            lines.append(
                f"[boundary] WARNING: bounded fallback disabled by "
                f"{ENV_FALLBACK_DISABLED}; an oversized boundary was executed "
                "incrementally and is NOT bounded verification"
            )
        return "\n".join(lines)


def build_evidence(
    *,
    boundary_size: int,
    strategy: Strategy,
    capabilities_covered: tuple[str, ...] = (),
    intentionally_bounded_scope: str = "",
    incremental_task_count: int | None = None,
    fallback_task_count: int | None = None,
    threshold: int | None = None,
) -> BoundaryEvidence:
    """Assemble the evidence record for a run."""

    limit = oversized_threshold() if threshold is None else threshold
    return BoundaryEvidence(
        boundary_size=boundary_size,
        threshold=limit,
        boundary_class=classify_boundary_size(boundary_size, threshold=limit),
        strategy=strategy,
        capabilities_covered=capabilities_covered,
        intentionally_bounded_scope=intentionally_bounded_scope,
        fallback_disabled=fallback_disabled(),
        incremental_task_count=incremental_task_count,
        fallback_task_count=fallback_task_count,
    )
