"""Tests for the Engineering Knowledge Base indexer — Program 11.

Deterministic tests. No network. No repository mutation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.foundation.knowledge.indexer import (
    build_index,
    save_index,
)
from runtime.foundation.knowledge.models import KnowledgeIndex


class TestKnowledgeIndexer:
    """Tests for the KnowledgeIndexer."""

    def test_build_index_returns_knowledge_index(self) -> None:
        index = build_index()
        assert isinstance(index, KnowledgeIndex)

    def test_index_has_endpoints(self) -> None:
        index = build_index()
        assert len(index.endpoints) >= 1

    def test_index_has_capabilities(self) -> None:
        index = build_index()
        assert len(index.capabilities) >= 1

    def test_index_has_mappers(self) -> None:
        index = build_index()
        assert len(index.mappers) >= 1

    def test_index_has_view_models(self) -> None:
        index = build_index()
        assert len(index.view_models) >= 1

    def test_index_has_workspaces(self) -> None:
        index = build_index()
        assert len(index.workspaces) >= 1

    def test_index_has_components(self) -> None:
        index = build_index()
        assert len(index.components) >= 1

    def test_index_has_verification_profiles(self) -> None:
        index = build_index()
        assert len(index.verification_profiles) >= 1

    def test_index_has_integrity_rules(self) -> None:
        index = build_index()
        assert len(index.integrity_rules) >= 1

    def test_index_has_runtime_artifacts(self) -> None:
        index = build_index()
        assert len(index.runtime_artifacts) >= 1

    def test_index_has_documentation(self) -> None:
        index = build_index()
        assert len(index.documentation) >= 1

    def test_index_deterministic(self) -> None:
        index1 = build_index()
        index2 = build_index()
        assert index1.endpoints == index2.endpoints
        assert index1.capabilities == index2.capabilities
        assert index1.integrity_rules == index2.integrity_rules

    def test_index_has_timestamp(self) -> None:
        index = build_index()
        assert index.indexed_at
        assert "T" in index.indexed_at

    def test_index_has_source_artifacts(self) -> None:
        index = build_index()
        assert len(index.source_artifacts) >= 1

    def test_save_index_creates_file(self, tmp_path: Path) -> None:
        index = build_index()
        output_path = tmp_path / "knowledge-index.json"
        result = save_index(index)
        assert result.exists()


class TestKnowledgeIndexerIntegration:
    """Integration tests for the KnowledgeIndexer."""

    def test_index_endpoint_from_cross_layer_map(self) -> None:
        index = build_index()
        endpoints = [ep for ep in index.endpoints if "loans" in ep.path]
        assert len(endpoints) >= 1

    def test_index_integrity_rules_from_registry(self) -> None:
        index = build_index()
        rule_ids = [r.rule_id for r in index.integrity_rules]
        assert any("ARCH" in rid for rid in rule_ids)