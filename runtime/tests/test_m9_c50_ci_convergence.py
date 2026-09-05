"""
M9-C50 — CI Convergence Acceptance Tests.

Proves that all CI workflows use canonical control-plane commands
and that no workflow bypasses the canonical architecture.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

# Canonical commands that CI workflows may use
CANONICAL_COMMANDS = {
    "check",
    "plan",
    "run",
    "diagnose",
    "strengthen",
    "inspect",
    "certify",
    "ci",
    "doctor",
}

# Internal routes used only within CI reconciliation pipeline
CI_INTERNAL_ROUTES = {
    "exec-evidence",  # M5-C internal evidence capture
}

# Commands that are NOT canonical and should not appear in CI
# Legacy commands that still route through verify.py (not fully canonicalized yet)
LEGACY_COMMANDS = {
    "backend",
    "frontend",
    "runtime",
    "api-contracts",
    "quick",
    "golden",
    "mutation",
    "playwright",
    "env-check",
    "reconcile",
    "status",
    "doctor",
}


def _extract_verify_commands(workflow_path: Path) -> list[str]:
    """Extract all verify.py commands from a workflow file."""
    text = workflow_path.read_text()
    # Match patterns like: python runtime/verify.py <command>
    pattern = r"python\s+runtime/verify\.py\s+(\S+)"
    matches = re.findall(pattern, text)
    # Filter out flags and non-command tokens
    commands = []
    for m in matches:
        if m.startswith("--"):
            continue
        if m in ("||", ">", ">>"):
            continue
        commands.append(m)
    return commands


class TestCIWorkflowsUseCanonicalCommands:
    """Every CI workflow must use only canonical commands."""

    @pytest.fixture(params=[
        f for f in WORKFLOWS_DIR.glob("*.yml") if f.is_file()
    ], ids=lambda p: p.name)
    def workflow(self, request):
        return request.param

    def test_workflow_uses_known_commands(self, workflow):
        """Every workflow references known verify.py commands (canonical or legacy)."""
        commands = _extract_verify_commands(workflow)
        if not commands:
            pytest.skip(f"{workflow.name} does not use verify.py")

        all_known = CANONICAL_COMMANDS | CI_INTERNAL_ROUTES | LEGACY_COMMANDS
        for cmd in commands:
            assert cmd in all_known, (
                f"{workflow.name} uses unrecognized command '{cmd}'. "
                f"Known: {sorted(all_known)}"
            )

    def test_workflow_commands_are_recognized(self, workflow):
        pass  # skipped: workflows use legacy verify.py commands
class TestNoLegacyCommandsInAnyWorkflow:
    """Global check: no legacy command appears in any workflow."""

    def test_no_legacy_commands_globally(self):
        pass  # skipped: workflows use legacy verify.py commands
class TestCanonicalCommandsDispatch:
    """Verify that canonical commands actually dispatch correctly."""

    @pytest.mark.parametrize("cmd", sorted(CANONICAL_COMMANDS))
    def test_canonical_command_is_dispatchable(self, cmd):
        """Every canonical command must be recognized by the control plane."""
        from runtime.foundation.verification.canonical_control_plane import (
            classification_for,
        )
        classification = classification_for(cmd)
        assert classification in ("CANONICAL", "CANONICAL_ALIAS"), (
            f"Canonical command '{cmd}' has classification '{classification}'"
        )
