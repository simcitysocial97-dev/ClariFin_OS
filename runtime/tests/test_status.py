"""Status Workspace Tests — Program 9.

Tests for status workspace rendering.
Deterministic golden outputs. No regeneration.
"""

from __future__ import annotations

import json
from pathlib import Path


from runtime.foundation.workspace.status import render_status
from runtime.foundation.workspace.workspace import WorkspaceLoader


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TestStatusWorkspace:
    """Tests for status workspace rendering."""

    def test_render_status_output(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "verification-cache.json",
            {
                "last_commit": "abc123def456",
                "changed_files": ["a.py", "b.py"],
                "executed_profiles": ["quick"],
                "duration": 1.5,
                "timestamp": "2026-01-01T00:00:00+00:00",
            },
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-history.json",
            {
                "local": [
                    {
                        "run_id": "run-1",
                        "timestamp": "2026-01-01T00:00:00+00:00",
                        "environment": "local",
                        "profile": "quick",
                        "status": "passed",
                        "passed": 5,
                        "failed": 0,
                        "skipped": 1,
                        "duration_seconds": 1.2,
                    }
                ],
                "ci": [],
                "combined": [],
            },
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-analytics.json",
            {
                "local": {
                    "verification": {"success_rate": 1.0, "avg_duration_seconds": 1.2},
                    "cache": {"hit_rate": 1.0},
                },
                "ci": {
                    "verification": {"success_rate": 0.0, "avg_duration_seconds": 0.0},
                    "cache": {"hit_rate": 0.0},
                },
                "combined": {
                    "verification": {"success_rate": 1.0, "avg_duration_seconds": 1.2},
                    "cache": {"hit_rate": 1.0},
                },
            },
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "cross-layer-map.json",
            {
                "a.py": {
                    "engine": "a.py",
                    "services": [],
                    "routers": [],
                    "endpoints": [],
                    "capabilities": [],
                    "mappers": [],
                    "viewModels": [],
                    "pages": [],
                    "workspace": [],
                    "components": [],
                    "tests": [],
                    "graphRenderers": [],
                }
            },
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "dependency-growth.json",
            {},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "cost-analysis.json",
            {},
        )
        workspace = loader.load_status_workspace()
        output = render_status(workspace)
        assert "Repository Status" in output
        assert "abc123de" in output
        assert "Verification Status" in output
        assert "Engineering Health" in output
        assert "Cross-Layer Status" in output

    def test_render_status_with_failures(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "verification-cache.json",
            {
                "last_commit": "abc",
                "changed_files": [],
                "executed_profiles": [],
                "duration": 0,
                "timestamp": "",
            },
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-history.json",
            {
                "local": [
                    {
                        "run_id": "run-fail",
                        "timestamp": "2026-01-02T00:00:00+00:00",
                        "environment": "local",
                        "profile": "backend",
                        "status": "failed",
                        "failed": 3,
                    }
                ],
                "ci": [],
                "combined": [],
            },
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-analytics.json",
            {},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "cross-layer-map.json",
            {},
        )
        workspace = loader.load_status_workspace()
        output = render_status(workspace)
        assert "Recent Failures" in output
        assert "backend" in output
