"""M9-C55 — Blast Radius Integration Tests.

Verifies the blast radius engine computes correctly and edge cases don't crash.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.foundation.verification.blast_radius import BlastRadiusEngine


class TestBlastRadiusIntegration:
    """End-to-end blast radius behavior checks."""

    def test_compute_returns_complete_contract(self):
        engine = BlastRadiusEngine()
        result = engine.compute(explicit_files=["backend/src/engines/loan_engine/emi.py"])
        d = result.to_dict()

        # Core fields must be present
        assert "contract_id" in d
        assert "schema" in d
        assert "generated_at" in d
        assert "change_surface" in d
        assert "capability_impacts" in d
        assert "surface_impacts" in d

        # Financial impact is reflected in capability impacts
        cap_impacts = d.get("capability_impacts", [])
        assert len(cap_impacts) > 0, "Expected at least one capability impact"

        # Frontend/backend classification present in change surface
        cs = d.get("change_surface", {})
        assert "changed_files" in cs
        assert "surfaces" in cs

    def test_router_change_triggers_capability_resolution(self):
        engine = BlastRadiusEngine()
        result = engine.compute(explicit_files=["backend/src/routers/accounts.py"])
        d = result.to_dict()
        # Should produce a valid contract even if no capabilities match
        assert "capability_impacts" in d
        assert isinstance(d["capability_impacts"], list)

    def test_blast_radius_handles_deleted_file(self):
        engine = BlastRadiusEngine()
        result = engine.compute(explicit_files=["backend/src/nonexistent.py"])
        assert result is not None
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "contract_id" in d

    def test_blast_radius_handles_new_file(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("def new_function(): pass\n")
            new_path = Path(f.name)
        try:
            engine = BlastRadiusEngine()
            result = engine.compute(explicit_files=[str(new_path)])
            assert result is not None
        finally:
            new_path.unlink(missing_ok=True)

    def test_verification_surfaces_populated(self):
        engine = BlastRadiusEngine()
        result = engine.compute(explicit_files=["backend/src/engines/loan_engine/emi.py"])
        d = result.to_dict()
        vsr = d.get("verification_surface_requirements", [])
        assert len(vsr) > 0, "Expected verification surfaces for backend engine change"
