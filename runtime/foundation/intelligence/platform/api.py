"""Unified Intelligence API — Program 14.1.

A single internal API that every runtime command must communicate through.

Before 14.0 the runtime had two overlapping "intelligence" implementations:
the legacy ``runtime/foundation/intelligence/{affected,diagnostics,risk,
repair,formatter,models}.py`` modules (filename-based inference, predating the
canonical architecture) and the canonical ``platform`` layer built in 14.0.

Constitutional rule (Programs 13.x-14.1): **no command may implement its own
algorithm**. Every service here is a thin composition over the canonical
``platform`` modules, which consume only
:func:`runtime.foundation.architecture.get_architecture` and the shared
:class:`EntityResolver`. This module performs no discovery of its own.

Services
--------
* ``resolve_entity``        — ownership lookup
* ``affected_entities``     — change analysis
* ``blast_radius``          — dependency/graph traversal
* ``verification_plan``     — verification planning
* ``engineering_risk``      — risk scoring
* ``repair_plan``           — repair planning
* ``test_resolution``       — provider-only test resolution
* ``analyze``               — full bundle (used by commands that want all)
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.intelligence.platform.blast import (
    BlastRadius,
    compute_blast_radius,
)
from runtime.foundation.intelligence.platform.change import (
    analyze_changes,
)
from runtime.foundation.intelligence.platform.memory import build_memory
from runtime.foundation.intelligence.platform.optimizer import (
    VerificationPlanIntel,
    optimize_verification,
)
from runtime.foundation.intelligence.platform.repair import (
    RepairPlan,
    build_repair_intelligence,
    load_defects,
)
from runtime.foundation.intelligence.platform.resolver import (
    EntityResolver,
    get_resolver,
)
from runtime.foundation.intelligence.platform.risk import (
    EngineeringRisk,
    assess_risk,
)

__all__ = [
    "resolve_entity",
    "affected_entities",
    "blast_radius",
    "verification_plan",
    "engineering_risk",
    "repair_plan",
    "test_resolution",
    "analyze",
]


def _collect_default() -> list[str]:
    """Use the single canonical git change collector (no local re-implementation)."""
    from runtime.foundation.verification.orchestrator import (
        _collect_changed_files,
        _is_git_available,
    )

    if not _is_git_available():
        return []
    return _collect_changed_files()


def _files(changed_files: list[str] | None) -> list[str]:
    return list(changed_files) if changed_files is not None else _collect_default()


# ---------------------------------------------------------------------------
# Entity resolution — the ONLY ownership lookup
# ---------------------------------------------------------------------------


def resolve_entity(path: str, resolver: EntityResolver | None = None) -> dict[str, Any]:
    res = resolver or get_resolver()
    refs = res.classify_path(path)
    owner = res.owning_engine(path)
    return {
        "path": path,
        "entities": [r.to_dict() for r in refs],
        "owning_engine": owner.to_dict() if owner else None,
        "resolved": bool(refs),
    }


# ---------------------------------------------------------------------------
# Change analysis
# ---------------------------------------------------------------------------


def affected_entities(
    changed_files: list[str] | None = None,
    resolver: EntityResolver | None = None,
) -> dict[str, Any]:
    change = analyze_changes(resolver=resolver, paths=_files(changed_files))
    entities: dict[str, list[str]] = {}
    counts: dict[str, int] = {}
    for category, refs in change.entities.items():
        entities[category] = [r.ref for r in refs]
        counts[category] = len(refs)
    return {
        "counts": counts,
        "entities": entities,
        "owning_engines": [r.ref for r in change.owning_engines],
        "unmapped_paths": list(change.unmapped_paths),
        "platform_paths": list(change.platform_paths),
    }


def blast_radius(
    changed_files: list[str] | None = None,
    resolver: EntityResolver | None = None,
) -> BlastRadius:
    change = analyze_changes(resolver=resolver, paths=_files(changed_files))
    return compute_blast_radius(change, resolver=resolver)


def verification_plan(
    changed_files: list[str] | None = None,
    resolver: EntityResolver | None = None,
) -> VerificationPlanIntel:
    return optimize_verification(
        blast_radius(changed_files, resolver), resolver=resolver
    )


def engineering_risk(
    changed_files: list[str] | None = None,
    resolver: EntityResolver | None = None,
    generated_dir: Any = None,
) -> EngineeringRisk:
    change = analyze_changes(resolver=resolver, paths=_files(changed_files))
    blast = compute_blast_radius(change, resolver=resolver)
    plan = optimize_verification(blast, resolver=resolver)
    memory = build_memory(generated_dir=generated_dir)
    return assess_risk(
        change, blast, plan, resolver=resolver, memory=memory.as_risk_input()
    )


def repair_plan(
    defects: list[Any] | None = None,
    changed_files: list[str] | None = None,
    resolver: EntityResolver | None = None,
) -> RepairPlan:
    blast = blast_radius(changed_files, resolver)
    if defects is None:
        defects = load_defects()
    return build_repair_intelligence(blast, defects=defects, resolver=resolver)


# ---------------------------------------------------------------------------
# Test resolution — provider-only, never inferred from filenames
# ---------------------------------------------------------------------------


def test_resolution(
    changed_files: list[str] | None = None,
    resolver: EntityResolver | None = None,
) -> dict[str, Any]:
    """Resolve affected tests strictly from provider state.

    A test is mapped to the engine that *records* it in provider state. If a
    test path cannot be linked to any engine, it is reported as ``Unknown``
    rather than having a path invented for it.
    """
    blast = blast_radius(changed_files, resolver)
    res = resolver or get_resolver()

    engine_of_test: dict[str, str] = {}
    for engine in res.arch.engines.values():
        for test_path in engine.tests:
            engine_of_test.setdefault(test_path, engine.name)

    entries: list[dict[str, str]] = []
    for ref in blast.verification:
        test_path = ref.key
        engine_name = engine_of_test.get(test_path, "Unknown")
        entries.append(
            {
                "test": test_path,
                "engine": engine_name,
                "resolution": "provider" if engine_name != "Unknown" else "Unknown",
            }
        )

    unresolved = [e for e in entries if e["resolution"] == "Unknown"]
    return {
        "schema": "test-resolution/v1",
        "provider": "runtime.foundation.architecture.get_architecture",
        "inference_method": "none (provider-recorded tests only)",
        "total": len(entries),
        "resolved": len(entries) - len(unresolved),
        "tests": entries,
        "unresolved": unresolved,
        "policy": (
            "if a test cannot be resolved to an engine via provider state it is "
            "reported as Unknown; no filename-based path is ever invented"
        ),
    }


# ---------------------------------------------------------------------------
# Full bundle
# ---------------------------------------------------------------------------


def analyze(
    changed_files: list[str] | None = None,
    resolver: EntityResolver | None = None,
    generated_dir: Any = None,
) -> dict[str, Any]:
    change = analyze_changes(resolver=resolver, paths=_files(changed_files))
    blast = compute_blast_radius(change, resolver=resolver)
    plan = optimize_verification(blast, resolver=resolver)
    memory = build_memory(generated_dir=generated_dir)
    risk = assess_risk(
        change, blast, plan, resolver=resolver, memory=memory.as_risk_input()
    )
    repair = build_repair_intelligence(blast, resolver=resolver)
    return {
        "change": change,
        "blast": blast,
        "plan": plan,
        "risk": risk,
        "repair": repair,
        "memory": memory,
    }
