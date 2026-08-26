"""
M9-C42.27 — M27.2 / M27.3 Verification Graph Inventory Builder

Builds the canonical verification graph from authoritative sources:

    1. Backend filesystem scan (engines / services / routers / models)
    2. Backend test surface scan (unit / property / invariant / contract /
       integration / golden / capability / audit / architecture)
    3. Existing verification.yaml (workflows + scripts)
    4. C42.26 capability matrix (14-component population ledger)
    5. Existing component measurement evidence (where present)

The builder does NOT make up relationships. Every edge it adds has a
caller-provided rule with an explicit derivation source. The inventory
emits a JSON artifact capturing the discovered graph + a manifest of
auto-derived vs manually-encoded edges.

Deterministic. Pure filesystem reads + small JSON writes under
runtime/generated/m9-c42.27/.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.graph_model import (  # noqa: E402
    CapabilityLayer,
    CapabilityNode,
    CertificationNode,
    EvidenceNode,
    SourceKind,
    SourceNode,
    TestSurfaceKind,
    TestSurfaceNode,
    VerificationGraph,
    VerificationTaskNode,
    capability_id,
    evidence_id,
    fingerprint_components,
    source_id,
    surface_id,
    task_id,
)


# ---------------------------------------------------------------------------
# File classification — mirrors impact_rules.py but is the inventory's
# canonical truth. C42.27 deliberately duplicates this here so the
# graph builder has a stable local definition independent of the
# planner's rules. Drift between the two is detected by the test suite.
# ---------------------------------------------------------------------------

_TEST_DIRS: dict[Path, TestSurfaceKind] = {
    Path("backend/tests/unit"): "unit",
    Path("backend/tests/properties"): "property",
    Path("backend/tests/invariants"): "invariant",
    Path("backend/tests/contract"): "contract",
    Path("backend/tests/integration"): "integration",
    Path("backend/tests/golden"): "golden",
    Path("backend/tests/capability"): "capability",
    Path("backend/tests/architecture"): "architecture",
    Path("backend/tests/audits"): "audit",
    Path("backend/tests/meta"): "audit",
    Path("runtime/tests"): "runtime",
}


def _classify_source(rel: str) -> tuple[SourceKind, str | None]:
    if rel.startswith("backend/src/engines/"):
        parts = rel.split("/")
        # Check directory segments first (e.g. credit_card_engine/x.py)
        for p in parts:
            if p.endswith("_engine") and p != "engines":
                return "engine", p
        # Check the filename itself (e.g. balance_engine.py, cashflow_engine.py)
        filename = parts[-1]
        if filename.endswith("_engine.py"):
            return "engine", filename[: -len(".py")]
        comp = parts[3] if len(parts) >= 4 else "unknown"
        return "engine", comp
    if rel.startswith("backend/src/services/"):
        parts = rel.split("/")
        return "service", parts[3] if len(parts) >= 4 else "unknown"
    if rel.startswith("backend/src/routers/"):
        parts = rel.split("/")
        return "router", parts[3] if len(parts) >= 4 else "unknown"
    if rel.startswith("backend/src/models/") or rel.startswith(
        "backend/src/core/dtos/"
    ):
        return "model", None
    if rel.startswith("backend/src/core/"):
        return "core", None
    if rel.startswith("backend/src/common/"):
        return "common", None
    if rel.startswith("backend/tests/"):
        if rel.startswith("backend/tests/generated/"):
            return "other", None
        return "test", None
    if rel.startswith("runtime/foundation/verification/"):
        return "runtime", None
    if rel.startswith("runtime/"):
        return "runtime", None
    if rel.startswith("frontend/"):
        return "frontend", None
    if rel.startswith("backend/") and rel.endswith((".toml", ".cfg", ".coveragerc")):
        return "config", None
    return "other", None


def _classify_surface(rel: str) -> TestSurfaceKind | None:
    p = Path(rel)
    for prefix, kind in _TEST_DIRS.items():
        if p.is_relative_to(prefix):
            return kind
    return None


def _fingerprint(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Source walk
# ---------------------------------------------------------------------------

def _iter_python(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                yield Path(dirpath) / f


def _walk_backend() -> tuple[list[SourceNode], list[TestSurfaceNode]]:
    sources: list[SourceNode] = []
    surfaces: list[TestSurfaceNode] = []
    backend = REPO_ROOT / "backend"
    if not backend.exists():
        return sources, surfaces

    # Production sources — engines, services, routers, models, core,
    # common. The walker also picks up core_domain_money and
    # common_calculations which are not in engines/ but are part of
    # the C42.26 component matrix.
    prod_roots = [
        backend / "src" / "engines",
        backend / "src" / "services",
        backend / "src" / "routers",
        backend / "src" / "models",
        backend / "src" / "core",
        backend / "src" / "common",
    ]
    for root in prod_roots:
        for f in _iter_python(root):
            rel = f.relative_to(REPO_ROOT).as_posix()
            kind, comp = _classify_source(rel)
            # Map non-engine core/common files to their C42.26
            # component names so the population linkage is intact.
            if kind == "core" and rel.endswith("domain/money.py"):
                comp = "core_domain_money"
            elif kind == "common" and rel.endswith("calculations.py"):
                comp = "common_calculations"
            sources.append(
                SourceNode(
                    id=source_id(rel),
                    path=rel,
                    kind=kind,
                    component=comp,
                    fingerprint=_fingerprint(f),
                )
            )

    # Test surfaces
    tests_root = backend / "tests"
    for dirpath, _dirs, files in os.walk(tests_root):
        py_files = [f for f in files if f.endswith(".py")]
        if not py_files:
            continue
        rel_dir = Path(dirpath).relative_to(REPO_ROOT)
        # Walk up to find the closest classified prefix
        kind: TestSurfaceKind | None = None
        for prefix, k in _TEST_DIRS.items():
            if rel_dir.is_relative_to(prefix):
                kind = k
                break
        if kind is None:
            continue
        # Exclude generated subdir
        if rel_dir.is_relative_to(Path("backend/tests/generated")):
            continue
        rel_path = rel_dir.as_posix()
        test_file_ids = []
        for f in py_files:
            test_rel = (rel_dir / f).as_posix()
            test_file_ids.append(source_id(test_rel))
        surfaces.append(
            TestSurfaceNode(
                id=surface_id(kind, rel_path),
                path=rel_path,
                kind=kind,
                test_file_ids=tuple(test_file_ids),
            )
        )
        # Also add the test files as SourceNodes so they're discoverable.
        for f in py_files:
            test_rel = (rel_dir / f).as_posix()
            sources.append(
                SourceNode(
                    id=source_id(test_rel),
                    path=test_rel,
                    kind="test",
                    component=None,
                    fingerprint=_fingerprint(REPO_ROOT / test_rel),
                )
            )

    return sources, surfaces


# ---------------------------------------------------------------------------
# Capabilities — derived from the C42.26 component matrix and the engine
# directory listing. This is a *manually encoded* mapping for the
# intelligence layer, and an *auto-derived* mapping for engines
# (1:1 engine name -> capability).
# ---------------------------------------------------------------------------

ENGINE_TO_CAPABILITY: dict[str, str] = {
    "credit_card": "credit-card-risk",
    "account": "account-management",
    "loan": "loan-management",
    "reconciliation": "reconciliation",
    "behaviour": "behaviour-analytics",
    "balance": "balance-engine",
    "ledger_audit": "ledger-audit",
    "cashflow": "cashflow",
    "financial_events": "financial-events",
    "common_calculations": "common-calculations",
    "recommendation": "recommendation",
    "transaction_intelligence": "transaction-intelligence",
    "financial_intelligence": "financial-intelligence",
    # Aliases from C42.26 component matrix
    "core_domain_money": "core-domain-money",
}


INTELLIGENCE_CAPABILITIES = {
    "transaction-intelligence",
    "financial-intelligence",
}


def _build_capabilities(components: list[str]) -> list[CapabilityNode]:
    out: list[CapabilityNode] = []
    for comp in components:
        if not isinstance(comp, str):
            continue
        cap = ENGINE_TO_CAPABILITY.get(comp, comp.replace("_", "-"))
        layer: CapabilityLayer = (
            "intelligence" if cap in INTELLIGENCE_CAPABILITIES else "domain"
        )
        out.append(
            CapabilityNode(
                id=capability_id(cap),
                name=cap,
                layer=layer,
                description=f"Capability derived from component '{comp}'",
            )
        )
    return out


# ---------------------------------------------------------------------------
# Workflows / tasks from verification.yaml
# ---------------------------------------------------------------------------

def _read_verification_config() -> dict:
    p = REPO_ROOT / "runtime" / "foundation" / "verification" / "verification.yaml"
    if not p.exists():
        return {}
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return {}
    return yaml.safe_load(p.read_text()) or {}


def _build_tasks() -> list[VerificationTaskNode]:
    cfg = _read_verification_config()
    workflows = cfg.get("workflows", {}) or {}
    out: list[VerificationTaskNode] = []
    for wf_id, wf in workflows.items():
        kind = wf.get("category", "capability")
        if kind not in {
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
        }:
            # map category names -> task kind
            kind = {
                "capability": "unit",
                "contract_frontend": "contract",
                "architectural": "unit",
                "migration": "unit",
            }.get(kind, "unit")
        out.append(
            VerificationTaskNode(
                id=task_id(kind, wf_id),
                kind=kind,  # type: ignore[arg-type]
                command=wf.get("command"),
                script=None,
                description=wf.get("description", ""),
                capability_ids=tuple(
                    capability_id(c) for c in (wf.get("capabilities") or [])
                ),
                estimated_duration_seconds=int(
                    wf.get("estimated_duration_seconds", 0) or 0
                ),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _read_c42_26_components() -> list[str]:
    matrix = (
        REPO_ROOT
        / "runtime"
        / "generated"
        / "m9-c42.26"
        / "m9-c42.26-component-matrix.json"
    )
    if not matrix.exists():
        return []
    try:
        data = json.loads(matrix.read_text())
    except json.JSONDecodeError:
        return []
    raw = data.get("components", []) or []
    names: list[str] = []
    for c in raw:
        if isinstance(c, dict):
            n = c.get("component") or c.get("name")
            if n:
                names.append(n)
        elif isinstance(c, str):
            names.append(c)
    return names


def build_graph() -> tuple[VerificationGraph, dict]:
    """Build the canonical verification graph + derivation manifest."""
    g = VerificationGraph()
    manifest: dict = {
        "auto_derived": {
            "source_from_path": 0,
            "test_surface_from_path": 0,
            "capability_from_engine_dir": 0,
            "source_to_capability_from_engine": 0,
        },
        "manually_encoded": {
            "capability_matrix_components": [],
            "intelligence_capabilities": list(INTELLIGENCE_CAPABILITIES),
            "engine_to_capability_aliases": list(ENGINE_TO_CAPABILITY.keys()),
        },
        "inconsistencies": [],
    }

    # 1. Walk backend
    sources, surfaces = _walk_backend()
    for s in sources:
        g.add_source(s)
        manifest["auto_derived"]["source_from_path"] += 1
    for t in surfaces:
        g.add_test_surface(t)
        manifest["auto_derived"]["test_surface_from_path"] += 1

    # 2. Build capabilities
    c42_26_components = _read_c42_26_components()
    manifest["manually_encoded"]["capability_matrix_components"] = c42_26_components
    capabilities = _build_capabilities(c42_26_components)
    for c in capabilities:
        g.add_capability(c)
        manifest["auto_derived"]["capability_from_engine_dir"] += 1

    # 3. Build tasks
    tasks = _build_tasks()
    for t in tasks:
        g.add_task(t)

    # 4. Link source -> capability for engine files
    for src in g.sources.values():
        if src.component is None:
            continue
        if src.kind in ("engine", "core", "common"):
            # The C42.26 component matrix uses full names
            # (e.g. "credit_card_engine"). The capability list is
            # built from those exact names. We prefer the direct
            # full-name match (which is in `g.capabilities`); we
            # only fall back to ENGINE_TO_CAPABILITY for short-name
            # compatibility if the direct match fails.
            full = src.component
            direct = full.replace("_", "-")
            short = full[: -len("_engine")] if full.endswith("_engine") else full
            candidates = [direct, ENGINE_TO_CAPABILITY.get(full)]
            short_mapped = ENGINE_TO_CAPABILITY.get(short)
            if short_mapped is not None:
                candidates.append(short_mapped)
            cap_name = next(
                (c for c in candidates if c and capability_id(c) in g.capabilities),
                None,
            )
            if cap_name is None:
                cap_name = direct
            cap = capability_id(cap_name)
            if cap in g.capabilities:
                g.link_source_capability(src.id, cap)
                manifest["auto_derived"][
                    "source_to_capability_from_engine"
                ] += 1

    # 5. Link capability -> test surface (coarse: all unit + integration
    #    surfaces apply to every capability unless restricted). This is
    #    the level at which a C42.24-style drift can hide, so we also
    #    expose `link_inventory` for deterministic scenarios.
    for cap_id_, cap in g.capabilities.items():
        for surface in g.test_surfaces.values():
            if surface.kind in {"unit", "integration", "property", "invariant"}:
                g.link_capability_surface(cap_id_, surface.id)

    # 6. Link surface -> task (from verification.yaml)
    for task in g.tasks.values():
        for cap in task.capability_ids:
            for surface in g.test_surfaces.values():
                if surface.kind == task.kind:
                    g.link_surface_task(surface.id, task.id)

    return g, manifest


def main() -> int:
    g, manifest = build_graph()

    out_dir = REPO_ROOT / "runtime" / "generated" / "m9-c42.27"
    out_dir.mkdir(parents=True, exist_ok=True)

    graph_path = out_dir / "m9-c42.27-graph-inventory.json"
    manifest_path = out_dir / "m9-c42.27-graph-derivation-manifest.json"

    payload = {
        "title": "M9-C42.27 — Verification Graph Inventory (M27.2)",
        "generated_at": datetime.now(UTC).isoformat(),
        "graph": g.to_dict(),
        "summary": {
            "sources": len(g.sources),
            "capabilities": len(g.capabilities),
            "test_surfaces": len(g.test_surfaces),
            "tasks": len(g.tasks),
            "edges_source_to_capability": sum(
                len(v) for v in g.source_to_capability.values()
            ),
            "edges_capability_to_surface": sum(
                len(v) for v in g.capability_to_surface.values()
            ),
            "edges_surface_to_task": sum(
                len(v) for v in g.surface_to_task.values()
            ),
        },
    }
    graph_path.write_text(json.dumps(payload, indent=2))
    manifest_path.write_text(
        json.dumps(
            {
                "title": "M9-C42.27 — Graph Derivation Manifest",
                "generated_at": datetime.now(UTC).isoformat(),
                **manifest,
            },
            indent=2,
        )
    )

    print(f"Graph inventory: {graph_path.relative_to(REPO_ROOT)}")
    print(f"Derivation manifest: {manifest_path.relative_to(REPO_ROOT)}")
    print(
        "Counts:",
        f"sources={len(g.sources)} capabilities={len(g.capabilities)}",
        f"surfaces={len(g.test_surfaces)} tasks={len(g.tasks)}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
