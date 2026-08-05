"""Engineering Knowledge Base (EKB) — Program 11.

Deterministic engineering knowledge system that indexes, correlates,
and exposes engineering knowledge already produced by the runtime.

The Knowledge Base is read-only. It consumes runtime artifacts from
Programs 7–10 and creates searchable indexes. It never generates
new engineering facts, performs AI reasoning, or duplicates runtime
calculations.

Usage:
    python runtime/verify.py knowledge
    python runtime/verify.py knowledge endpoint /api/v1/loans
    python runtime/verify.py knowledge capability useLoansCapability
    python runtime/verify.py knowledge workspace loans
    python runtime/verify.py knowledge rule ARCH-002
    python runtime/verify.py knowledge component AmortizationTable
"""

from __future__ import annotations

from runtime.foundation.knowledge.catalog import (
    KnowledgeCatalog,
    get_catalog,
)
from runtime.foundation.knowledge.formatter import (
    format_knowledge_report,
    format_query_result,
    format_catalog_summary,
)
from runtime.foundation.knowledge.indexer import (
    build_index,
)
from runtime.foundation.knowledge.models import (
    ComponentEntry,
    DocumentationEntry,
    EndpointEntry,
    GraphRendererEntry,
    IntegrityRuleEntry,
    KnowledgeEntry,
    KnowledgeIndex,
    MapperEntry,
    QueryResult,
    RelationshipChain,
    RuntimeArtifactEntry,
    VerificationProfileEntry,
    ViewModelEntry,
    WorkspaceEntry,
)
from runtime.foundation.knowledge.query import (
    KnowledgeQueryEngine,
    query_endpoint,
    query_capability,
    query_workspace,
    query_rule,
    query_component,
)
from runtime.foundation.knowledge.references import (
    ReferenceEngine,
    resolve_endpoint,
    resolve_capability,
    resolve_mapper,
    resolve_viewmodel,
    resolve_workspace,
    resolve_component,
    resolve_test,
    resolve_verification_profile,
    resolve_integrity_rule,
    resolve_documentation,
)

__all__ = [
    "KnowledgeCatalog",
    "get_catalog",
    "build_index",
    "KnowledgeQueryEngine",
    "query_endpoint",
    "query_capability",
    "query_workspace",
    "query_rule",
    "query_component",
    "ReferenceEngine",
    "resolve_endpoint",
    "resolve_capability",
    "resolve_mapper",
    "resolve_viewmodel",
    "resolve_workspace",
    "resolve_component",
    "resolve_test",
    "resolve_verification_profile",
    "resolve_integrity_rule",
    "resolve_documentation",
    "format_knowledge_report",
    "format_query_result",
    "format_catalog_summary",
    "KnowledgeEntry",
    "EndpointEntry",
    "CapabilityEntry",
    "MapperEntry",
    "ViewModelEntry",
    "WorkspaceEntry",
    "ComponentEntry",
    "GraphRendererEntry",
    "VerificationProfileEntry",
    "IntegrityRuleEntry",
    "RuntimeArtifactEntry",
    "DocumentationEntry",
    "KnowledgeIndex",
    "QueryResult",
    "RelationshipChain",
]