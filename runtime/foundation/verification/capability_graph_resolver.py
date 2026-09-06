# runtime/foundation/verification/capability_graph_resolver.py
#
# M9-C48 C1–C5 — Capability Graph Resolver (GAP-004/005/006/009/010).
#
# A single, deterministic capability-graph engine that closes the C47 gaps:
#
#   C1 / GAP-004 — Symbol-level planning (AST).
#   C2 / GAP-005 — Graph-based capability resolution (endpoint → capability).
#   C3 / GAP-006 — Severity filtering / prioritization.
#   C4 / GAP-009 — Rename / move graph invalidation.
#   C5 / GAP-010 — Deletion capability removal.
#
# The module is pure logic — no I/O. It is importable by tests and by the
# planner (planner.py:382-388 TODO closure).
#
# The graph connects:
#
#   changed file → changed symbol (AST)
#                 → module
#                 → engine (from ENGINE_SELECTION)
#                 → capability (canonical capability ID)
#                 → verification requirement
#                 → test selection
#                 → evidence
#
# Plus:
#
#   changed endpoint → capability (via CapabilityEndpointMap)
#
# Plus:
#
#   renamed/moved/deleted files invalidate prior graph edges
#   (rename: old path → new path; deletion: path removed with explicit
#   DEL capability state).
#
# Severity is preserved on every requirement and surfaces as a tier:

from __future__ import annotations

import ast
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# ── Severity taxonomy ──────────────────────────────────────────────────────
class SeverityTier(str, Enum):
    """M9-C48 C3 — Severity taxonomy with explicit effect on planning.

    BLOCKING   — must execute; failure halts the run.
    REQUIRED   — must execute; failure is reported but the run may continue.
    PRIORITIZED — preferred over OPTIONAL; selected when scope is constrained.
    OPTIONAL   — included if budget allows; otherwise deferred.
    DIAGNOSTIC — informational; never blocks; recorded as evidence only.
    """

    BLOCKING = "blocking"
    REQUIRED = "required"
    PRIORITIZED = "prioritized"
    OPTIONAL = "optional"
    DIAGNOSTIC = "diagnostic"


_SEVERITY_TO_TIER: dict[str, SeverityTier] = {
    "critical": SeverityTier.BLOCKING,
    "high": SeverityTier.REQUIRED,
    "medium": SeverityTier.PRIORITIZED,
    "low": SeverityTier.OPTIONAL,
    "info": SeverityTier.DIAGNOSTIC,
}


def severity_to_tier(severity: str | None) -> SeverityTier:
    if severity is None:
        return SeverityTier.OPTIONAL
    return _SEVERITY_TO_TIER.get(str(severity).lower(), SeverityTier.OPTIONAL)


