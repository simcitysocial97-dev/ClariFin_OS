"""History Workspace Tests — Program 9.

Tests for history workspace rendering.
Deterministic golden outputs. No regeneration.
"""

from __future__ import annotations

import json
from pathlib import Path


from runtime.foundation.workspace.history import render_history
from runtime.foundation.workspace.workspace import WorkspaceLoader


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TestHistoryWorkspace:
    """Tests for history workspace rendering."""

    def test_render_history_output(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
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
                        "duration_seconds": 1.0,
                    }
                ],
                "ci": [
                    {
                        "run_id": "run-2",
                        "timestamp": "2026-01-02T00:00:00+00:00",
                        "environment": "ci",
                        "profile": "full",
                        "status": "failed",
                        "passed": 0,
                        "failed": 1,
                        "skipped": 0,
                        "duration_seconds": 2.0,
                    }
                ],
                "combined": [],
            },
        )
        history = loader.load_history_events()
        output = render_history(history)
        assert "Recent Verification Events" in output
        assert "Timeline" in output
        assert "Verification Trends" in output
        assert "run-1" in output
        assert "run-2" in output

    def test_render_history_no_events(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-history.json",
            {"local": [], "ci": [], "combined": []},
        )
        history = loader.load_history_events()
        output = render_history(history)
        assert output.strip() == ""
