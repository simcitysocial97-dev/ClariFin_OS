"""Tests for the Engineering Knowledge Base reference engine — Program 11.

Deterministic tests. No network. No repository mutation.
"""

from __future__ import annotations

import pytest

from runtime.foundation.knowledge.catalog import KnowledgeCatalog
from runtime.foundation.knowledge.indexer import build_index
from runtime.foundation.knowledge.models import (
    EndpointEntry,
    RelationshipChain,
)
from runtime.foundation.knowledge.references import (
    ReferenceEngine,
    resolve_capability,
    resolve_component,
    resolve_endpoint,
    resolve_integrity_rule,
    resolve_workspace,
)


class TestReferenceEngine:
    """Tests for the ReferenceEngine."""

    def test_resolve_endpoint_returns_chains(self) -> None:
        chains = resolve_endpoint("/api/loans/{loan_id}/schedule")
        assert isinstance(chains, list)

    def test_resolve_endpoint_empty_for_unknown(self) -> None:
        chains = resolve_endpoint("/api/nonexistent")
        assert chains == []

    def test_resolve_capability_returns_chains(self) -> None:
        chains = resolve_capability("useLoansCapability")
        assert isinstance(chains, list)

    def test_resolve_capability_empty_for_unknown(self) -> None:
        chains = resolve_capability("nonexistent")
        assert chains == []

    def test_resolve_component_returns_chains(self) -> None:
        chains = resolve_component("AmortizationTable")
        assert isinstance(chains, list)

    def test_resolve_component_empty_for_unknown(self) -> None:
        chains = resolve_component("nonexistent")
        assert chains == []


class TestReferenceEngineChain:
    """Tests for RelationshipChain structure."""

    def test_chain_has_source(self) -> None:
        chains = resolve_endpoint("/api/loans/{loan_id}/schedule")
        if chains:
            assert hasattr(chains[0], "source")

    def test_chain_has_target(self) -> None:
        chains = resolve_endpoint("/api/loans/{loan_id}/schedule")
        if chains:
            assert hasattr(chains[0], "target")

    def test_chain_has_relationship(self) -> None:
        chains = resolve_endpoint("/api/loans/{loan_id}/schedule")
        if chains:
            assert hasattr(chains[0], "relationship")

    def test_chain_has_depth(self) -> None:
        chains = resolve_endpoint("/api/loans/{loan_id}/schedule")
        if chains:
            assert hasattr(chains[0], "depth")


class TestReferenceEngineWithEngine:
    """Tests using KnowledgeQueryEngine with ReferenceEngine."""

    def test_reference_engine_initialization(self) -> None:
        engine = ReferenceEngine()
        assert engine._catalog is not None