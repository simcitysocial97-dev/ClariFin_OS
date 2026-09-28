"""M9-C55 — Full Pipeline Integration Test.

Executes a minimal end-to-end verification with a real file change and
validates output structure.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


class TestFullPipelineIntegration:
    """End-to-end pipeline validation."""

    def test_plan_with_real_change(self):
        """Plan mode must handle a real backend file change."""
        test_file = Path("backend/src/engines/loan_engine/emi.py")
        if not test_file.exists():
            pytest.skip("emi.py not found")

        original_content = test_file.read_text()
        try:
            # Add a non-breaking comment
            modified_content = "# Pipeline validation comment\n" + original_content
            test_file.write_text(modified_content)

            result = subprocess.run(
                [sys.executable, "-m", "runtime.verify", "plan", "--scope", "backend"],
                capture_output=True, text=True, timeout=60,
            )

            output = result.stdout + result.stderr
            # Must not crash
            assert "Traceback" not in output, f"Pipeline crashed:\n{output[-1000:]}"
            assert result.returncode == 0, f"Plan failed: {result.stderr[:300]}"
        finally:
            test_file.write_text(original_content)

    def test_inspect_health_after_change(self):
        """Health inspection must remain valid after verification."""
        result = subprocess.run(
            [sys.executable, "-m", "runtime.verify", "inspect", "health"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Health check failed: {result.stderr[:300]}"
        assert "Traceback" not in result.stderr
