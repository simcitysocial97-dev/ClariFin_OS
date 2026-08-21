"""Knowledge Indexer — Program 11.

Builds deterministic indexes from runtime artifacts.
Consumes only existing artifacts. Never generates new facts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.foundation.knowledge.catalog import KnowledgeCatalog, set_catalog
from runtime.foundation.knowledge.models import (
    CapabilityEntry,
    ComponentEntry,
    DocumentationEntry,
    EndpointEntry,
    GraphRendererEntry,
    IntegrityRuleEntry,
    KnowledgeIndex,
    MapperEntry,
    RuntimeArtifactEntry,
    VerificationProfileEntry,
    ViewModelEntry,
    WorkspaceEntry,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GENERATED_DIR = REPO_ROOT / "runtime" / "generated"
DOCS_DIR = REPO_ROOT / "docs"
KNOWLEDGE_INDEX_PATH = GENERATED_DIR / "knowledge-index.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _load_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _extract_endpoints(cross_layer_map: dict[str, Any]) -> list[EndpointEntry]:
    endpoints: list[EndpointEntry] = []
    seen: set[str] = set()
    for file_path, entry in cross_layer_map.items():
        for ep in entry.get("endpoints", []):
            if ep not in seen:
                seen.add(ep)
                method = "GET"
                path_part = ep
                if " " in ep:
                    parts = ep.split(" ", 1)
                    method = parts[0]
                    path_part = parts[1] if len(parts) > 1 else ep
                references = {
                    "source_file": file_path,
                    "architecture_provider": "runtime.foundation.architecture.get_architecture",
                }
                for svc in entry.get("services", []):
                    references[f"service:{svc}"] = f"service:{svc}"
                for cap in entry.get("capabilities", []):
                    references[f"capability:{cap}"] = f"capability:{cap}"
                for router in entry.get("routers", []):
                    references[f"router:{router}"] = f"router:{router}"
                for mapper in entry.get("mappers", []):
                    references[f"mapper:{mapper}"] = f"mapper:{mapper}"
                for vm in entry.get("viewModels", []):
                    references[f"viewModel:{vm}"] = f"viewModel:{vm}"
                for comp in entry.get("components", []):
                    references[f"component:{comp}"] = f"component:{comp}"
                for ws in entry.get("workspace", []):
                    references[f"workspace:{ws}"] = f"workspace:{ws}"
                for test in entry.get("tests", []):
                    references[f"test:{test}"] = f"test:{test}"
                endpoints.append(
                    EndpointEntry(
                        path=path_part,
                        method=method,
                        references=references,
                        tags=tuple(sorted(seen)),
                    )
                )
    return endpoints


def _extract_capabilities(cross_layer_map: dict[str, Any]) -> list[CapabilityEntry]:
    capabilities: list[CapabilityEntry] = []
    seen: set[str] = set()
    for file_path, entry in cross_layer_map.items():
        for cap in entry.get("capabilities", []):
            if cap not in seen:
                seen.add(cap)
                references = {
                    "source_file": file_path,
                    "architecture_provider": "runtime.foundation.architecture.get_architecture",
                }
                for ep in entry.get("endpoints", []):
                    references[f"endpoint:{ep}"] = f"endpoint:{ep}"
                for svc in entry.get("services", []):
                    references[f"service:{svc}"] = f"service:{svc}"
                for comp in entry.get("components", []):
                    references[f"component:{comp}"] = f"component:{comp}"
                for ws in entry.get("workspace", []):
                    references[f"workspace:{ws}"] = f"workspace:{ws}"
                capabilities.append(
                    CapabilityEntry(
                        name=cap,
                        references=references,
                        tags=tuple(sorted(seen)),
                    )
                )
    return capabilities


def _extract_mappers(cross_layer_map: dict[str, Any]) -> list[MapperEntry]:
    mappers: list[MapperEntry] = []
    seen: set[str] = set()
    for file_path, entry in cross_layer_map.items():
        for mp in entry.get("mappers", []):
            if mp not in seen:
                seen.add(mp)
                references = {
                    "source_file": file_path,
                    "architecture_provider": "runtime.foundation.architecture.get_architecture",
                }
                for cap in entry.get("capabilities", []):
                    references[f"capability:{cap}"] = f"capability:{cap}"
                for vm in entry.get("viewModels", []):
                    references[f"viewModel:{vm}"] = f"viewModel:{vm}"
                mappers.append(
                    MapperEntry(
                        name=mp,
                        references=references,
                        tags=tuple(sorted(seen)),
                    )
                )
    return mappers


def _extract_view_models(cross_layer_map: dict[str, Any]) -> list[ViewModelEntry]:
    view_models: list[ViewModelEntry] = []
    seen: set[str] = set()
    for file_path, entry in cross_layer_map.items():
        for vm in entry.get("viewModels", []):
            if vm not in seen:
                seen.add(vm)
                references = {
                    "source_file": file_path,
                    "architecture_provider": "runtime.foundation.architecture.get_architecture",
                }
                for mp in entry.get("mappers", []):
                    references[f"mapper:{mp}"] = f"mapper:{mp}"
                for ws in entry.get("workspace", []):
                    references[f"workspace:{ws}"] = f"workspace:{ws}"
                view_models.append(
                    ViewModelEntry(
                        name=vm,
                        references=references,
                        tags=tuple(sorted(seen)),
                    )
                )
    return view_models


def _extract_workspaces(cross_layer_map: dict[str, Any]) -> list[WorkspaceEntry]:
    workspaces: list[WorkspaceEntry] = []
    seen: set[str] = set()
    for file_path, entry in cross_layer_map.items():
        for ws in entry.get("workspace", []):
            if ws not in seen:
                seen.add(ws)
                references = {
                    "source_file": file_path,
                    "architecture_provider": "runtime.foundation.architecture.get_architecture",
                }
                for comp in entry.get("components", []):
                    references[f"component:{comp}"] = f"component:{comp}"
                for vm in entry.get("viewModels", []):
                    references[f"viewModel:{vm}"] = f"viewModel:{vm}"
                workspaces.append(
                    WorkspaceEntry(
                        name=ws,
                        references=references,
                        tags=tuple(sorted(seen)),
                    )
                )
    return workspaces


def _extract_components(cross_layer_map: dict[str, Any]) -> list[ComponentEntry]:
    components: list[ComponentEntry] = []
    seen: set[str] = set()
    for file_path, entry in cross_layer_map.items():
        for comp in entry.get("components", []):
            if comp not in seen:
                seen.add(comp)
                references = {
                    "source_file": file_path,
                    "architecture_provider": "runtime.foundation.architecture.get_architecture",
                }
                for ws in entry.get("workspace", []):
                    references[f"workspace:{ws}"] = f"workspace:{ws}"
                for vm in entry.get("viewModels", []):
                    references[f"viewModel:{vm}"] = f"viewModel:{vm}"
                components.append(
                    ComponentEntry(
                        name=comp,
                        references=references,
                        tags=tuple(sorted(seen)),
                    )
                )
    return components


def _extract_graph_renderers(
    cross_layer_map: dict[str, Any],
) -> list[GraphRendererEntry]:
    renderers: list[GraphRendererEntry] = []
    seen: set[str] = set()
    for file_path, entry in cross_layer_map.items():
        for gr in entry.get("graphRenderers", []):
            if gr not in seen:
                seen.add(gr)
                references = {
                    "source_file": file_path,
                    "architecture_provider": "runtime.foundation.architecture.get_architecture",
                }
                renderers.append(
                    GraphRendererEntry(
                        name=gr,
                        references=references,
                        tags=tuple(sorted(seen)),
                    )
                )
    return renderers


def _extract_runtime_artifacts() -> list[RuntimeArtifactEntry]:
    artifacts: list[RuntimeArtifactEntry] = []
    artifact_files = [
        "cross-layer-map.json",
        "dashboard.json",
        "engineering-history.json",
        "engineering-health.md",
        "engineering-analytics.json",
        "verification-report.md",
        "dependency-growth.json",
        "flaky-tests.json",
        "cost-analysis.json",
    ]
    for filename in artifact_files:
        path = GENERATED_DIR / filename
        if path.exists():
            references = {"path": str(path.relative_to(REPO_ROOT))}
            artifacts.append(
                RuntimeArtifactEntry(
                    path=str(path.relative_to(REPO_ROOT)),
                    references=references,
                    tags=(filename,),
                )
            )
    return artifacts


def _extract_documentation() -> list[DocumentationEntry]:
    docs: list[DocumentationEntry] = []
    if not DOCS_DIR.exists():
        return docs
    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        rel_path = md_file.relative_to(REPO_ROOT)
        title = md_file.stem
        references = {"path": str(rel_path)}
        docs.append(
            DocumentationEntry(
                title=title,
                path=str(rel_path),
                references=references,
                tags=(md_file.suffix.lstrip("."),),
            )
        )
    return docs


def _extract_integrity_rules() -> list[IntegrityRuleEntry]:
    rules: list[IntegrityRuleEntry] = []
    try:
        from runtime.foundation.integrity.registry import get_constitution

        registry = get_constitution()
        for rule in registry.rules:
            rule_id = rule.id if hasattr(rule, "id") else rule.rule_id
            references = {
                "rule_id": rule_id,
                "name": rule.name,
                "category": (
                    rule.category.value
                    if hasattr(rule.category, "value")
                    else str(rule.category)
                ),
                "severity": (
                    rule.severity.value
                    if hasattr(rule.severity, "value")
                    else str(rule.severity)
                ),
            }
            rules.append(
                IntegrityRuleEntry(
                    rule_id=rule_id,
                    references=references,
                    tags=(
                        (
                            rule.category.value
                            if hasattr(rule.category, "value")
                            else str(rule.category)
                        ),
                    ),
                )
            )
    except Exception:
        pass
    return rules


def _extract_verification_profiles() -> list[VerificationProfileEntry]:
    profiles: list[VerificationProfileEntry] = []
    try:
        from runtime.foundation.verification.profiles import list_profiles

        for profile in list_profiles():
            name = profile.name if hasattr(profile, "name") else str(profile)
            references = {"profile": name}
            profiles.append(
                VerificationProfileEntry(
                    name=name,
                    references=references,
                    tags=(name,),
                )
            )
    except Exception:
        pass
    return profiles


def _merge_from_provider(
    endpoints: list[EndpointEntry],
    capabilities: list[CapabilityEntry],
    workspaces: list[WorkspaceEntry],
) -> tuple[list[EndpointEntry], list[CapabilityEntry], list[WorkspaceEntry]]:
    """Augment the cross-layer extracted entries with canonical-provider entities.

    Program 13.2: the canonical provider is the single source of architectural
    truth. The cross-layer map is the primary extraction source (it carries rich
    references), but entities only present in the provider (e.g. frontend-only
    capabilities with no backend router) are merged in so the knowledge base is
    complete and consistent with the provider.
    """
    from runtime.foundation.architecture.provider import get_architecture

    arch = get_architecture(refresh=False)
    existing_eps = {(e.method, e.path) for e in endpoints}
    existing_caps = {c.name for c in capabilities}
    existing_ws = {w.name for w in workspaces}

    out_eps = list(endpoints)
    out_caps = list(capabilities)
    out_ws = list(workspaces)

    for sig, ep in arch.endpoints.items():
        if (ep.method, ep.path) in existing_eps:
            continue
        existing_eps.add((ep.method, ep.path))
        refs = {"source_file": ep.router, "provider": "architecture-provider"}
        for eng in ep.engines:
            refs[f"engine:{eng}"] = f"engine:{eng}"
        for cap in ep.capabilities:
            refs[f"capability:{cap}"] = f"capability:{cap}"
        out_eps.append(
            EndpointEntry(
                path=ep.path, method=ep.method, references=refs, tags=("provider",)
            )
        )

    for name, cap in arch.capabilities.items():
        if name in existing_caps:
            continue
        existing_caps.add(name)
        refs = {"source_file": cap.path or "", "provider": "architecture-provider"}
        for eng in cap.engines:
            refs[f"engine:{eng}"] = f"engine:{eng}"
        for ep in cap.endpoints:
            refs[f"endpoint:{ep}"] = f"endpoint:{ep}"
        tag = "provider" if cap.engines else "provider-frontend-only"
        out_caps.append(CapabilityEntry(name=name, references=refs, tags=(tag,)))

    for name, ws in arch.workspaces.items():
        if name in existing_ws:
            continue
        existing_ws.add(name)
        refs = {"source_file": ws.path, "provider": "architecture-provider"}
        out_ws.append(WorkspaceEntry(name=name, references=refs, tags=("provider",)))

    return out_eps, out_caps, out_ws


def build_index() -> KnowledgeIndex:
    """Build the complete knowledge index from all runtime artifacts.

    Returns:
        Immutable KnowledgeIndex with all catalog entries.
    """
    # Program 13.3: chains come from the canonical architecture provider.
    from runtime.foundation.architecture.chains import get_chain_map

    try:
        cross_layer_map = get_chain_map()
    except Exception:  # provider not yet discovered
        cross_layer_map = {}

    endpoints = _extract_endpoints(cross_layer_map)
    capabilities = _extract_capabilities(cross_layer_map)
    mappers = _extract_mappers(cross_layer_map)
    view_models = _extract_view_models(cross_layer_map)
    workspaces = _extract_workspaces(cross_layer_map)
    components = _extract_components(cross_layer_map)
    graph_renderers = _extract_graph_renderers(cross_layer_map)
    endpoints, capabilities, workspaces = _merge_from_provider(
        endpoints, capabilities, workspaces
    )
    runtime_artifacts = _extract_runtime_artifacts()
    documentation = _extract_documentation()
    integrity_rules = _extract_integrity_rules()
    verification_profiles = _extract_verification_profiles()

    catalog = KnowledgeCatalog(
        endpoints=tuple(sorted(endpoints, key=lambda e: e.path)),
        capabilities=tuple(
            sorted(capabilities, key=lambda c: getattr(c, "name", str(c)))
        ),
        mappers=tuple(sorted(mappers, key=lambda m: m.name)),
        view_models=tuple(sorted(view_models, key=lambda v: v.name)),
        workspaces=tuple(sorted(workspaces, key=lambda w: w.name)),
        components=tuple(sorted(components, key=lambda c: c.name)),
        graph_renderers=tuple(sorted(graph_renderers, key=lambda g: g.name)),
        verification_profiles=tuple(
            sorted(verification_profiles, key=lambda v: v.name)
        ),
        integrity_rules=tuple(sorted(integrity_rules, key=lambda r: r.rule_id)),
        runtime_artifacts=tuple(sorted(runtime_artifacts, key=lambda r: r.path)),
        documentation=tuple(sorted(documentation, key=lambda d: d.path)),
    )

    set_catalog(catalog)

    source_artifacts = [
        "runtime.foundation.architecture (canonical provider)",
        "runtime/generated/dashboard.json",
        "runtime/generated/engineering-history.json",
        "runtime/generated/engineering-health.md",
        "runtime/generated/engineering-analytics.json",
        "runtime/generated/verification-report.md",
        "runtime/generated/dependency-growth.json",
        "runtime/generated/flaky-tests.json",
        "runtime/generated/cost-analysis.json",
    ]

    index = KnowledgeIndex(
        endpoints=catalog.endpoints,
        capabilities=catalog.capabilities,
        mappers=catalog.mappers,
        view_models=catalog.view_models,
        workspaces=catalog.workspaces,
        components=catalog.components,
        graph_renderers=catalog.graph_renderers,
        verification_profiles=catalog.verification_profiles,
        integrity_rules=catalog.integrity_rules,
        runtime_artifacts=catalog.runtime_artifacts,
        documentation=catalog.documentation,
        indexed_at=datetime.now(timezone.utc).isoformat(),
        source_artifacts=tuple(source_artifacts),
    )

    return index


def save_index(index: KnowledgeIndex | None = None) -> Path:
    """Save the knowledge index to runtime/generated/knowledge-index.json.

    Args:
        index: Optional pre-built index. If None, builds a new one.

    Returns:
        Path to the saved index file.
    """
    if index is None:
        index = build_index()

    KNOWLEDGE_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "indexed_at": index.indexed_at,
        "source_artifacts": list(index.source_artifacts),
        "categories": {
            "endpoints": [
                {
                    "path": ep.path,
                    "method": ep.method,
                    "references": ep.references,
                    "tags": list(ep.tags),
                }
                for ep in index.endpoints
            ],
            "capabilities": [
                {
                    "name": getattr(cap, "name", str(cap)),
                    "references": getattr(cap, "references", {}),
                    "tags": list(getattr(cap, "tags", ())),
                }
                for cap in index.capabilities
            ],
            "mappers": [
                {
                    "name": mp.name,
                    "references": mp.references,
                    "tags": list(mp.tags),
                }
                for mp in index.mappers
            ],
            "view_models": [
                {
                    "name": vm.name,
                    "references": vm.references,
                    "tags": list(vm.tags),
                }
                for vm in index.view_models
            ],
            "workspaces": [
                {
                    "name": ws.name,
                    "references": ws.references,
                    "tags": list(ws.tags),
                }
                for ws in index.workspaces
            ],
            "components": [
                {
                    "name": comp.name,
                    "references": comp.references,
                    "tags": list(comp.tags),
                }
                for comp in index.components
            ],
            "graph_renderers": [
                {
                    "name": gr.name,
                    "references": gr.references,
                    "tags": list(gr.tags),
                }
                for gr in index.graph_renderers
            ],
            "verification_profiles": [
                {
                    "name": vp.name,
                    "references": vp.references,
                    "tags": list(vp.tags),
                }
                for vp in index.verification_profiles
            ],
            "integrity_rules": [
                {
                    "rule_id": rule.rule_id,
                    "references": rule.references,
                    "tags": list(rule.tags),
                }
                for rule in index.integrity_rules
            ],
            "runtime_artifacts": [
                {
                    "path": ra.path,
                    "references": ra.references,
                    "tags": list(ra.tags),
                }
                for ra in index.runtime_artifacts
            ],
            "documentation": [
                {
                    "title": doc.title,
                    "path": doc.path,
                    "references": doc.references,
                    "tags": list(doc.tags),
                }
                for doc in index.documentation
            ],
        },
        "counts": {
            "endpoints": len(index.endpoints),
            "capabilities": len(index.capabilities),
            "mappers": len(index.mappers),
            "view_models": len(index.view_models),
            "workspaces": len(index.workspaces),
            "components": len(index.components),
            "graph_renderers": len(index.graph_renderers),
            "verification_profiles": len(index.verification_profiles),
            "integrity_rules": len(index.integrity_rules),
            "runtime_artifacts": len(index.runtime_artifacts),
            "documentation": len(index.documentation),
        },
    }

    with open(KNOWLEDGE_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    return KNOWLEDGE_INDEX_PATH
