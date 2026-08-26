"""
M9-C42.27 — Verification Graph Model (Phase 3)

Canonical graph nodes for the verification architecture. The graph
is the authoritative model used by the planner, evidence layer, and
correlation layer to answer:

    What changed? -> What capability? -> What evidence exists?
                  -> What must be re-measured? -> What is certifiable?

The graph is *not* an inferred structure. It is constructed from
explicit, enumerable relationships between:

    SourceNode
    CapabilityNode
    TestSurfaceNode
    VerificationTaskNode
    EvidenceNode
    CertificationNode

It is additive on top of the existing C42.26 verification architecture.
It does not modify the planner's existing surface area; it adds a
dedicated graph layer the planner consults.

Pure logic only — no subprocess, no filesystem writes at import time.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

# ---------------------------------------------------------------------------
# Source nodes — production code that may be exercised by verification.
# ---------------------------------------------------------------------------

SourceKind = Literal[
    "engine",          # backend/src/engines/<name>/*.py
    "service",         # backend/src/services/<name>/*.py
    "router",          # backend/src/routers/<name>/*.py
    "model",           # backend/src/models/*.py / core/dtos / core/domain
    "core",            # backend/src/core/* (non-DTO)
    "common",          # backend/src/common/*
    "config",          # configuration files
    "test",            # backend/tests/** (excluding generated)
    "runtime",         # runtime/** (verification framework itself)
    "frontend",        # frontend/**
    "other",           # anything not otherwise classified
]


@dataclass(frozen=True, slots=True)
class SourceNode:
    """A production source file (or test file) that may be verified."""

    id: str
    path: str                # repo-relative path
    kind: SourceKind
    component: str | None    # engine name, service name, router name, etc.
    fingerprint: str         # sha256 of file contents (or "" if unknown)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path": self.path,
            "kind": self.kind,
            "component": self.component,
            "fingerprint": self.fingerprint,
        }


# ---------------------------------------------------------------------------
# Capability nodes — the user-observable / system-observable capability.
# ---------------------------------------------------------------------------

CapabilityLayer = Literal["domain", "intelligence", "platform", "api", "frontend"]


@dataclass(frozen=True, slots=True)
class CapabilityNode:
    """A user/system capability the application delivers."""

    id: str                       # e.g. "cashflow" or "credit-card-risk"
    name: str                     # human-readable
    layer: CapabilityLayer
    description: str = ""
    source_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "layer": self.layer,
            "description": self.description,
            "source_ids": list(self.source_ids),
        }


# ---------------------------------------------------------------------------
# Test surface nodes — the tests that actually exercise source.
# ---------------------------------------------------------------------------

TestSurfaceKind = Literal[
    "unit",           # backend/tests/unit/**
    "property",       # backend/tests/properties/**
    "invariant",      # backend/tests/invariants/**
    "contract",       # backend/tests/contract/**
    "integration",    # backend/tests/integration/**
    "golden",         # backend/tests/golden/**
    "capability",     # backend/tests/capability/**
    "e2e_frontend",   # frontend e2e (playwright)
    "runtime",        # runtime/tests/**
    "audit",          # backend/tests/audits/**
    "architecture",   # backend/tests/architecture/**
]


@dataclass(frozen=True, slots=True)
class TestSurfaceNode:
    """A surface that can exercise a source/capability."""

    id: str
    path: str
    kind: TestSurfaceKind
    description: str = ""
    test_file_ids: tuple[str, ...] = field(default_factory=tuple)
    capability_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path": self.path,
            "kind": self.kind,
            "description": self.description,
            "test_file_ids": list(self.test_file_ids),
            "capability_ids": list(self.capability_ids),
        }


# ---------------------------------------------------------------------------
# Verification task nodes — concrete operations the orchestrator can run.
# ---------------------------------------------------------------------------

TaskKind = Literal[
    "unit",
    "property",
    "invariant",
    "contract",
    "integration",
    "golden",
    "e2e",
    "mutation",
    "static",
    "coverage",
]


@dataclass(frozen=True, slots=True)
class VerificationTaskNode:
    """A concrete verification operation."""

    id: str
    kind: TaskKind
    command: str | None
    script: str | None
    description: str
    capability_ids: tuple[str, ...] = field(default_factory=tuple)
    test_surface_ids: tuple[str, ...] = field(default_factory=tuple)
    estimated_duration_seconds: int = 0
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "command": self.command,
            "script": self.script,
            "description": self.description,
            "capability_ids": list(self.capability_ids),
            "test_surface_ids": list(self.test_surface_ids),
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "metadata": dict(self.metadata),
        }


# ---------------------------------------------------------------------------
# Evidence nodes — the actual measured evidence.
# ---------------------------------------------------------------------------

EvidenceKind = Literal[
    "unit_pass",
    "property_pass",
    "invariant_pass",
    "contract_pass",
    "integration_pass",
    "golden_pass",
    "e2e_pass",
    "mutation_score",
    "coverage",
    "static_lint",
    "derived_aggregate",
    "capability_certification",
]


EvidenceStatus = Literal["fresh", "reusable", "derived", "stale", "invalidated"]


@dataclass(frozen=True, slots=True)
class EvidenceNode:
    """An evidence record — what was actually measured and is the result."""

    id: str
    kind: EvidenceKind
    component_id: str | None    # engine/component or capability this evidence is for
    task_id: str | None
    run_id: str
    measured_at: str            # ISO timestamp
    repository_sha: str
    config_hash: str            # fingerprint of toolchain/config used
    population_id: str | None   # which population snapshot this evidence belongs to
    fingerprint: str            # sha256 of (run_id + config_hash + measurement)
    status: EvidenceStatus
    summary: dict[str, str | int | float | None] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "component_id": self.component_id,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "measured_at": self.measured_at,
            "repository_sha": self.repository_sha,
            "config_hash": self.config_hash,
            "population_id": self.population_id,
            "fingerprint": self.fingerprint,
            "status": self.status,
            "summary": dict(self.summary),
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Certification nodes — the conclusion the evidence supports.
# ---------------------------------------------------------------------------

CertificationStatus = Literal[
    "certified",            # all required evidence present and valid
    "certified_by_composition",  # evidence composed/derived from multiple sub-evidence
    "uncertified",          # missing evidence or invalidation
    "blocked_by_drift",     # discovered inconsistency (e.g. C42.24-style)
]


@dataclass(frozen=True, slots=True)
class CertificationNode:
    """A certification conclusion for a component or capability."""

    id: str
    scope_id: str            # capability_id or component_id
    scope_kind: Literal["component", "capability", "population", "repository"]
    status: CertificationStatus
    evidence_ids: tuple[str, ...]
    derived_from_ids: tuple[str, ...] = field(default_factory=tuple)
    gaps: tuple[str, ...] = field(default_factory=tuple)
    decided_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scope_id": self.scope_id,
            "scope_kind": self.scope_kind,
            "status": self.status,
            "evidence_ids": list(self.evidence_ids),
            "derived_from_ids": list(self.derived_from_ids),
            "gaps": list(self.gaps),
            "decided_at": self.decided_at,
            "rationale": self.rationale,
        }


# ---------------------------------------------------------------------------
# Graph container
# ---------------------------------------------------------------------------

@dataclass
class VerificationGraph:
    """The complete verification graph for the repository."""

    sources: dict[str, SourceNode] = field(default_factory=dict)
    capabilities: dict[str, CapabilityNode] = field(default_factory=dict)
    test_surfaces: dict[str, TestSurfaceNode] = field(default_factory=dict)
    tasks: dict[str, VerificationTaskNode] = field(default_factory=dict)
    evidence: dict[str, EvidenceNode] = field(default_factory=dict)
    certifications: dict[str, CertificationNode] = field(default_factory=dict)

    # Edge maps (source -> capability) and (capability -> test surface)
    source_to_capability: dict[str, tuple[str, ...]] = field(default_factory=dict)
    capability_to_surface: dict[str, tuple[str, ...]] = field(default_factory=dict)
    surface_to_task: dict[str, tuple[str, ...]] = field(default_factory=dict)
    task_to_evidence: dict[str, tuple[str, ...]] = field(default_factory=dict)
    evidence_to_certification: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def capabilities_for_source(self, source_id: str) -> tuple[CapabilityNode, ...]:
        cap_ids = self.source_to_capability.get(source_id, ())
        return tuple(self.capabilities[c] for c in cap_ids if c in self.capabilities)

    def surfaces_for_capability(self, capability_id: str) -> tuple[TestSurfaceNode, ...]:
        s_ids = self.capability_to_surface.get(capability_id, ())
        return tuple(self.test_surfaces[s] for s in s_ids if s in self.test_surfaces)

    def tasks_for_surface(self, surface_id: str) -> tuple[VerificationTaskNode, ...]:
        t_ids = self.surface_to_task.get(surface_id, ())
        return tuple(self.tasks[t] for t in t_ids if t in self.tasks)

    def evidence_for_task(self, task_id: str) -> tuple[EvidenceNode, ...]:
        e_ids = self.task_to_evidence.get(task_id, ())
        return tuple(self.evidence[e] for e in e_ids if e in self.evidence)

    def evidence_for_component(
        self, component_id: str
    ) -> tuple[EvidenceNode, ...]:
        return tuple(
            e for e in self.evidence.values() if e.component_id == component_id
        )

    def add_source(self, node: SourceNode) -> None:
        self.sources[node.id] = node

    def add_capability(self, node: CapabilityNode) -> None:
        self.capabilities[node.id] = node

    def add_test_surface(self, node: TestSurfaceNode) -> None:
        self.test_surfaces[node.id] = node

    def add_task(self, node: VerificationTaskNode) -> None:
        self.tasks[node.id] = node

    def add_evidence(self, node: EvidenceNode) -> None:
        self.evidence[node.id] = node

    def add_certification(self, node: CertificationNode) -> None:
        self.certifications[node.id] = node

    def link_source_capability(self, source_id: str, capability_id: str) -> None:
        existing = list(self.source_to_capability.get(source_id, ()))
        if capability_id not in existing:
            existing.append(capability_id)
            self.source_to_capability[source_id] = tuple(existing)

    def link_capability_surface(
        self, capability_id: str, surface_id: str
    ) -> None:
        existing = list(self.capability_to_surface.get(capability_id, ()))
        if surface_id not in existing:
            existing.append(surface_id)
            self.capability_to_surface[capability_id] = tuple(existing)

    def link_surface_task(self, surface_id: str, task_id: str) -> None:
        existing = list(self.surface_to_task.get(surface_id, ()))
        if task_id not in existing:
            existing.append(task_id)
            self.surface_to_task[surface_id] = tuple(existing)

    def link_task_evidence(self, task_id: str, evidence_id: str) -> None:
        existing = list(self.task_to_evidence.get(task_id, ()))
        if evidence_id not in existing:
            existing.append(evidence_id)
            self.task_to_evidence[task_id] = tuple(existing)

    def link_evidence_certification(
        self, evidence_id: str, certification_id: str
    ) -> None:
        existing = list(self.evidence_to_certification.get(evidence_id, ()))
        if certification_id not in existing:
            existing.append(certification_id)
            self.evidence_to_certification[evidence_id] = tuple(existing)

    def to_dict(self) -> dict:
        return {
            "sources": {k: v.to_dict() for k, v in self.sources.items()},
            "capabilities": {k: v.to_dict() for k, v in self.capabilities.items()},
            "test_surfaces": {
                k: v.to_dict() for k, v in self.test_surfaces.items()
            },
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "evidence": {k: v.to_dict() for k, v in self.evidence.items()},
            "certifications": {
                k: v.to_dict() for k, v in self.certifications.items()
            },
            "edges": {
                "source_to_capability": {
                    k: list(v) for k, v in self.source_to_capability.items()
                },
                "capability_to_surface": {
                    k: list(v) for k, v in self.capability_to_surface.items()
                },
                "surface_to_task": {
                    k: list(v) for k, v in self.surface_to_task.items()
                },
                "task_to_evidence": {
                    k: list(v) for k, v in self.task_to_evidence.items()
                },
                "evidence_to_certification": {
                    k: list(v) for k, v in self.evidence_to_certification.items()
                },
            },
        }


# ---------------------------------------------------------------------------
# Identity helpers
# ---------------------------------------------------------------------------

def source_id(path: str) -> str:
    return f"src::{path}"


def capability_id(name: str) -> str:
    return f"cap::{name}"


def surface_id(kind: TestSurfaceKind, path: str) -> str:
    return f"surf::{kind}::{path}"


def task_id(kind: TaskKind, target: str) -> str:
    return f"task::{kind}::{target}"


def evidence_id(kind: EvidenceKind, scope: str, fingerprint: str) -> str:
    return f"ev::{kind}::{scope}::{fingerprint[:12]}"


def certification_id(scope_kind: str, scope_id: str) -> str:
    return f"cert::{scope_kind}::{scope_id}"


def fingerprint_components(parts: tuple[str, ...]) -> str:
    """Stable fingerprint from ordered string parts."""
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()