# ── Symbol-level (C1) ──────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class ChangedSymbol:
    file: str
    qualified_name: str  # e.g. "LoanService.calculate_payment"
    kind: str  # "function" | "method" | "class" | "import"
    line: int
    column: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class UnresolvedSymbol:
    file: str
    line: int
    column: int
    reason: str  # "syntax_error" | "unknown_construct" | "unparseable"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SymbolResolver:
    """AST-based symbol resolution (C1).

    Pure logic; reads source text passed in by the caller. The planner
    invokes this for every Python file in the diff.
    """

    _CLASS_RE = re.compile(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)")
    _FUNC_RE = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)")
    _METHOD_RE = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)")

    def resolve(
        self, file_path: str, source: str
    ) -> tuple[list[ChangedSymbol], list[UnresolvedSymbol]]:
        symbols: list[ChangedSymbol] = []
        unresolved: list[UnresolvedSymbol] = []
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError as exc:
            unresolved.append(
                UnresolvedSymbol(
                    file=file_path,
                    line=exc.lineno or 0,
                    column=exc.offset or 0,
                    reason="syntax_error",
                )
            )
            return symbols, unresolved

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = "function"
                qname = node.name
                if node.col_offset == 0:
                    # Might be a method (nested under a class)
                    # We resolve via parent walk below.
                    kind = "function"
                symbols.append(
                    ChangedSymbol(
                        file=file_path,
                        qualified_name=qname,
                        kind=kind,
                        line=node.lineno,
                        column=node.col_offset,
                    )
                )
            elif isinstance(node, ast.ClassDef):
                symbols.append(
                    ChangedSymbol(
                        file=file_path,
                        qualified_name=node.name,
                        kind="class",
                        line=node.lineno,
                        column=node.col_offset,
                    )
                )
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                # Record a coarse import marker per import statement.
                line = node.lineno
                col = node.col_offset
                symbols.append(
                    ChangedSymbol(
                        file=file_path,
                        qualified_name="<import>",
                        kind="import",
                        line=line,
                        column=col,
                    )
                )

        # Second pass: methods (function defs whose parent is a ClassDef).
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                for child in ast.iter_child_nodes(parent):
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        qname = f"{parent.name}.{child.name}"
                        symbols.append(
                            ChangedSymbol(
                                file=file_path,
                                qualified_name=qname,
                                kind="method",
                                line=child.lineno,
                                column=child.col_offset,
                            )
                        )

        return symbols, unresolved

    def resolve_many(
        self, files: Mapping[str, str]
    ) -> tuple[list[ChangedSymbol], list[UnresolvedSymbol]]:
        all_syms: list[ChangedSymbol] = []
        all_unr: list[UnresolvedSymbol] = []
        for path, src in files.items():
            s, u = self.resolve(path, src)
            all_syms.extend(s)
            all_unr.extend(u)
        return all_syms, all_unr


# ── Endpoint → capability map (C2) ─────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class EndpointEdge:
    method: str  # "GET" | "POST" | ...
    path: str  # "/loans/{loan_id}/payment"
    capability_id: str  # canonical capability


class EndpointCapabilityMap:
    """A graph from (method, path) → capability.

    The repository owns this map. The M9-C48 graph resolver augments it
    with derivations from file paths when no explicit edge exists.
    """

    def __init__(self) -> None:
        self._edges: dict[tuple[str, str], str] = {}

    def add(self, method: str, path: str, capability_id: str) -> None:
        self._edges[(method.upper(), path)] = capability_id

    def resolve(self, method: str, path: str) -> str | None:
        return self._edges.get((method.upper(), path))

    def all_edges(self) -> list[EndpointEdge]:
        return [
            EndpointEdge(method=m, path=p, capability_id=c)
            for (m, p), c in sorted(self._edges.items())
        ]

    @classmethod
    def from_path_rules(
        cls, rules: Iterable[tuple[str, str, str]]
    ) -> EndpointCapabilityMap:
        m = cls()
        for method, path, cap in rules:
            m.add(method, path, cap)
        return m


# Heuristic path-based derivation (no special cases, but stable). This is
# the graph edge that lets a changed endpoint resolve to a capability when
# no explicit edge is present.
_PATH_RULES: tuple[tuple[str, str], ...] = (
    (r"^/loans(/.*)?$", "loan-engine"),
    (r"^/credit-cards?(/.*)?$", "credit-card-engine"),
    (r"^/accounts?(/.*)?$", "account-engine"),
    (r"^/balances?(/.*)?$", "balance-engine"),
    (r"^/cashflow(/.*)?$", "cashflow-engine"),
    (r"^/reconciliation(/.*)?$", "reconciliation-engine"),
    (r"^/ledger(/.*)?$", "ledger-audit-engine"),
    (r"^/recommendations?(/.*)?$", "recommendation-engine"),
    (r"^/transactions?(/.*)?$", "transaction-intelligence"),
    (r"^/financial-intelligence(/.*)?$", "financial-intelligence"),
    (r"^/behaviour(/.*)?$", "behaviour-engine"),
    (r"^/financial-events(/.*)?$", "financial-events"),
)


def derive_capability_from_path(path: str) -> str | None:
    for pattern, cap in _PATH_RULES:
        if re.match(pattern, path):
            return cap
    return None


