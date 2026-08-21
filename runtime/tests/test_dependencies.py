"""Dependency Explorer Tests — Program 9.

Tests for dependency explorer rendering.
Deterministic golden outputs. No regeneration.
"""

from __future__ import annotations

import json
from pathlib import Path


from runtime.foundation.workspace.dependencies import render_dependencies
from runtime.foundation.workspace.workspace import WorkspaceLoader


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TestDependencyExplorer:
    """Tests for dependency explorer."""

    def test_render_dependencies_found(self, tmp_path: Path):
        loader = WorkspaceLoader(
            repo_root=tmp_path,
            chain_map={
                "backend/src/engines/loan_engine/amortization.py": {
                    "engine": "backend/src/engines/loan_engine/amortization.py",
                    "services": ["LoanService"],
                    "routers": ["backend/src/routers/loans.py"],
                    "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                    "capabilities": ["useLoansCapability"],
                    "mappers": ["loansMapper"],
                    "viewModels": ["LoansViewModel"],
                    "pages": ["app/loans/page.tsx"],
                    "workspace": ["LoansWorkspace"],
                    "components": ["AmortizationTable"],
                    "tests": ["backend/tests/unit/engines/loan/test_amortization.py"],
                    "graphRenderers": [],
                }
            },
        )
        result = loader.load_dependency_chain(
            "backend/src/engines/loan_engine/amortization.py"
        )
        output = render_dependencies(result)
        assert "Dependency Chain" in output
        assert "LoanService" in output
        assert "AmortizationTable" in output
        assert "backend/tests/unit/engines/loan/test_amortization.py" in output

    def test_render_dependencies_not_found(self, tmp_path: Path):
        loader = WorkspaceLoader(
            repo_root=tmp_path,
            chain_map={},
        )
        result = loader.load_dependency_chain("nonexistent.py")
        output = render_dependencies(result)
        assert "No dependency chain found" in output

    def test_load_dependency_chain_empty_entry(self, tmp_path: Path):
        loader = WorkspaceLoader(
            repo_root=tmp_path,
            chain_map={"file.py": {}},
        )
        result = loader.load_dependency_chain("file.py")
        assert result.found is True
        assert result.chain is not None
        assert result.chain.engine is None
