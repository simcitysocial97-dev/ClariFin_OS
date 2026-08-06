"""Cross-Layer Map Audit — Program 12.

Verifies the cross-layer dependency map (cross-layer-map.json) for:
- File existence of all chain components
- Chain completeness (each chain has at least engine + one component type)
- No duplicate chains (same engine appearing multiple times)
- Ownership mapping validity
- Structural consistency across chains
"""

from __future__ import annotations

import json
import os
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

REQUIRED_CHAIN_FIELDS = ["engine"]

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


def _find_map_path(repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    return root / "runtime" / "generated" / "cross-layer-map.json"


def _load_map(map_path: Path) -> dict[str, dict[str, Any]]:
    if not map_path.exists():
        return {}
    return json.loads(map_path.read_text(encoding="utf-8"))


def _check_file_exists(repo_root: Path, file_path: str) -> bool:
    """Check if a file or package directory exists for the given path."""
    full = repo_root / file_path
    if full.exists():
        return True
    # Check if .py file is actually a package (directory with __init__.py)
    if file_path.endswith(".py"):
        pkg_path = str(full).replace(".py", "/__init__.py")
        if os.path.exists(pkg_path):
            return True
    return False


def _verify_map_existence(map_path: Path) -> dict[str, Any]:
    if map_path.exists():
        status = "pass"
        message = f"Cross-layer map exists at {map_path}"
    else:
        status = "fail"
        message = f"Cross-layer map not found at {map_path}"
    return {
        "section": "cross_layer",
        "check_id": "cl-map-existence",
        "name": "Cross-layer map existence",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": {"path": str(map_path), "exists": map_path.exists()},
        "recommendation": "" if status == "pass" else "Run build_cross_layer_map.py to generate the cross-layer map",
    }


def _verify_map_json_validity(map_path: Path) -> dict[str, Any]:
    try:
        data = json.loads(map_path.read_text(encoding="utf-8"))
        status = "pass"
        message = "Cross-layer map JSON is valid"
    except (json.JSONDecodeError, OSError) as exc:
        status = "fail"
        message = f"Cross-layer map JSON is invalid: {exc}"
        data = {}
    return {
        "section": "cross_layer",
        "check_id": "cl-map-json-validity",
        "name": "Cross-layer map JSON validity",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": {"chain_count": len(data) if data else 0},
        "recommendation": "" if status == "pass" else "Fix JSON syntax errors in cross-layer-map.json",
    }


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
        for field_name in REQUIRED_CHAIN_FIELDS:
            val = chain.get(field_name)
            if val is not None and not isinstance(val, str):
                findings.append({
                    "section": "cross_layer",
                    "check_id": f"cl-field-type-{chain_key[:30]}-{field_name}",
                    "name": f"Field type check: {chain_key}.{field_name}",
                    "status": "fail",
                    "severity": "high",
                    "priority": "high",
                    "message": f"Field '{field_name}' should be string, got {type(val).__name__}",
                    "details": {"chain_key": chain_key, "field": field_name, "actual_type": type(val).__name__},
                    "recommendation": f"Fix type of '{field_name}' in chain {chain_key}",
                })

        for field_name in OPTIONAL_LIST_FIELDS:
            val = chain.get(field_name)
            if val is not None and not isinstance(val, list):
                findings.append({
                    "section": "cross_layer",
                    "check_id": f"cl-field-type-{chain_key[:30]}-{field_name}",
                    "name": f"Field type check: {chain_key}.{field_name}",
                    "status": "fail",
                    "severity": "medium",
                    "priority": "medium",
                    "message": f"Field '{field_name}' should be list, got {type(val).__name__}",
                    "details": {"chain_key": chain_key, "field": field_name, "actual_type": type(val).__name__},
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
    missing_engines: list[str] = []

    for chain_key, chain in data.items():
        engine = chain.get("engine", "")
        if not engine:
            continue
        if not _check_file_exists(repo_root, engine):
            missing_engines.append(engine)
            findings.append({
                "section": "cross_layer",
                "check_id": f"cl-engine-exists-{engine[:50]}",
                "name": f"Engine file exists: {engine}",
                "status": "fail",
                "severity": "high",
                "priority": "high",
                "message": f"Engine file not found on disk: {engine}",
                "details": {"engine": engine, "chain_key": chain_key},
                "recommendation": f"Create or restore the engine file: {engine}",
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
            if not _check_file_exists(repo_root, router):
                missing_routers.append(router)

    if missing_routers:
        status = "fail"
        message = f"Found {len(missing_routers)} missing router files"
    else:
        status = "pass"
        message = "All router files exist on disk"

    return [
        {
            "section": "cross_layer",
            "check_id": "cl-router-existence",
            "name": "Router file existence",
            "status": status,
            "severity": "high" if status == "fail" else "info",
            "priority": "high" if status == "fail" else "low",
            "message": message,
            "details": {"missing_routers": missing_routers[:50], "total_routers_checked": sum(len(c.get("routers", [])) for c in data.values())},
            "recommendation": "" if status == "pass" else "Restore missing router files",
        }
    ]


def _verify_no_duplicate_engines(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    engines: list[str] = []
    seen: set[str] = set()
    duplicates: list[str] = []
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
    for chain_key, chain in data.items():
        has_engine = bool(chain.get("engine", ""))
        has_any_component = any(
            isinstance(chain.get(f), list) and len(chain.get(f)) > 0
            for f in OPTIONAL_LIST_FIELDS
        )
        if not (has_engine and has_any_component):
            incomplete.append(chain_key)

    if not incomplete:
        status = "pass"
        message = f"All {len(data)} chains are complete (have engine + at least one component type)"
    else:
        status = "fail"
        message = f"Found {len(incomplete)} incomplete chains"
    return {
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


def _verify_component_ownership(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    chains_with_no_capability: list[str] = []
    chains_with_no_routers: list[str] = []

    for chain_key, chain in data.items():
        if not chain.get("capabilities"):
            chains_with_no_capability.append(chain_key)
        if not chain.get("routers"):
            chains_with_no_routers.append(chain_key)

    issues = len(chains_with_no_capability) + len(chains_with_no_routers)
    if issues == 0:
        status = "pass"
        message = f"All {len(data)} chains have ownership mapping (capabilities + routers)"
    else:
        status = "fail"
        message = f"Found {len(chains_with_no_capability)} chains without capabilities, {len(chains_with_no_routers)} without routers"
    return {
        "section": "cross_layer",
        "check_id": "cl-component-ownership",
        "name": "Component ownership mapping",
        "status": status,
        "severity": "medium" if status == "fail" else "info",
        "priority": "medium" if status == "fail" else "low",
        "message": message,
        "details": {
            "chains_without_capabilities": chains_with_no_capability[:50],
            "chains_without_routers": chains_with_no_routers[:50],
        },
        "recommendation": "" if status == "pass" else "Add capability and router mappings to chains",
    }


def _verify_endpoint_deduplication(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    all_endpoints: list[str] = []
    seen: set[str] = set()
    duplicates: list[str] = []
    for chain_key, chain in data.items():
        for ep in chain.get("endpoints", []):
            if ep in seen and ep not in duplicates:
                duplicates.append(ep)
            seen.add(ep)
            all_endpoints.append(ep)

    if not duplicates:
        status = "pass"
        message = f"All {len(all_endpoints)} endpoints are unique across chains"
    else:
        status = "fail"
        message = f"Found {len(duplicates)} duplicate endpoints across chains"
    return {
        "section": "cross_layer",
        "check_id": "cl-endpoint-deduplication",
        "name": "Endpoint deduplication across chains",
        "status": status,
        "severity": "medium" if status == "fail" else "info",
        "priority": "medium" if status == "fail" else "low",
        "message": message,
        "details": {"duplicate_endpoints": duplicates[:50], "total_endpoints": len(all_endpoints)},
        "recommendation": "" if status == "pass" else "Remove duplicate endpoint entries from cross-layer map",
    }


def _verify_test_mapping(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    chains_without_tests: list[str] = []
    total_test_refs = 0

    for chain_key, chain in data.items():
        tests = chain.get("tests", [])
        total_test_refs += len(tests)
        if not tests:
            chains_without_tests.append(chain_key)

    if not chains_without_tests:
        status = "pass"
        message = f"All {len(data)} chains have test mappings"
    else:
        pct = (len(data) - len(chains_without_tests)) / len(data) * 100 if data else 0
        status = "fail" if pct < 50 else "pass"
        message = f"{len(chains_without_tests)} of {len(data)} chains have no test mappings ({pct:.0f}% coverage)"
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


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    findings: list[dict[str, Any]] = []
    repo = repo_root or REPO_ROOT
    map_path = _find_map_path(repo)

    findings.append(_verify_map_existence(map_path))

    data = _load_map(map_path)

    if data:
        findings.append(_verify_map_json_validity(map_path))
        findings.extend(_verify_chain_field_completeness(data))
        findings.extend(_verify_chain_field_types(data))
        findings.extend(_verify_engine_file_existence(data, repo))
        findings.extend(_verify_router_file_existence(data, repo))
        findings.append(_verify_no_duplicate_engines(data))
        findings.append(_verify_chain_completeness(data))
        findings.append(_verify_component_ownership(data))
        findings.append(_verify_endpoint_deduplication(data))
        findings.append(_verify_test_mapping(data))
    else:
        findings.append({
            "section": "cross_layer",
            "check_id": "cl-map-load",
            "name": "Cross-layer map load",
            "status": "fail",
            "severity": "critical",
            "priority": "critical",
            "message": "Could not load cross-layer map for content checks",
            "details": {},
            "recommendation": "Generate cross-layer-map.json before running cross-layer audit",
        })

    all_pass = all(f["status"] == "pass" for f in findings)
    overall_status = "pass" if all_pass else "fail"

    duration = time.monotonic() - start
    metrics = {
        "total_chains": len(data),
        "total_checks": len(findings),
        "failures": sum(1 for f in findings if f["status"] == "fail"),
        "passes": sum(1 for f in findings if f["status"] == "pass"),
    }
    if data:
        total_endpoints = sum(len(c.get("endpoints", [])) for c in data.values())
        total_components = sum(len(c.get("components", [])) for c in data.values())
        total_tests = sum(len(c.get("tests", [])) for c in data.values())
        metrics["total_endpoints"] = total_endpoints
        metrics["total_components"] = total_components
        metrics["total_test_refs"] = total_tests

    return {
        "section": "cross_layer",
        "name": "Cross-Layer Map Audit",
        "status": overall_status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": duration,
    }