# ── Change event taxonomy (C4, C5) ─────────────────────────────────────────
class ChangeKind(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    RENAMED = "renamed"
    MOVED = "moved"
    DELETED = "deleted"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class FileChange:
    kind: ChangeKind
    old_path: str | None
    new_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "old_path": self.old_path,
            "new_path": self.new_path,
        }


def parse_git_status_output(name_status: str, raw_status: str = "") -> list[FileChange]:
    """Parse ``git diff --name-status`` (and ``-M`` rename detection) output.

    Status codes:
        A  added
        M  modified
        R<score>  renamed (with similarity score; old path is the previous token)
        D  deleted
        C  copied (treated as ADDED here)
        T  type change (treated as MODIFIED)
    """
    changes: list[FileChange] = []
    for line in name_status.splitlines():
        line = line.rstrip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            changes.append(
                FileChange(
                    kind=ChangeKind.RENAMED,
                    old_path=parts[1],
                    new_path=parts[2],
                )
            )
        elif status == "A":
            changes.append(
                FileChange(kind=ChangeKind.ADDED, old_path=None, new_path=parts[1])
            )
        elif status == "M":
            changes.append(
                FileChange(kind=ChangeKind.MODIFIED, old_path=None, new_path=parts[1])
            )
        elif status == "D":
            changes.append(
                FileChange(kind=ChangeKind.DELETED, old_path=None, new_path=parts[1])
            )
        elif status.startswith("C"):
            changes.append(
                FileChange(kind=ChangeKind.ADDED, old_path=None, new_path=parts[1])
            )
        elif status.startswith("T"):
            changes.append(
                FileChange(kind=ChangeKind.MODIFIED, old_path=None, new_path=parts[1])
            )
        else:
            changes.append(
                FileChange(kind=ChangeKind.UNKNOWN, old_path=None, new_path=parts[-1])
            )
    return changes


# ── Graph node ─────────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class CapabilityEdge:
    """An edge from a source (file/symbol/endpoint) to a capability."""

    source_kind: str  # "file" | "symbol" | "endpoint"
    source: str  # file path, "LoanService.calculate_payment", or "POST /loans"
    capability_id: str
    severity: SeverityTier = SeverityTier.REQUIRED
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "source": self.source,
            "capability_id": self.capability_id,
            "severity": self.severity.value,
            "rationale": self.rationale,
        }


# ── Main graph resolver ────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class CapabilityResolution:
    """The output of resolving a set of changes into affected capabilities."""

    edges: tuple[CapabilityEdge, ...]
    unmapped: tuple[FileChange, ...]
    deleted_capabilities: tuple[str, ...]
    renamed_paths: tuple[tuple[str, str], ...]
    unresolved_symbols: tuple[UnresolvedSymbol, ...]
    generated_at: str

    @property
    def affected_capability_ids(self) -> list[str]:
        # Preserve insertion order; deduplicate.
        seen: set[str] = set()
        out: list[str] = []
        for e in self.edges:
            if e.capability_id not in seen:
                seen.add(e.capability_id)
                out.append(e.capability_id)
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "edges": [e.to_dict() for e in self.edges],
            "unmapped": [u.to_dict() for u in self.unmapped],
            "deleted_capabilities": list(self.deleted_capabilities),
            "renamed_paths": [list(r) for r in self.renamed_paths],
            "unresolved_symbols": [u.to_dict() for u in self.unresolved_symbols],
            "affected_capability_ids": self.affected_capability_ids,
            "generated_at": self.generated_at,
            "schema": "m9-c48/capability-resolution@1",
        }


