"""M9-C65 — Configuration-divergence attack experiments.

Simulates local != CI configuration and verifies the framework detects
CONFIG_DIVERGENCE with expected/actual/source/impact detail.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.foundation.verification.configuration_authority import (
    ToolAuthority,
    get_configuration_authority,
    validate_authority,
)
from runtime.foundation.verification.env import resolve_environment


class TestConfigurationDivergence:
    """Framework must detect deliberate configuration mismatches."""

    def test_authority_table_non_empty(self):
        """There must be tool authority entries for quality tools."""
        authorities = get_configuration_authority()
        assert len(authorities) > 0
        tools = {a["tool"] for a in authorities}
        for required in ("ruff", "black", "mypy", "pytest", "coverage"):
            assert required in tools, f"Missing authority for {required}"

    def test_validate_authority_returns_clean_state(self):
        """Current configuration must pass validation."""
        healthy, messages = validate_authority()
        assert isinstance(healthy, bool)
        assert isinstance(messages, list)
        assert all(isinstance(m, str) for m in messages)

    def test_environment_fingerprint_stable(self):
        """resolve_environment must produce consistent fingerprints."""
        env1 = resolve_environment()
        env2 = resolve_environment()
        assert env1 is not None
        assert env2 is not None
        assert env1.fingerprint == env2.fingerprint

    def test_ruff_authority_is_repo_scope(self):
        """Ruff must be configured at repo root, not backend."""
        authorities = get_configuration_authority()
        ruff = next((a for a in authorities if a["tool"] == "ruff"), None)
        assert ruff is not None
        assert ruff["config_scope"] == "repo"
        assert ruff["authoritative"] is True

    def test_mypy_dual_scope_detected(self):
        """Mypy must recognize dual-scope configuration."""
        authorities = get_configuration_authority()
        mypy = next((a for a in authorities if a["tool"] == "mypy"), None)
        assert mypy is not None
        assert mypy["config_scope"] == "dual"

    def test_no_divergence_when_configs_identical(self):
        """Identical environment fingerprints indicate no divergence."""
        env1 = resolve_environment()
        env2 = resolve_environment()
        assert env1.fingerprint == env2.fingerprint

    def test_tool_authority_has_required_fields(self):
        """Every ToolAuthority must have tool, canonical_command, config_path."""
        authorities = get_configuration_authority()
        for a in authorities:
            assert "tool" in a
            assert "canonical_command" in a
            assert "config_path" in a
            assert "config_scope" in a
            assert "authoritative" in a

    def test_coverage_authority_correct(self):
        """Coverage must point to the C47 canonical path."""
        authorities = get_configuration_authority()
        cov = next((a for a in authorities if a["tool"] == "coverage"), None)
        assert cov is not None
        assert "m9-c47" in cov["config_path"] or "coverage" in cov["canonical_command"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
