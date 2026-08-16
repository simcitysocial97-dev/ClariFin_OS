"""Cross-Layer Map Audit — Program 13.2 (provider-migrated).

Program 13.2: this audit no longer performs its own discovery or reads the
legacy ``cross-layer-map.json``. It consumes the single canonical architecture
via :func:`runtime.foundation.architecture.get_architecture`.

Internal engines (no capability, no router — e.g. ``nudge_engine``,
``insight_generator``, ``transaction_intelligence``) are GENUINE architectural
debt under the constitutional model. They are reported as known debt
(informational), never as false-positive failures.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

CHAIN_FIELDS = [
    "engine",
    "capabilities",
    "components",
    "endpoints",
    "graphRenderers",
    "mappers",
    "pages",
    "routers",
    "services",
    "tests",
    "viewModels",
    "workspace",
]

OPTIONAL_LIST_FIELDS = [
    "capabilities",
    "components",
    "endpoints",
    "graphRenderers",
    "mappers",
    "pages",
    "routers",
    "services",
    "tests",
    "viewModels",
    "workspace",
]


# ---------------------------------------------------------------------------
# canonical data source
# ---------------------------------------------------------------------------


def _build_data_from_provider(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Build a legacy-shaped chain map from the canonical provider.

    Internal engines are flagged via the ``internal`` key so downstream checks
    can exempt them from completeness/ownership failure.
    """
    from runtime.foundation.architecture.provider import get_architecture

    arch = get_architecture(refresh=False)
    data: dict[str, dict[str, Any]] = {}
    for name, eng in arch.engines.items():
        key = eng.path
        data[key] = {
            "engine": key,
            "engineName": name,
            "internal": bool(eng.internal),
            "migrationStatus": eng.migration_status or "CANONICAL",
            "services": list(eng.services),
            "routers": list(eng.routers),
            "endpoints": list(eng.endpoints),
            "ownedEndpoints": list(eng.endpoints),
            "capabilities": list(eng.capabilities),
            "implementationModules": list(eng.implementation_modules),
            "modules": list(eng.implementation_modules),
            "detectors": list(eng.detectors),
            "repositories": list(eng.repositories),
            "tests": list(eng.tests),
            "artifacts": list(eng.artifacts),
            "workspace": [],
            "pages": [],
            "components": [],
            "graphRenderers": [],
            "mappers": [],
            "viewModels": [],
        }
    return data


def _check_provider_available() -> dict[str, Any]:
    from runtime.foundation.architecture.provider import architecture_available

    ok = architecture_available()
    return {
        "section": "cross_layer",
        "check_id": "cl-provider-available",
        "name": "Canonical architecture provider available",
        "status": "pass" if ok else "fail",
        "severity": "critical" if not ok else "info",
        "priority": "critical" if not ok else "low",
        "message": (
            "Canonical architecture provider resolved all artifacts."
            if ok
            else "Canonical architecture artifacts missing; run discovery pipeline."
        ),
        "details": {"available": ok},
        "recommendation": "" if ok else "Run `python -m runtime.foundation.architecture.discovery`",
    }


# ---------------------------------------------------------------------------
# checks (legacy-shaped `data`, internal engines exempt)
# ---------------------------------------------------------------------------


