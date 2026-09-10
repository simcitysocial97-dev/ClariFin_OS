#!/usr/bin/env python3
"""
Phase 5: Engine Normalization Audit.

Classifies every engine by:
  - canonical_style (package | single_file)
  - legacy_style (bool)
  - migration_status (CANONICAL_PACKAGE | CANONICAL_SINGLE_FILE |
                     CANONICAL_SINGLE_FILE_INTERNAL | CANONICAL_PACKAGE_INTERNAL |
                     PARTIAL_MIGRATION | PARKED | ORPHAN_INTERNAL | FACADE)

Reports:
  legacy_engines, partially_migrated_engines, duplicate_engines,
  parked_engines, orphan_engines, facade_engines, implementation_only_modules

DO NOT refactor. Only classify.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path("/home/vasantha/AI-Projects/ClariFin_OS")

# Legacy / parked single-file engines that are NOT canonical packages
# NOTE (Program J): this map is now empty.
#  - behavior_engine.py was deleted; the behaviour_engine/ package migration is
#    complete, so there is no parked legacy file left to report.
#  - cashflow_engine.py.parked no longer exists; cashflow_engine.py is live and
#    backs the household_cashflow capability, so it is a canonical single-file
#    engine (declared in analyze_engine_topology.SINGLE_FILE_ENGINES), not parked.
PARKED: dict[str, dict] = {}
# Namespace facade: engines/__init__.py re-exports balance_engine symbols
FACADE_FILES = {
    "backend/src/engines/__init__.py": "Re-exports balance_engine public API; namespace facade.",
}


def classify(name, e):
    style = e["canonical_style"]
    caps = e["capabilities"]
    has_router = len(e["routers"]) > 0
    has_svc = len(e["services"]) > 0
    if style == "package":
        status = "CANONICAL_PACKAGE" if caps else "CANONICAL_PACKAGE_INTERNAL"
    else:
        if has_router and caps:
            status = "CANONICAL_SINGLE_FILE"
        elif has_router and not caps:
            status = "CANONICAL_SINGLE_FILE_INTERNAL"
        elif not has_router and not has_svc:
            status = "ORPHAN_INTERNAL"
        else:
            status = "CANONICAL_SINGLE_FILE"
    return status


def build():
    topo = json.loads(
        (REPO / "runtime" / "generated" / "engine-topology.json").read_text()
    )
    engines = {}
    legacy, partial, duplicate, parked, orphan, facade, impl_only = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    impl_by_engine = defaultdict(list)

    for name, e in topo["engines"].items():
        status = classify(name, e)
        engines[name] = {
            "canonical_style": e["canonical_style"],
            "legacy_style": e["canonical_style"] == "single_file",
            "migration_status": status,
            "entry_point": e["public_entry_point"],
            "implementation_module_count": e["implementation_module_count"],
            "services": e["services"],
            "routers": e["routers"],
            "repositories": e["repositories"],
            "capabilities": e["capabilities"],
            "tests": e["tests"],
            "evidence": e["evidence"],
        }
        if e["canonical_style"] == "single_file":
            legacy.append(name)
        if not e["capabilities"]:
            # internal (no capability owner) - distinct from orphan
            pass
        if status == "ORPHAN_INTERNAL":
            orphan.append(name)
        for m in e["implementation_modules"]:
            impl_by_engine[name].append(m)
            impl_only.append({"engine": name, "module": m})

    # partial migration: behaviour domain has both legacy + package
    if "behaviour_engine" in topo["engines"] and "behavior_engine" in PARKED:
        engines["behaviour_engine"]["migration_status"] = "CANONICAL_PACKAGE"
        engines["behaviour_engine"]["note"] = (
            "Canonical package exists; legacy "
            "behavior_engine.py still present (partial migration)."
        )
        partial.append(
            {
                "domain": "behaviour",
                "canonical": "backend/src/engines/behaviour_engine/",
                "legacy": PARKED["behavior_engine"]["path"],
                "evidence": "Both behaviour_engine/ package and behavior_engine.py legacy file coexist.",
            }
        )

    # duplicate engines
    # NOTE (Program J): the behaviour duplicate was unconditional and asserted that
    # behavior_engine.py coexists with the behaviour_engine/ package. That file no
    # longer exists, so the duplicate is only reported if the legacy file is still
    # declared as parked.
    if "behavior_engine" in PARKED:
        duplicate.append(
            {
                "domain": "behaviour",
                "engines": [
                    "backend/src/engines/behaviour_engine/ (package)",
                    "backend/src/engines/behavior_engine.py (legacy single-file)",
                ],
                "evidence": "Same domain implemented twice: package engine + legacy single-file facade.",
            }
        )

    # parked
    for name, info in PARKED.items():
        parked.append({"name": name, **info})
        engines[name] = {
            "canonical_style": "single_file",
            "legacy_style": True,
            "migration_status": "PARKED",
            "entry_point": info["path"],
            "replaces": info["replaces"],
            "note": info["note"],
        }

    # facade
    for path, note in FACADE_FILES.items():
        facade.append({"path": path, "note": note})
        engines.setdefault("engines_namespace_facade", {})
        engines["engines_namespace_facade"] = {
            "canonical_style": "package",
            "legacy_style": False,
            "migration_status": "FACADE",
            "entry_point": path,
            "note": note,
        }

    out = {
        "generated_at": datetime.now().isoformat(),
        "engine_count": len(
            [k for k in engines if k not in ("engines_namespace_facade",)]
        ),
        "canonical_architecture": "package-preferred; single-file only for small cohesive engines",
        "engines": engines,
        "report": {
            "legacy_engines": legacy,
            "partially_migrated_engines": partial,
            "duplicate_engines": duplicate,
            "parked_engines": parked,
            "orphan_engines": orphan,
            "facade_engines": facade,
            "implementation_only_modules": impl_only,
            "implementation_only_module_count": len(impl_only),
        },
        "notes": [
            "8 of 12 canonical engines are PACKAGES; 4 are single-file.",
            "Single-file engines kept (balance_engine, cashflow_engine, "
            "ledger_audit_engine, reconciliation_engine) are small/cohesive.",
            "behaviour_engine migration is COMPLETE: the canonical package is the only "
            "implementation; legacy behavior_engine.py, nudge_engine.py and "
            "insight_generator.py were removed and their behaviour now lives in "
            "behaviour_engine/nudges.py and behaviour_engine/insights.py.",
            "cashflow_engine is a canonical single-file engine backing the "
            "household_cashflow capability (previously mis-recorded as parked).",
            "transaction_intelligence, financial_events, financial_intelligence have NO "
            "capability owner (internal engines); they are CANONICAL_PACKAGE_INTERNAL.",
        ],
    }
    (REPO / "runtime" / "generated" / "engine-normalization.json").write_text(
        json.dumps(out, indent=2)
    )
    print("Engine normalization audit complete.")
    print(
        f"  legacy(single_file): {len(legacy)}  partial: {len(partial)}  "
        f"duplicate: {len(duplicate)}  parked: {len(parked)}"
    )
    print(
        f"  orphan: {len(orphan)}  facade: {len(facade)}  impl_modules: {len(impl_only)}"
    )


if __name__ == "__main__":
    build()