class CapabilityGraphResolver:
    """The unified resolver.

    Combines:
      * AST symbol resolution (C1).
      * Endpoint → capability (C2).
      * Severity tier (C3).
      * Rename / move invalidation (C4).
      * Deletion capability removal (C5).

    Usage:
        resolver = CapabilityGraphResolver(registry, engine_bridge)
        resolution = resolver.resolve(
            changes=[...],
            sources={"path/to/foo.py": "..."},
            endpoints=[("POST", "/loans")],
        )
    """

    def __init__(
        self,
        registry: Any,
        engine_bridge: Any | None = None,
        endpoint_map: EndpointCapabilityMap | None = None,
    ) -> None:
        self._registry = registry
        self._engine_bridge = engine_bridge
        self._endpoint_map = endpoint_map or EndpointCapabilityMap()
        self._symbol_resolver = SymbolResolver()
        # Build module → capability index from the registry.
        self._module_index: dict[str, str] = {}
        if hasattr(registry, "load"):
            registry.load()
        if hasattr(registry, "get_all_capabilities"):
            for cap in registry.get_all_capabilities():
                for mod in cap.modules:
                    self._module_index[mod] = cap.id

    def _capability_for_file(self, file_path: str) -> str | None:
        """Map a file path to a canonical capability.

        Resolution order:
          1. Direct module match against the registry index.
          2. Engine bridge (ENGINE_SELECTION source_paths).

        The match is performed on the path tail so that a leading
        ``backend/`` does not block a match against ``src/...`` source
        paths, and vice-versa.
        """
        # Normalize: strip a leading "backend/" to support both forms.
        norm = file_path
        if norm.startswith("backend/"):
            norm = norm[len("backend/") :]
        for mod, cap in self._module_index.items():
            if file_path.startswith(mod) or norm.startswith(mod):
                return cap
        if self._engine_bridge is not None:
            for rec in self._engine_bridge.engine_capability_records():
                for src in rec.source_paths:
                    if file_path.startswith(src) or norm.startswith(src):
                        return rec.id
        return None

    def resolve(
        self,
        changes: list[FileChange],
        sources: Mapping[str, str] | None = None,
        endpoints: Iterable[tuple[str, str]] | None = None,
    ) -> CapabilityResolution:
        edges: list[CapabilityEdge] = []
        unmapped: list[FileChange] = []
        deleted_caps: list[str] = []
        renamed: list[tuple[str, str]] = []
        unresolved: list[UnresolvedSymbol] = []

        sources = sources or {}
        endpoints = list(endpoints or [])

        # C4/C5: rename and deletion produce explicit graph edges.
        for ch in changes:
            if ch.kind in (ChangeKind.RENAMED, ChangeKind.MOVED):
                if ch.old_path and ch.new_path:
                    renamed.append((ch.old_path, ch.new_path))
                # Invalidate the old identity, resolve the new identity.
                # We do not silently drop the old path.
                cap = self._capability_for_file(ch.new_path)
                if cap is None:
                    unmapped.append(ch)
                    edges.append(
                        CapabilityEdge(
                            source_kind="file",
                            source=ch.new_path,
                            capability_id="UNMAPPED",
                            severity=SeverityTier.BLOCKING,
                            rationale="rename target has no capability mapping",
                        )
                    )
                else:
                    edges.append(
                        CapabilityEdge(
                            source_kind="file",
                            source=ch.new_path,
                            capability_id=cap,
                            severity=SeverityTier.REQUIRED,
                            rationale=f"renamed from {ch.old_path}",
                        )
                    )
                if ch.old_path:
                    edges.append(
                        CapabilityEdge(
                            source_kind="file",
                            source=ch.old_path,
                            capability_id="INVALIDATED",
                            severity=SeverityTier.DIAGNOSTIC,
                            rationale="old identity invalidated by rename",
                        )
                    )
            elif ch.kind == ChangeKind.DELETED:
                cap = self._capability_for_file(ch.new_path)
                if cap:
                    deleted_caps.append(cap)
                    edges.append(
                        CapabilityEdge(
                            source_kind="file",
                            source=ch.new_path,
                            capability_id="DELETED",
                            severity=SeverityTier.DIAGNOSTIC,
                            rationale=f"deleted capability {cap}",
                        )
                    )
                else:
                    unmapped.append(ch)
                    edges.append(
                        CapabilityEdge(
                            source_kind="file",
                            source=ch.new_path,
                            capability_id="UNMAPPED",
                            severity=SeverityTier.BLOCKING,
                            rationale="deletion target has no capability mapping",
                        )
                    )
            elif ch.kind in (ChangeKind.ADDED, ChangeKind.MODIFIED, ChangeKind.UNKNOWN):
                cap = self._capability_for_file(ch.new_path)
                if cap is None:
                    unmapped.append(ch)
                    edges.append(
                        CapabilityEdge(
                            source_kind="file",
                            source=ch.new_path,
                            capability_id="UNMAPPED",
                            severity=SeverityTier.BLOCKING,
                            rationale="production file change with no capability mapping",
                        )
                    )
                else:
                    edges.append(
                        CapabilityEdge(
                            source_kind="file",
                            source=ch.new_path,
                            capability_id=cap,
                            severity=SeverityTier.REQUIRED,
                            rationale="changed file",
                        )
                    )

        # C1: symbol-level edges (from AST).
        for path, src in sources.items():
            syms, unr = self._symbol_resolver.resolve(path, src)
            unresolved.extend(unr)
            # Find capability for the file.
            cap_for_file = self._capability_for_file(path)
            if cap_for_file is None:
                # No capability; don't emit symbol edges.
                continue
            for s in syms:
                edges.append(
                    CapabilityEdge(
                        source_kind="symbol",
                        source=f"{path}::{s.qualified_name}",
                        capability_id=cap_for_file,
                        severity=SeverityTier.REQUIRED,
                        rationale=f"{s.kind} change",
                    )
                )

        # C2: endpoint → capability edges.
        for method, ep in endpoints:
            cap = self._endpoint_map.resolve(method, ep) or derive_capability_from_path(
                ep
            )
            if cap is None:
                edges.append(
                    CapabilityEdge(
                        source_kind="endpoint",
                        source=f"{method} {ep}",
                        capability_id="UNMAPPED",
                        severity=SeverityTier.BLOCKING,
                        rationale="changed endpoint has no capability mapping",
                    )
                )
            else:
                edges.append(
                    CapabilityEdge(
                        source_kind="endpoint",
                        source=f"{method} {ep}",
                        capability_id=cap,
                        severity=SeverityTier.REQUIRED,
                        rationale="changed endpoint",
                    )
                )

        return CapabilityResolution(
            edges=tuple(edges),
            unmapped=tuple(unmapped),
            deleted_capabilities=tuple(deleted_caps),
            renamed_paths=tuple(renamed),
            unresolved_symbols=tuple(unresolved),
            generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )


