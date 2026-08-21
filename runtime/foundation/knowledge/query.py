"""Knowledge Query Engine — Program 11.

Deterministic lookups over the knowledge index.
Supports endpoint, capability, workspace, rule, and component queries.
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.knowledge.catalog import get_catalog
from runtime.foundation.knowledge.models import (
    KnowledgeEntry,
    QueryResult,
)


class KnowledgeQueryEngine:
    """Deterministic query engine for the Engineering Knowledge Base.

    Supports lookups by endpoint path, capability name, workspace name,
    rule ID, and component name. Returns ownership, dependencies,
    verification profile, integrity rules, documentation references,
    and related runtime artifacts.
    """

    def __init__(self, catalog: Any | None = None) -> None:
        self._catalog = catalog or get_catalog()

    def query_endpoint(self, path: str) -> QueryResult | None:
        """Look up an endpoint by its path."""
        entry = self._catalog.endpoint_by_path(path)
        if entry is None:
            return None
        knowledge_entry = KnowledgeEntry(
            id=entry.path,
            category="endpoint",
            name=entry.path,
            references=entry.references,
            tags=entry.tags,
        )
        return self._build_result(knowledge_entry)

    def query_capability(self, name: str) -> QueryResult | None:
        """Look up a capability by its name."""
        entry = self._catalog.capability_by_name(name)
        if entry is None:
            return None
        knowledge_entry = KnowledgeEntry(
            id=name,
            category="capability",
            name=name,
            references=entry.references,
            tags=entry.tags,
        )
        return self._build_result(knowledge_entry)

    def query_workspace(self, name: str) -> QueryResult | None:
        """Look up a workspace by its name."""
        entry = self._catalog.workspace_by_name(name)
        if entry is None:
            return None
        knowledge_entry = KnowledgeEntry(
            id=name,
            category="workspace",
            name=name,
            references=entry.references,
            tags=entry.tags,
        )
        return self._build_result(knowledge_entry)

    def query_rule(self, rule_id: str) -> QueryResult | None:
        """Look up an integrity rule by its ID."""
        entry = self._catalog.rule_by_id(rule_id)
        if entry is None:
            return None
        knowledge_entry = KnowledgeEntry(
            id=rule_id,
            category="integrity_rule",
            name=rule_id,
            references=entry.references,
            tags=entry.tags,
        )
        return self._build_result(knowledge_entry)

    def query_component(self, name: str) -> QueryResult | None:
        """Look up a component by its name."""
        entry = self._catalog.component_by_name(name)
        if entry is None:
            return None
        knowledge_entry = KnowledgeEntry(
            id=name,
            category="component",
            name=name,
            references=entry.references,
            tags=entry.tags,
        )
        return self._build_result(knowledge_entry)

    def query_all(self) -> list[KnowledgeEntry]:
        """Return all knowledge entries."""
        results: list[KnowledgeEntry] = []
        for ep in self._catalog.endpoints:
            results.append(
                KnowledgeEntry(
                    id=ep.path,
                    category="endpoint",
                    name=ep.path,
                    references=ep.references,
                    tags=ep.tags,
                )
            )
        for cap in self._catalog.capabilities:
            results.append(
                KnowledgeEntry(
                    id=getattr(cap, "name", str(cap)),
                    category="capability",
                    name=getattr(cap, "name", str(cap)),
                    references=getattr(cap, "references", {}),
                    tags=getattr(cap, "tags", ()),
                )
            )
        for mp in self._catalog.mappers:
            results.append(
                KnowledgeEntry(
                    id=mp.name,
                    category="mapper",
                    name=mp.name,
                    references=mp.references,
                    tags=mp.tags,
                )
            )
        for vm in self._catalog.view_models:
            results.append(
                KnowledgeEntry(
                    id=vm.name,
                    category="viewModel",
                    name=vm.name,
                    references=vm.references,
                    tags=vm.tags,
                )
            )
        for ws in self._catalog.workspaces:
            results.append(
                KnowledgeEntry(
                    id=ws.name,
                    category="workspace",
                    name=ws.name,
                    references=ws.references,
                    tags=ws.tags,
                )
            )
        for comp in self._catalog.components:
            results.append(
                KnowledgeEntry(
                    id=comp.name,
                    category="component",
                    name=comp.name,
                    references=comp.references,
                    tags=comp.tags,
                )
            )
        for gr in self._catalog.graph_renderers:
            results.append(
                KnowledgeEntry(
                    id=gr.name,
                    category="graphRenderer",
                    name=gr.name,
                    references=gr.references,
                    tags=gr.tags,
                )
            )
        for vp in self._catalog.verification_profiles:
            results.append(
                KnowledgeEntry(
                    id=vp.name,
                    category="verificationProfile",
                    name=vp.name,
                    references=vp.references,
                    tags=vp.tags,
                )
            )
        for rule in self._catalog.integrity_rules:
            results.append(
                KnowledgeEntry(
                    id=rule.rule_id,
                    category="integrityRule",
                    name=rule.rule_id,
                    references=rule.references,
                    tags=rule.tags,
                )
            )
        for ra in self._catalog.runtime_artifacts:
            results.append(
                KnowledgeEntry(
                    id=ra.path,
                    category="runtimeArtifact",
                    name=ra.path,
                    references=ra.references,
                    tags=ra.tags,
                )
            )
        for doc in self._catalog.documentation:
            results.append(
                KnowledgeEntry(
                    id=doc.path,
                    category="documentation",
                    name=doc.title,
                    references=doc.references,
                    tags=doc.tags,
                )
            )
        return results

    def _build_result(self, entry: KnowledgeEntry) -> QueryResult:
        ownership = self._resolve_ownership(entry)
        dependencies = self._resolve_dependencies(entry)
        verification_profile = self._resolve_verification_profile(entry)
        integrity_rules = self._resolve_integrity_rules(entry)
        documentation_references = self._resolve_documentation(entry)
        related_artifacts = self._resolve_related_artifacts(entry)

        return QueryResult(
            entry=entry,
            ownership=ownership,
            dependencies=tuple(dependencies),
            verification_profile=verification_profile,
            integrity_rules=tuple(integrity_rules),
            documentation_references=tuple(documentation_references),
            related_artifacts=tuple(related_artifacts),
        )

    def _resolve_ownership(self, entry: KnowledgeEntry) -> dict[str, str]:
        ownership: dict[str, str] = {}
        refs = entry.references
        if "source_file" in refs:
            source = refs["source_file"]
            if "backend" in source:
                ownership["layer"] = "backend"
                ownership["owner"] = "backend"
            elif "frontend" in source:
                ownership["layer"] = "frontend"
                ownership["owner"] = "frontend"
            else:
                ownership["layer"] = "shared"
                ownership["owner"] = "runtime"
        return ownership

    def _resolve_dependencies(self, entry: KnowledgeEntry) -> list[str]:
        deps: list[str] = []
        for key, value in entry.references.items():
            if key not in ("source_file", "cross_layer_map"):
                deps.append(value)
        return deps

    def _resolve_verification_profile(self, entry: KnowledgeEntry) -> str | None:
        for vp in self._catalog.verification_profiles:
            if vp.name in entry.tags or vp.name in str(entry.references):
                return vp.name
        return None

    def _resolve_integrity_rules(self, entry: KnowledgeEntry) -> list[str]:
        rules: list[str] = []
        for rule in self._catalog.integrity_rules:
            if rule.rule_id in entry.tags or rule.rule_id in str(entry.references):
                rules.append(rule.rule_id)
        return rules

    def _resolve_documentation(self, entry: KnowledgeEntry) -> list[str]:
        docs: list[str] = []
        for doc in self._catalog.documentation:
            if doc.title in entry.tags or doc.path in str(entry.references):
                docs.append(doc.path)
        return docs

    def _resolve_related_artifacts(self, entry: KnowledgeEntry) -> list[str]:
        artifacts: list[str] = []
        for ra in self._catalog.runtime_artifacts:
            if ra.path in str(entry.references):
                artifacts.append(ra.path)
        return artifacts


def query_endpoint(path: str) -> QueryResult | None:
    """Look up an endpoint by its path."""
    return KnowledgeQueryEngine().query_endpoint(path)


def query_capability(name: str) -> QueryResult | None:
    """Look up a capability by its name."""
    return KnowledgeQueryEngine().query_capability(name)


def query_workspace(name: str) -> QueryResult | None:
    """Look up a workspace by its name."""
    return KnowledgeQueryEngine().query_workspace(name)


def query_rule(rule_id: str) -> QueryResult | None:
    """Look up an integrity rule by its ID."""
    return KnowledgeQueryEngine().query_rule(rule_id)


def query_component(name: str) -> QueryResult | None:
    """Look up a component by its name."""
    return KnowledgeQueryEngine().query_component(name)
