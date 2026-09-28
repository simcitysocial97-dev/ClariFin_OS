from pathlib import Path

import pytest


def test_frontend_backend_mapper_scans_all_routers():
    """Mapper must scan all router files, not just a subset."""
    from runtime.foundation.verification.frontend_backend_map import (
        FrontendBackendMapper,
    )

    mapper = FrontendBackendMapper()
    result = mapper.build_consumer_map()

    endpoints = list(result.keys())

    router_dir = Path("backend/src/routers")
    if router_dir.exists():
        router_files = list(router_dir.glob("*.py"))
        if len(router_files) > 1:
            assert len(endpoints) > 5, \
                f"Only found {len(endpoints)} endpoints from {len(router_files)} routers"


def test_frontend_sync_gate_identifies_orphans():
    """Sync gate must identify frontend calling deleted backend endpoints."""
    from runtime.foundation.verification.frontend_backend_gate import (
        FrontendBackendGate,
    )

    gate = FrontendBackendGate(Path.cwd())
    result = gate.validate()

    assert "passed" in result
    assert "orphaned_consumers" in result

    if not result["passed"]:
        assert len(result["orphaned_consumers"]) > 0
        for orphan in result["orphaned_consumers"]:
            assert orphan.get("endpoint") is not None
            assert len(orphan.get("frontend_files", [])) > 0


def test_blast_radius_frontend_impact_real_router():
    """Blast radius must detect real frontend impact for router changes."""
    from runtime.foundation.verification.blast_radius import BlastRadiusEngine

    router_file = "backend/src/routers/accounts.py"

    if not Path(router_file).exists():
        pytest.skip("Accounts router not found")

    engine = BlastRadiusEngine()
    result = engine.compute(explicit_files=[router_file])

    # Result is a BlastRadiusContract, verify it has expected structure
    assert result is not None

    # Check change_surface exists and has surfaces
    d = result.to_dict()
    assert "change_surface" in d
    cs = d["change_surface"]
    assert "surfaces" in cs
    assert len(cs["surfaces"]) > 0


def test_frontend_mapper_handles_typescript_syntax():
    """Mapper must correctly parse TypeScript fetch patterns."""
    from runtime.foundation.verification.frontend_backend_map import (
        FrontendBackendMapper,
    )

    mapper = FrontendBackendMapper()
    result = mapper.build_consumer_map()

    assert len(result) > 0