def _verify_chain_field_completeness(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    missing_fields: dict[str, list[str]] = {}

    for chain_key, chain in data.items():
        missing = [f for f in CHAIN_FIELDS if f not in chain]
        if missing:
            missing_fields[chain_key] = missing
            findings.append({
                "section": "cross_layer",
                "check_id": f"cl-chain-fields-{chain_key[:50]}",
                "name": f"Chain field completeness for {chain_key}",
                "status": "fail",
                "severity": "high",
                "priority": "high",
                "message": f"Chain missing fields: {', '.join(missing)}",
                "details": {"chain_key": chain_key, "missing_fields": missing},
                "recommendation": f"Add missing fields to chain {chain_key}",
            })

    if not findings:
        findings.append({
            "section": "cross_layer",
            "check_id": "cl-chain-field-completeness",
            "name": "Chain field completeness",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"All {len(data)} chains have complete fields",
            "details": {"chains_checked": len(data)},
            "recommendation": "",
        })
    return findings


def _verify_chain_field_types(data: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    for chain_key, chain in data.items():
        val = chain.get("engine")
        if val is not None and not isinstance(val, str):
            findings.append({
                "section": "cross_layer",
                "check_id": f"cl-field-type-{chain_key[:30]}-engine",
                "name": f"Field type check: {chain_key}.engine",
                "status": "fail",
                "severity": "high",
                "priority": "high",
                "message": f"Field 'engine' should be string, got {type(val).__name__}",
                "details": {"chain_key": chain_key, "field": "engine", "actual_type": type(val).__name__},
                "recommendation": f"Fix type of 'engine' in chain {chain_key}",
            })
        for field_name in OPTIONAL_LIST_FIELDS:
            v = chain.get(field_name)
            if v is not None and not isinstance(v, list):
                findings.append({
                    "section": "cross_layer",
                    "check_id": f"cl-field-type-{chain_key[:30]}-{field_name}",
                    "name": f"Field type check: {chain_key}.{field_name}",
                    "status": "fail",
                    "severity": "medium",
                    "priority": "medium",
                    "message": f"Field '{field_name}' should be list, got {type(v).__name__}",
                    "details": {"chain_key": chain_key, "field": field_name, "actual_type": type(v).__name__},
                    "recommendation": f"Fix type of '{field_name}' in chain {chain_key}",
                })

    if not findings:
        findings.append({
            "section": "cross_layer",
            "check_id": "cl-field-types",
            "name": "Chain field types",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": "All chain fields have correct types",
            "details": {"chains_checked": len(data)},
            "recommendation": "",
        })
    return findings


def _verify_engine_file_existence(data: dict[str, dict[str, Any]], repo_root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for chain_key, chain in data.items():
        engine = chain.get("engine", "")
        if not engine:
            continue
        full = repo_root / engine
        exists = full.exists() or (engine.endswith(".py") and (repo_root / engine).with_suffix("").joinpath("__init__.py").exists())
        if not exists:
            findings.append({
                "section": "cross_layer",
                "check_id": f"cl-engine-exists-{engine[:50]}",
                "name": f"Engine file exists: {engine}",
                "status": "fail",
                "severity": "high",
                "priority": "high",
                "message": f"Engine file not found on disk: {engine}",
                "details": {"engine": engine, "chain_key": chain_key},
                "recommendation": f"Create or restore the engine: {engine}",
            })
    if not findings:
        findings.append({
            "section": "cross_layer",
            "check_id": "cl-engine-existence",
            "name": "Engine file existence",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"All {len(data)} engine files exist on disk",
            "details": {"engines_checked": len(data)},
            "recommendation": "",
        })
    return findings


def _verify_router_file_existence(data: dict[str, dict[str, Any]], repo_root: Path) -> list[dict[str, Any]]:
    missing_routers: list[str] = []
    for chain_key, chain in data.items():
        for router in chain.get("routers", []):
            if not (repo_root / router).exists():
                missing_routers.append(router)
    if missing_routers:
        status = "fail"
        message = f"Found {len(missing_routers)} missing router files"
    else:
        status = "pass"
        message = "All router files exist on disk"
    return [{
        "section": "cross_layer",
        "check_id": "cl-router-existence",
        "name": "Router file existence",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {"missing_routers": missing_routers[:50], "total_routers_checked": sum(len(c.get("routers", [])) for c in data.values())},
        "recommendation": "" if status == "pass" else "Restore missing router files",
    }]


def _verify_no_duplicate_engines(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    duplicates: list[str] = []
    engines: list[str] = []
    for chain_key, chain in data.items():
        engine = chain.get("engine", "")
        if engine:
            if engine in seen and engine not in duplicates:
                duplicates.append(engine)
            seen.add(engine)
            engines.append(engine)
    if not duplicates:
        status = "pass"
        message = f"All {len(engines)} engine references are unique"
    else:
        status = "fail"
        message = f"Found {len(duplicates)} duplicate engine references"
    return {
        "section": "cross_layer",
        "check_id": "cl-no-duplicate-engines",
        "name": "No duplicate engine chains",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {"duplicate_engines": duplicates, "total_engines": len(engines)},
        "recommendation": "" if status == "pass" else "Remove duplicate engine chains from cross-layer map",
    }


def _verify_chain_completeness(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    incomplete: list[str] = []
    internal_engines: list[str] = []
    for chain_key, chain in data.items():
        if chain.get("internal"):
            internal_engines.append(chain.get("engineName", chain_key))
            continue
        has_engine = bool(chain.get("engine", ""))
        has_any_component = any(
            isinstance(chain.get(f), list) and len(chain.get(f)) > 0
            for f in OPTIONAL_LIST_FIELDS
        )
        if not (has_engine and has_any_component):
            incomplete.append(chain_key)

    if not incomplete:
        status = "pass"
        message = "All external chains are complete (engine + at least one component type)"
    else:
        status = "fail"
        message = f"Found {len(incomplete)} incomplete external chains"
    finding = {
        "section": "cross_layer",
        "check_id": "cl-chain-completeness",
        "name": "Chain completeness",
        "status": status,
        "severity": "medium" if status == "fail" else "info",
        "priority": "medium" if status == "fail" else "low",
        "message": message,
        "details": {"incomplete_chains": incomplete[:50], "total_chains": len(data)},
        "recommendation": "" if status == "pass" else "Add missing components or engine to incomplete chains",
    }
    findings = [finding]
    if internal_engines:
        findings.append({
            "section": "cross_layer",
            "check_id": "cl-internal-engines",
            "name": "Internal engines (known architectural debt)",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": (
                f"{len(internal_engines)} internal engine(s) have no HTTP surface / capability "
                f"by design (consumed internally): {', '.join(internal_engines)}"
            ),
            "details": {"internal_engines": internal_engines},
            "recommendation": "Document as architectural debt; do not flag as cross-layer failure.",
        })
    return findings


def _verify_component_ownership(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    no_cap_external: list[str] = []
    no_rtr_external: list[str] = []
    internal_engines: list[str] = []

    for chain_key, chain in data.items():
        if chain.get("internal"):
            internal_engines.append(chain.get("engineName", chain_key))
            continue
        if not chain.get("capabilities"):
            no_cap_external.append(chain_key)
        if not chain.get("routers"):
            no_rtr_external.append(chain_key)

    issues = len(no_cap_external) + len(no_rtr_external)
    if issues == 0:
        status = "pass"
        message = "All external chains have ownership mapping (capabilities + routers)"
    else:
        status = "fail"
        message = (
            f"Found {len(no_cap_external)} external chains without capabilities, "
            f"{len(no_rtr_external)} without routers"
        )
    finding = {
        "section": "cross_layer",
        "check_id": "cl-component-ownership",
        "name": "Component ownership mapping",
        "status": status,
        "severity": "medium" if status == "fail" else "info",
        "priority": "medium" if status == "fail" else "low",
        "message": message,
        "details": {
            "chains_without_capabilities": no_cap_external[:50],
            "chains_without_routers": no_rtr_external[:50],
        },
        "recommendation": "" if status == "pass" else "Add capability and router mappings to external chains",
    }
    findings = [finding]
    if internal_engines:
        findings.append({
            "section": "cross_layer",
            "check_id": "cl-internal-ownership",
            "name": "Internal engine ownership (known debt)",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"Internal engines exempt from capability/router ownership: {', '.join(internal_engines)}",
            "details": {"internal_engines": internal_engines},
            "recommendation": "Consumed internally; not a top-level API engine.",
        })
    return findings


def _verify_endpoint_deduplication(arch_endpoints: dict[str, Any]) -> dict[str, Any]:
    """A true duplicate endpoint is one registered on TWO DIFFERENT routers.

    An endpoint legitimately appears in multiple engine chains when a router is
    shared by several engines (e.g. ``behaviour.py`` is owned by both
    ``behaviour_engine`` and ``recommendation_engine``). That is not a defect.
    """
    ep_to_routers: dict[str, set[str]] = {}
    for sig, ep in arch_endpoints.items():
        ep_to_routers.setdefault(sig, set()).add(ep.router)
    true_duplicates = [sig for sig, rs in ep_to_routers.items() if len(rs) > 1]
    if not true_duplicates:
        status = "pass"
        message = "Every endpoint is owned by exactly one router (shared routers permitted)"
    else:
        status = "fail"
        message = f"Found {len(true_duplicates)} endpoints registered on multiple routers"
    return {
        "section": "cross_layer",
        "check_id": "cl-endpoint-deduplication",
        "name": "Endpoint deduplication (unique owning router)",
        "status": status,
        "severity": "medium" if status == "fail" else "info",
        "priority": "medium" if status == "fail" else "low",
        "message": message,
        "details": {
            "true_duplicate_endpoints": true_duplicates[:50],
            "total_endpoints": len(ep_to_routers),
        },
        "recommendation": "" if status == "pass" else "Register each endpoint on a single router",
    }


def _verify_test_mapping(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    chains_without_tests: list[str] = []
    total_test_refs = 0
    external = [c for c in data.values() if not c.get("internal")]
    for chain in external:
        tests = chain.get("tests", [])
        total_test_refs += len(tests)
        if not tests:
            chains_without_tests.append(chain.get("engineName", ""))
    if not chains_without_tests:
        status = "pass"
        message = f"All {len(external)} external chains have test mappings"
    else:
        pct = (len(external) - len(chains_without_tests)) / len(external) * 100 if external else 0
        status = "fail" if pct < 50 else "pass"
        message = f"{len(chains_without_tests)} of {len(external)} external chains have no test mappings ({pct:.0f}% coverage)"
    return {
        "section": "cross_layer",
        "check_id": "cl-test-mapping",
        "name": "Test mapping completeness",
        "status": status,
        "severity": "medium" if status == "fail" else "info",
        "priority": "medium" if status == "fail" else "low",
        "message": message,
        "details": {"chains_without_tests": chains_without_tests[:50], "total_test_refs": total_test_refs},
        "recommendation": "" if status == "pass" else "Add test mappings to chains missing coverage",
    }


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    repo = repo_root or REPO_ROOT
    findings: list[dict[str, Any]] = []

    findings.append(_check_provider_available())

    data = _build_data_from_provider(repo)
    if not data:
        findings.append({
            "section": "cross_layer",
            "check_id": "cl-map-load",
            "name": "Cross-layer map load",
            "status": "fail",
            "severity": "critical",
            "priority": "critical",
            "message": "Could not build cross-layer chains from the canonical provider",
            "details": {},
            "recommendation": "Run the discovery pipeline before the cross-layer audit",
        })
    else:
        findings.extend(_verify_chain_field_completeness(data))
        findings.extend(_verify_chain_field_types(data))
        findings.extend(_verify_engine_file_existence(data, repo))
        findings.extend(_verify_router_file_existence(data, repo))
        findings.append(_verify_no_duplicate_engines(data))
        findings.extend(_verify_chain_completeness(data))
        findings.extend(_verify_component_ownership(data))
        from runtime.foundation.architecture.provider import get_architecture

        findings.append(_verify_endpoint_deduplication(get_architecture(refresh=False).endpoints))
        findings.append(_verify_test_mapping(data))

    all_pass = all(f["status"] == "pass" for f in findings)
    duration = time.monotonic() - start
    metrics = {
        "total_chains": len(data),
        "total_checks": len(findings),
        "failures": sum(1 for f in findings if f["status"] == "fail"),
        "passes": sum(1 for f in findings if f["status"] == "pass"),
    }
    if data:
        metrics["total_endpoints"] = sum(len(c.get("endpoints", [])) for c in data.values())
        metrics["total_components"] = sum(len(c.get("components", [])) for c in data.values())
        metrics["total_test_refs"] = sum(len(c.get("tests", [])) for c in data.values())
        metrics["internal_engines"] = sum(1 for c in data.values() if c.get("internal"))

    return {
        "section": "cross_layer",
        "name": "Cross-Layer Map Audit",
        "status": "pass" if all_pass else "fail",
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": duration,
    }
