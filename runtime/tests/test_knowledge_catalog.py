"""Tests for the Engineering Knowledge Base catalog — Program 11.

Deterministic tests. No network. No repository mutation.
"""

from __future__ import annotations


from runtime.foundation.knowledge.catalog import (
    KnowledgeCatalog,
    get_catalog,
    set_catalog,
)
from runtime.foundation.knowledge.models import (
    EndpointEntry,
    WorkspaceEntry,
)


class TestKnowledgeCatalog:
    """Tests for the KnowledgeCatalog."""

    def test_catalog_empty_by_default(self) -> None:
        catalog = KnowledgeCatalog()
        assert len(catalog.endpoints) == 0
        assert len(catalog.capabilities) == 0
        assert len(catalog.workspaces) == 0
        assert len(catalog.integrity_rules) == 0

    def test_catalog_endpoint_lookup(self) -> None:
        catalog = KnowledgeCatalog()
        endpoint = EndpointEntry(
            path="/api/test",
            method="GET",
            references={},
            tags=(),
        )
        catalog_with_ep = KnowledgeCatalog(endpoints=(endpoint,))
        result = catalog_with_ep.endpoint_by_path("/api/test")
        assert result is not None
        assert result.path == "/api/test"

    def test_catalog_endpoint_not_found(self) -> None:
        catalog = KnowledgeCatalog()
        result = catalog.endpoint_by_path("/api/nonexistent")
        assert result is None

    def test_catalog_workspace_lookup(self) -> None:
        catalog = KnowledgeCatalog()
        workspace = WorkspaceEntry(
            name="TestWorkspace",
            references={},
            tags=(),
        )
        catalog_with_ws = KnowledgeCatalog(workspaces=(workspace,))
        result = catalog_with_ws.workspace_by_name("TestWorkspace")
        assert result is not None
        assert result.name == "TestWorkspace"

    def test_catalog_workspace_not_found(self) -> None:
        catalog = KnowledgeCatalog()
        result = catalog.workspace_by_name("nonexistent")
        assert result is None


class TestCatalogSingleton:
    """Tests for the catalog singleton pattern."""

    def test_get_catalog_returns_catalog(self) -> None:
        catalog = get_catalog()
        assert isinstance(catalog, KnowledgeCatalog)

    def test_set_catalog_sets_singleton(self) -> None:
        new_catalog = KnowledgeCatalog()
        set_catalog(new_catalog)
        assert get_catalog() is new_catalog