#!/usr/bin/env python3
"""Cross-Layer Intelligence Map — DEPRECATED generator shim.

Program 13.2 retired this generator as an architecture authority. The single
source of architectural truth is now
:func:`runtime.foundation.architecture.get_architecture`. This shim delegates
to the canonical generator and additionally writes a legacy-compatible
``cross-layer-map.json`` derived from the canonical data (no phantom
``<engine>.py`` keys, no submodule-as-engine roots).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERATED = PROJECT_ROOT / "runtime" / "generated"
V2_PATH = GENERATED / "cross-layer-map-v2.json"
LEGACY_PATH = GENERATED / "cross-layer-map.json"


def main() -> int:
    print("Cross-Layer Map: delegating to the canonical architecture provider.")
    from runtime.foundation.architecture import cross_layer

    v2_path = cross_layer.save()
    print(f"  Wrote canonical map: {v2_path}")

    chains = cross_layer.load_chains()
    legacy = {}
    for name, chain in chains.items():
        eng = chain.get("engine", "")
        key = eng[:-len("/__init__.py")] if eng.endswith("/__init__.py") else eng
        endpoints = sorted(set(chain.get("endpoints", []) + chain.get("ownedEndpoints", [])))
        legacy[key] = {
            "engine": key,
            "services": list(chain.get("services", [])),
            "routers": list(chain.get("routers", [])),
            "endpoints": endpoints,
            "capabilities": list(chain.get("capabilities", [])),
            "mappers": list(chain.get("mappers", [])),
            "viewModels": list(chain.get("viewModels", [])),
            "pages": list(chain.get("pages", [])),
            "workspace": list(chain.get("workspace", [])),
            "components": list(chain.get("components", [])),
            "graphRenderers": list(chain.get("graphRenderers", [])),
            "tests": list(chain.get("tests", [])),
            "modules": list(chain.get("implementationModules", []) or chain.get("modules", [])),
        }
    LEGACY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEGACY_PATH.write_text(json.dumps(legacy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"  Wrote legacy-compatible map: {LEGACY_PATH} ({len(legacy)} chains)")
    print("  NOTE: cross-layer-map.json is now derived from the canonical provider;")
    print("        the legacy generator is retired (Program 13.2).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
