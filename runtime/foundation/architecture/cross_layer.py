"""Canonical cross-layer map generator (v2) — Program 13.2, Phase 3.

Replaces ``tools/generators/build_cross_layer_map.py``.

The legacy generator assumed ``Python file == Engine``. It therefore:

* invented 7 ``backend/src/engines/<pkg>.py`` keys for engines that are
  PACKAGES (the files do not exist), and
* registered every engine submodule as its own "engine" chain, duplicating
  33 endpoints and inflating the test-coverage denominator.

The canonical generator emits exactly ONE chain per canonical engine, with
implementation modules as CHILDREN:

    Loan Engine
        foreclosure.py
        amortization.py
        emi.py
        metrics.py

Endpoints are owned by Routers (the HTTP layer), so the map also carries an
explicit ``endpointOwnership`` section where each endpoint resolves to exactly
one router. An endpoint reachable from several engines is legitimate execution
reachability, never duplicate ownership.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.foundation.architecture.models import Architecture
from runtime.foundation.architecture.provider import GENERATED_DIR, get_architecture

OUTPUT_NAME = "cross-layer-map-v2.json"
SCHEMA = "cross-layer-map-v2"

LEGACY_PHANTOM_ENGINE_KEYS = (
    "backend/src/engines/account_engine.py",
    "backend/src/engines/behaviour_engine.py",
    "backend/src/engines/credit_card_engine.py",
    "backend/src/engines/financial_events.py",
    "backend/src/engines/financial_intelligence.py",
    "backend/src/engines/recommendation_engine.py",
    "backend/src/engines/transaction_intelligence.py",
)


def _chain_for_engine(arch: Architecture, name: str) -> dict[str, Any]:
    engine = arch.engines[name]

    capabilities = sorted(engine.capabilities)
    workspaces: set[str] = set()
    components: set[str] = set()
    pages: set[str] = set()
    mappers: set[str] = set()
    view_models: set[str] = set()
    graph_renderers: set[str] = set()

    for cap_name in capabilities:
        cap = arch.capabilities.get(cap_name)
        if cap is None:
            continue
        for ws_name in cap.workspaces:
            ws = arch.workspaces.get(ws_name)
            if ws is None:
                continue
            workspaces.add(ws_name)
            if ws.path:
                pages.add(ws.path)
            for comp in ws.components:
                components.add(comp)
                if "/graph/" in comp or comp.endswith("graph-renderer"):
                    graph_renderers.add(f"frontend/{comp}.tsx")
        if cap.path:
            cap_module = _inventory_imports(arch, cap.path)
            for imp in cap_module:
                if "/mappers/" in imp:
                    mappers.add(imp.removeprefix("@/"))
                if "view-model" in imp or imp.endswith("ViewModel"):
                    view_models.add(imp.removeprefix("@/"))

    owned_endpoints = sorted(
        signature
        for signature, endpoint in arch.endpoints.items()
        if endpoint.router in engine.routers and len(endpoint.engines) == 1
    )

    return {
        "id": engine.id,
        "engine": engine.path,
        "engineName": engine.name,
        "engineId": engine.id,
        "engineStyle": engine.style,
        "entryPoint": engine.entry_point,
        "internal": engine.internal,
        "migrationStatus": engine.migration_status,
        "implementationModules": list(engine.implementation_modules),
        "detectors": list(engine.detectors),
        "services": list(engine.services),
        "routers": list(engine.routers),
        "repositories": list(engine.repositories),
        "endpoints": list(engine.endpoints),
        "ownedEndpoints": owned_endpoints,
        "capabilities": capabilities,
        "workspace": sorted(workspaces),
        "pages": sorted(pages),
        "components": sorted(components),
        "graphRenderers": sorted(graph_renderers),
        "mappers": sorted(mappers),
        "viewModels": sorted(view_models),
        "tests": list(engine.tests),
        "artifacts": list(engine.artifacts),
    }


def _inventory_imports(arch: Architecture, path: str) -> list[str]:
    """Imports recorded for a frontend module by the discovery pipeline."""
    inventory_path = GENERATED_DIR / "architecture-inventory.json"
    cache = getattr(_inventory_imports, "_cache", None)
    if cache is None:
        try:
            data = json.loads(inventory_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {"modules": []}
        cache = {m["path"]: m.get("imports", []) for m in data.get("modules", [])}
        _inventory_imports._cache = cache  # type: ignore[attr-defined]
    return cache.get(path, [])


def build_cross_layer_map_v2(arch: Architecture | None = None) -> dict[str, Any]:
    architecture = arch or get_architecture()

    chains = {
        engine.id: _chain_for_engine(architecture, name)
        for name, engine in sorted(architecture.engines.items())
    }

    endpoint_ownership = {
        signature: {
            "router": endpoint.router,
            "method": endpoint.method,
            "path": endpoint.path,
            "executedByEngines": list(endpoint.engines),
            "capabilities": list(endpoint.capabilities),
        }
        for signature, endpoint in sorted(architecture.endpoints.items())
    }

    demoted = sorted(
        [
            {"module": path, "ownedByEngine": mod.engine, "wasTreatedAsEngine": True}
            for path, mod in architecture.engine_modules.items()
        ]
        + [
            {"module": path, "ownedByEngine": det.engine, "wasTreatedAsEngine": True}
            for path, det in architecture.detectors.items()
        ],
        key=lambda d: d["module"],
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema": SCHEMA,
        "generator": "runtime.foundation.architecture.cross_layer.build_cross_layer_map_v2",
        "basis": [f"runtime/generated/{n}" for n in architecture.source_artifacts],
        "principle": (
            "One chain per canonical engine. Package engines are engines; "
            "implementation modules and detectors are children. Endpoints are "
            "owned by routers."
        ),
        "chain_count": len(chains),
        "chains": chains,
        "endpointOwnership": endpoint_ownership,
        "facades": {
            path: facade.to_dict() for path, facade in sorted(architecture.facades.items())
        },
        "phantomEngineKeysRemoved": list(LEGACY_PHANTOM_ENGINE_KEYS),
        "implementationModulesDemoted": demoted,
        "notes": [
            "The legacy map contained 7 phantom '<engine>.py' keys for package engines; "
            "they are removed here.",
            "Implementation modules that the legacy map listed as engines are now children "
            "of their owning engine (implementationModulesDemoted).",
            "'endpoints' on a chain is EXECUTION reachability. 'ownedEndpoints' lists endpoints "
            "whose router is reached by this engine alone. Endpoint OWNERSHIP is the router, "
            "recorded once in endpointOwnership.",
            "Engines with no capability are internal engines; that is expected, not a defect.",
        ],
    }


def save(output_path: Path | None = None, arch: Architecture | None = None) -> Path:
    data = build_cross_layer_map_v2(arch)
    target = output_path or (GENERATED_DIR / OUTPUT_NAME)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return target


def load_map(path: Path | None = None) -> dict[str, Any]:
    """Load the canonical v2 map, generating it on demand."""
    target = path or (GENERATED_DIR / OUTPUT_NAME)
    if not target.exists():
        save(target)
    return json.loads(target.read_text(encoding="utf-8"))


def load_chains(path: Path | None = None) -> dict[str, dict[str, Any]]:
    return load_map(path).get("chains", {})


def normalize_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return chains from either a v2 document or a legacy flat map.

    Legacy flat maps are still accepted so that unit tests and third-party
    fixtures keep working; they are NEVER used as an architecture authority.
    """
    if isinstance(data, dict) and data.get("schema") == SCHEMA:
        return data.get("chains", {})
    return data if isinstance(data, dict) else {}
