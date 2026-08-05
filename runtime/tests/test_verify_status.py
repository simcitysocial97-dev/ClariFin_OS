"""Verification Workspace Tests — Program 9.

Tests for verification workspace rendering.
Deterministic golden outputs. No regeneration.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.workspace.verification import render_verification
from runtime.foundation.workspace.workspace import WorkspaceLoader


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TestVerificationWorkspace:
    """Tests for verification workspace rendering."""

    def test_render_verification_output(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "verification-cache.json",
            {
                "last_commit": "abc123",
                "changed_files": ["a.py"],
                "executed_profiles": ["quick", "backend"],
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
                        "duration_seconds": 1.0,
                    }
                ],
                "ci": [],
                "combined": [
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
            },
        )
        workspace = loader.load_verification_workspace()
        output = render_verification(workspace)
        assert "Verification Profiles" in output
        assert "Execution History" in output
        assert "Last Execution" in output
        assert "Pending Verification" in output
        assert "quick" in output

    def test_render_verification_no_executions(self, tmp_path: Path):
        loader = WorkspaceLoader(repo_root=tmp_path)
        _write_json(
            tmp_path / "runtime" / "generated" / "verification-cache.json",
            {"last_commit": "", "changed_files": [], "executed_profiles": [], "duration": 0, "timestamp": ""},
        )
        _write_json(
            tmp_path / "runtime" / "generated" / "engineering-history.json",
            {"local": [], "ci": [], "combined": []},
        )
        workspace = loader.load_verification_workspace()
        output = render_verification(workspace)
        assert "Pending Verification" in output
        assert "Pending Count" in output
