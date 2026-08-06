"""Tests for the Engineering Knowledge Base query engine — Program 11.

Deterministic tests. No network. No repository mutation.
"""

from __future__ import annotations

import pytest

from runtime.foundation.knowledge.catalog import KnowledgeCatalog
from runtime.foundation.knowledge.indexer import build_index
from runtime.foundation.knowledge.models import (
    EndpointEntry,
    IntegrityRuleEntry,
    QueryResult,
)
from runtime.foundation.knowledge.query import (
    KnowledgeQueryEngine,
    query_capability,
    query_component,
    query_endpoint,
    query_rule,
    query_workspace,
)
from runtime.foundation.knowledge.references import (
    ReferenceEngine,
    resolve_component,
)


class TestKnowledgeQueries:
    """Tests for the KnowledgeQueryEngine."""

    def test_query_endpoint_by_path(self) -> None:
        result = query_endpoint("/loans/{loan_id}/schedule")
        assert result is not None
        assert result.entry.category == "endpoint"

    def test_query_endpoint_not_found(self) -> None:
        result = query_endpoint("/api/nonexistent")
        assert result is None

    def test_query_capability_by_name(self) -> None:
        result = query_capability("useLoansCapability")
        assert result is not None
        assert result.entry.category == "capability"

    def test_query_capability_not_found(self) -> None:
        result = query_capability("nonexistentCapability")
        assert result is None

    def test_query_workspace_by_name(self) -> None:
        result = query_workspace("loans")
        assert result is not None
        assert result.entry.category == "workspace"

    def test_query_workspace_not_found(self) -> None:
        result = query_workspace("nonexistentWorkspace")
        assert result is None

    def test_query_rule_by_id(self) -> None:
        result = query_rule("ARCH-001")
        assert result is not None
        assert result.entry.category == "integrity_rule"

    def test_query_rule_not_found(self) -> None:
        result = query_rule("NONEXISTENT")
        assert result is None

    def test_query_component_by_name(self) -> None:
        result = query_component("components/loans/amortization-schedule")
        assert result is not None
        assert result.entry.category == "component"

    def test_query_component_not_found(self) -> None:
        result = query_component("nonexistentComponent")
        assert result is None


class TestKnowledgeQueryEngine:
    """Tests for the KnowledgeQueryEngine class."""

    def test_engine_has_catalog(self) -> None:
        engine = KnowledgeQueryEngine()
        assert engine._catalog is not None

    def test_engine_query_all(self) -> None:
        engine = KnowledgeQueryEngine()
        all_entries = engine.query_all()
        assert len(all_entries) >= 130


class TestQueryResult:
    """Tests for QueryResult structure."""

    def test_result_has_entry(self) -> None:
        result = query_endpoint("/loans/{loan_id}/schedule")
        assert result is not None
        assert result.entry is not None

    def test_result_has_dependencies(self) -> None:
        result = query_endpoint("/loans/{loan_id}/schedule")
        assert result is not None
        assert len(result.dependencies) >= 1

    def test_result_has_verification_profile(self) -> None:
        result = query_endpoint("/loans/{loan_id}/schedule")
        assert result is not None
        assert result.verification_profile == "backend"

    def test_result_has_integrity_rules(self) -> None:
        result = query_rule("ARCH-001")
        assert result is not None
        assert result.integrity_rules is not None

    def test_result_has_related_artifacts(self) -> None:
        result = query_endpoint("/loans/{loan_id}/schedule")
        assert result is not None
        # Canonical endpoints are not embedded in runtime-artifact references, so
        # related artifacts may legitimately be empty for an endpoint.
        assert isinstance(result.related_artifacts, (list, tuple))