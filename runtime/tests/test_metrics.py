"""Metrics Workspace Tests — Program 9.

Tests for metrics workspace rendering.
Deterministic golden outputs. No regeneration.
"""

from __future__ import annotations

import json
from pathlib import Path


from runtime.foundation.workspace.metrics import render_metrics
from runtime.foundation.workspace.workspace import WorkspaceLoader


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TestMetricsWorkspace:
    """Tests for metrics workspace rendering."""

    def test_render_metrics_output(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-analytics.json",
            {
                "local": {
                    "verification": {"total_runs": 10, "passed_runs": 8, "failed_runs": 2, "skipped_runs": 0, "success_rate": 0.8, "avg_duration_seconds": 1.0, "min_duration_seconds": 0.5, "max_duration_seconds": 1.5},
                    "cache": {"hit_rate": 0.5, "hits": 2, "total": 4},
                },
                "ci": {
                    "verification": {"total_runs": 5, "passed_runs": 5, "failed_runs": 0, "skipped_runs": 0, "success_rate": 1.0, "avg_duration_seconds": 2.0, "min_duration_seconds": 1.0, "max_duration_seconds": 3.0},
                    "cache": {"hit_rate": 0.0, "hits": 0, "total": 5},
                },
                "combined": {
                    "verification": {"total_runs": 15, "passed_runs": 13, "failed_runs": 2, "skipped_runs": 0, "success_rate": 0.867, "avg_duration_seconds": 1.333, "min_duration_seconds": 0.5, "max_duration_seconds": 3.0},
                    "cache": {"hit_rate": 0.133, "hits": 2, "total": 15},
                },
            },
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "flaky-tests.json",
            {"flaky_tests": ["test_a"]},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "dependency-growth.json",
            {
                "engines": {"category": "engines", "current_count": 4, "previous_count": 4, "delta": 0, "growth_rate": 0.0},
            },
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "cross-layer-map.json",
            {},
        )
        workspace = loader.load_metrics_workspace()
        output = render_metrics(workspace)
        assert "Verification Counts" in output
        assert "Local vs CI Metrics" in output
        assert "Cache Hit Rate" in output
        assert "Average Duration" in output
        assert "Failure Rate" in output
        assert "Flaky Tests" in output
        assert "Dependency Growth" in output
        assert "Risk Distribution" in output
        assert "test_a" in output
