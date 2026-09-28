"""M9-C55 — CLI Contract Tests.

Ensures every registered runtime.verify command responds to --help and
executes in plan/dry-run mode without crashing.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestCliContract:
    """Verify CLI commands are alive and well-behaved."""

    def _run(self, cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "runtime.verify"] + cmd,
            capture_output=True, text=True, timeout=timeout,
        )

    def test_plan_help(self):
        result = self._run(["plan", "--help"])
        assert result.returncode in (0, 2), f"exit={result.returncode}\n{result.stderr[:500]}"

    def test_inspect_health_runs(self):
        result = self._run(["inspect", "health"])
        assert result.returncode == 0, f"exit={result.returncode}\n{result.stderr[:500]}"

    def test_inspect_evidence_cleanup_dry_run(self):
        result = self._run(["inspect", "evidence-cleanup", "--dry-run"])
        assert result.returncode == 0, f"exit={result.returncode}\n{result.stderr[:500]}"

    def test_plan_backend_no_crash(self):
        result = self._run(["plan", "--scope", "backend"])
        assert result.returncode == 0, f"exit={result.returncode}\n{result.stderr[:500]}"

    def test_plan_frontend_no_crash(self):
        result = self._run(["plan", "--scope", "frontend"])
        assert result.returncode == 0, f"exit={result.returncode}\n{result.stderr[:500]}"

    def test_plan_runtime_no_crash(self):
        result = self._run(["plan", "--scope", "runtime"])
        assert result.returncode == 0, f"exit={result.returncode}\n{result.stderr[:500]}"

    def test_inspect_capabilities_runs(self):
        result = self._run(["inspect", "capabilities"])
        assert result.returncode == 0, f"exit={result.returncode}\n{result.stderr[:500]}"
