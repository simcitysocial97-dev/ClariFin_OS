"""Scanner Tests — Program 10.

Tests for ArchitecturalScanner using synthetic source files.
Deterministic. No network. No git mutation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.integrity.scanner import (
    ArchitecturalGraph,
    ArchitecturalScanner,
    classify_layer,
    discover_source_files,
)
from runtime.foundation.integrity.models import ArchitectureLayer


class TestClassifyLayer:
    """Tests for layer classification."""

    def test_backend_engine(self) -> None:
        assert classify_layer("backend/src/engines/loan_engine/amortization.py") == ArchitectureLayer.BACKEND_ENGINE

    def test_backend_service(self) -> None:
        assert classify_layer("backend/src/services/loan_service.py") == ArchitectureLayer.BACKEND_SERVICE

    def test_backend_router(self) -> None:
        assert classify_layer("backend/src/routers/loans.py") == ArchitectureLayer.BACKEND_ROUTER

    def test_backend_dto(self) -> None:
        assert classify_layer("backend/src/core/dtos/loan_dto.py") == ArchitectureLayer.BACKEND_DTO

    def test_backend_repository(self) -> None:
        assert classify_layer("backend/src/repositories/loan_repo.py") == ArchitectureLayer.BACKEND_REPOSITORY

    def test_frontend_api(self) -> None:
        assert classify_layer("frontend/lib/api/client.ts") == ArchitectureLayer.FRONTEND_API

    def test_frontend_capability(self) -> None:
        assert classify_layer("frontend/lib/capabilities/use-loans-capability.ts") == ArchitectureLayer.FRONTEND_CAPABILITY

    def test_frontend_mapper(self) -> None:
        assert classify_layer("frontend/lib/mappers/loans-mapper.ts") == ArchitectureLayer.FRONTEND_MAPPER

    def test_frontend_viewmodel(self) -> None:
        assert classify_layer("frontend/types/loans-view-model.ts") == ArchitectureLayer.FRONTEND_VIEWMODEL

    def test_frontend_workspace(self) -> None:
        assert classify_layer("frontend/lib/workspace/workspace-context.ts") == ArchitectureLayer.FRONTEND_WORKSPACE

    def test_frontend_component(self) -> None:
        assert classify_layer("frontend/components/dashboard/card.tsx") == ArchitectureLayer.FRONTEND_COMPONENT

    def test_frontend_page(self) -> None:
        assert classify_layer("frontend/app/loans/page.tsx") == ArchitectureLayer.FRONTEND_PAGE

    def test_unknown_file(self) -> None:
        assert classify_layer("backend/src/config.py") == ArchitectureLayer.UNKNOWN

    def test_non_project_file(self) -> None:
        assert classify_layer("docs/README.md") == ArchitectureLayer.UNKNOWN


class TestDiscoverSourceFiles:
    """Tests for source file discovery."""

    def test_discovery_is_deterministic(self, tmp_path: Path) -> None:
        # Create a minimal repo structure
        (tmp_path / "backend" / "src" / "engines").mkdir(parents=True)
        (tmp_path / "backend" / "src" / "services").mkdir(parents=True)
        (tmp_path / "backend" / "src" / "routers").mkdir(parents=True)
        (tmp_path / "frontend" / "lib" / "capabilities").mkdir(parents=True)
        (tmp_path / "frontend" / "components").mkdir(parents=True)
        (tmp_path / "frontend" / "app").mkdir(parents=True)

        (tmp_path / "backend" / "src" / "engines" / "loan_engine.py").write_text("")
        (tmp_path / "backend" / "src" / "services" / "loan_service.py").write_text("")
        (tmp_path / "backend" / "src" / "routers" / "loans.py").write_text("")
        (tmp_path / "frontend" / "lib" / "capabilities" / "use-loans.ts").write_text("")
        (tmp_path / "frontend" / "components" / "card.tsx").write_text("")
        page_dir = tmp_path / "frontend" / "app" / "loans"
        page_dir.mkdir(parents=True)
        (page_dir / "page.tsx").write_text("")

        files = discover_source_files(tmp_path)
        assert len(files) == 6
        assert files == sorted(files)

    def test_excludes_test_files(self, tmp_path: Path) -> None:
        (tmp_path / "backend" / "src" / "services").mkdir(parents=True)
        (tmp_path / "backend" / "src" / "services" / "loan_service.py").write_text("")
        (tmp_path / "backend" / "src" / "services" / "test_loan_service.py").write_text("")

        files = discover_source_files(tmp_path)
        assert len(files) == 1
        assert "test_loan_service.py" not in files[0]

    def test_excludes_init_files(self, tmp_path: Path) -> None:
        (tmp_path / "backend" / "src" / "services").mkdir(parents=True)
        (tmp_path / "backend" / "src" / "services" / "__init__.py").write_text("")
        (tmp_path / "backend" / "src" / "services" / "loan_service.py").write_text("")

        files = discover_source_files(tmp_path)
        assert len(files) == 1

    def test_excludes_pycache(self, tmp_path: Path) -> None:
        (tmp_path / "backend" / "src" / "services" / "__pycache__").mkdir(parents=True)
        (tmp_path / "backend" / "src" / "services" / "__pycache__" / "loan_service.cpython-312.pyc").write_text("")
        (tmp_path / "backend" / "src" / "services" / "loan_service.py").write_text("")

        files = discover_source_files(tmp_path)
        assert len(files) == 1


class TestArchitecturalScanner:
    """Tests for ArchitecturalScanner."""

    def test_scan_with_real_repo(self) -> None:
        scanner = ArchitecturalScanner()
        graph = scanner.scan()
        assert graph.files_scanned >= 0
        assert isinstance(graph.cross_layer_map, dict)
        assert isinstance(graph.graph_nodes, tuple)
        assert isinstance(graph.graph_edges, tuple)

    def test_scan_produces_deterministic_results(self) -> None:
        scanner = ArchitecturalScanner()
        graph1 = scanner.scan()
        graph2 = scanner.scan()
        assert graph1.files_scanned == graph2.files_scanned
        assert graph1.files == graph2.files

    def test_scan_with_missing_cross_layer_map(self, tmp_path: Path) -> None:
        scanner = ArchitecturalScanner(
            repo_root=tmp_path,
            cross_layer_map_path=tmp_path / "nonexistent" / "map.json",
            graph_index_path=tmp_path / "nonexistent" / "index.json",
        )
        graph = scanner.scan()
        assert graph.files_scanned == 0
        assert len(graph.cross_layer_map) == 0
        assert len(graph.scan_errors) > 0

    def test_scan_with_empty_repo(self, tmp_path: Path) -> None:
        # Program 13.3: chains come from the provider; an explicit empty map is
        # injected to verify isolated behaviour.
        map_path = tmp_path / "runtime" / "generated" / "cross-layer-map.json"
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text("{}", encoding="utf-8")
        scanner = ArchitecturalScanner(
            repo_root=tmp_path, cross_layer_map_path=map_path
        )
        graph = scanner.scan()
        assert graph.files_scanned == 0
        assert len(graph.cross_layer_map) == 0

    def test_scan_loads_cross_layer_map(self) -> None:
        scanner = ArchitecturalScanner()
        graph = scanner.scan()
        # The real repo has a cross-layer map
        assert isinstance(graph.cross_layer_map, dict)

    def test_scan_loads_graph_index(self) -> None:
        scanner = ArchitecturalScanner()
        graph = scanner.scan()
        assert isinstance(graph.graph_nodes, tuple)
        assert isinstance(graph.graph_edges, tuple)