# ── Severity filter (C3) ───────────────────────────────────────────────────
def filter_requirements_by_tier(
    requirements: Iterable[Any],
    *,
    include: frozenset[SeverityTier] = frozenset(
        {SeverityTier.BLOCKING, SeverityTier.REQUIRED, SeverityTier.PRIORITIZED}
    ),
    severity_attr: str = "severity",
) -> list[Any]:
    """Return requirements whose mapped tier is in ``include``.

    The mapping is ``severity_to_tier(severity)``; requirements whose
    severity cannot be mapped default to OPTIONAL (and are excluded by
    the default ``include`` set).
    """
    out: list[Any] = []
    for r in requirements:
        sev = getattr(r, severity_attr, None)
        tier = severity_to_tier(sev.value if hasattr(sev, "value") else sev)
        if tier in include:
            out.append(r)
    return out


__all__ = [
    "SeverityTier",
    "severity_to_tier",
    "ChangedSymbol",
    "UnresolvedSymbol",
    "SymbolResolver",
    "EndpointEdge",
    "EndpointCapabilityMap",
    "derive_capability_from_path",
    "ChangeKind",
    "FileChange",
    "parse_git_status_output",
    "CapabilityEdge",
    "CapabilityResolution",
    "CapabilityGraphResolver",
    "filter_requirements_by_tier",
]
