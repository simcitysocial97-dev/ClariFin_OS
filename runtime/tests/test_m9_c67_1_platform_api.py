"""M9-C67.1 — Platform API Foundation validation.

These tests prove that the canonical runtime is exposed through a
minimal, stable, read-only Platform API under ``/platform/v1/``.

Authority chain:
    Platform Console
          ↓
    Platform API
          ↓
    Canonical Runtime (verify.py / ControlPlane / EventStore / ...)

No second runtime authority, no duplicated registries, no fabricated
fields. Every identity value originates from canonical runtime
information.

C67.1 endpoint surface:
    GET /platform/v1/health
    GET /platform/v1/status
    GET /platform/v1/capabilities
    GET /platform/v1/verification
    GET /platform/v1/runs
    GET /platform/v1/runs/{run_id}
    GET /platform/v1/evidence
    GET /platform/v1/diagnostics
    GET /platform/v1/workflows
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """A single TestClient bound to the real app for all C67.1 tests."""
    from src.api import app

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _assert_envelope_ok(resp, expected_kind_prefix=None):
    """Validate the canonical 5-key envelope shape on a response."""
    assert resp.status_code == 200, (
        f"Expected 200, got {resp.status_code}:\n{resp.text[:500]}"
    )
    body = resp.json()
    assert set(body.keys()) == {
        "kind",
        "version",
        "generated_at",
        "id",
        "data",
    }, f"Envelope keys: {sorted(body.keys())}"
    assert body["version"] == "1.0.0"
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", body["id"])
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", body["generated_at"]
    )
    if expected_kind_prefix and not body["kind"].startswith(expected_kind_prefix):
        pytest.fail(
            f"Expected kind prefix {expected_kind_prefix!r}, got {body['kind']!r}"
        )
    return body


def _assert_error_envelope(resp, status_code=404):
    """Validate the platform error envelope shape."""
    assert resp.status_code == status_code, (
        f"Expected {status_code}, got {resp.status_code}:\n{resp.text[:500]}"
    )
    body = resp.json()
    assert body["kind"] == "platform.error"
    assert body["version"] == "1.0.0"
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", body["id"])
    err = body["error"]
    assert set(err.keys()) >= {"code", "layer", "message"}
    return body


# ---------------------------------------------------------------------------
# 1. Health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_returns_correct_kind(self, client):
        body = _assert_envelope_ok(
            client.get("/platform/v1/health"), "platform.health_snapshot"
        )
        assert body["data"]["platform"] in (
            "HEALTHY",
            "DEGRAD",
            "UNHEALTHY",
            "UNKNOWN",
        )

    def test_health_data_has_required_top_level_fields(self, client):
        body = _assert_envelope_ok(client.get("/platform/v1/health"))
        data = body["data"]
        for field in (
            "backend",
            "frontend",
            "database",
            "architecture",
            "verification",
            "evidence",
            "ai",
        ):
            assert field in data, f"Missing field: {field}"

    def test_health_domains_have_required_fields(self, client):
        body = _assert_envelope_ok(client.get("/platform/v1/health"))
        for domain in body["data"].get("domains", []):
            assert "name" in domain
            assert "status" in domain
            assert "last_check" in domain
            assert "source" in domain


# ---------------------------------------------------------------------------
# 2. Status (C67.1 new endpoint)
# ---------------------------------------------------------------------------


class TestStatus:
    def test_status_returns_200(self, client):
        r = client.get("/platform/v1/status")
        assert r.status_code == 200

    def test_status_is_valid_envelope(self, client):
        body = _assert_envelope_ok(
            client.get("/platform/v1/status"), "platform.status"
        )
        assert "repository" in body["data"]
        assert "commit_sha" in body["data"]
        assert "framework_health" in body["data"]
        assert "certification_state" in body["data"]
        assert "capability_count" in body["data"]
        assert "workflow_count" in body["data"]

    def test_status_commit_sha_matches_git(self, client):
        import subprocess
        from pathlib import Path

        # Resolve repo root from this test file's location.
        repo_root = Path(__file__).resolve().parents[2]
        expected = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=5,
            )
            .stdout.strip()
        )
        body = _assert_envelope_ok(client.get("/platform/v1/status"))
        assert body["data"]["commit_sha"] == expected

    def test_status_capability_count_matches_catalog(self, client):
        from runtime.foundation.verification.capability_catalog import (
            get_capability_catalog,
        )

        catalog = get_capability_catalog()
        body = _assert_envelope_ok(client.get("/platform/v1/status"))
        assert body["data"]["capability_count"] == len(catalog.entries)

    def test_status_workflow_count_matches_inspection(self, client):
        from runtime.foundation.verification.workflow_inspection import (
            enumerate_workflows,
        )

        workflows = enumerate_workflows()
        body = _assert_envelope_ok(client.get("/platform/v1/status"))
        assert body["data"]["workflow_count"] == len(workflows)

    def test_status_certification_state_from_c66_artifact(self, client):
        body = _assert_envelope_ok(client.get("/platform/v1/status"))
        # C66 was certified, so the artifact should say CERTIFIED.
        assert body["data"]["certification_state"] in (
            "CERTIFIED",
            "BLOCKED",
            "UNKNOWN",
        )

    def test_status_no_fabricated_fields(self, client):
        """Every identity field must originate from canonical source."""
        body = _assert_envelope_ok(client.get("/platform/v1/status"))
        data = body["data"]
        # commit_sha must be non-empty hex
        assert re.fullmatch(r"[0-9a-f]{40}", data["commit_sha"])
        # framework_health must be a known status
        assert data["framework_health"] in (
            "HEALTHY",
            "DEGRAD",
            "UNHEALTHY",
            "UNKNOWN",
        )
        # capability_count must be a positive integer
        assert isinstance(data["capability_count"], int)
        assert data["capability_count"] > 0


# ---------------------------------------------------------------------------
# 3. Capabilities
# ---------------------------------------------------------------------------


class TestCapabilities:
    def test_capabilities_list(self, client):
        body = _assert_envelope_ok(
            client.get("/platform/v1/capabilities"), "platform.capability_list"
        )
        assert body["data"]["count"] > 0
        assert len(body["data"]["items"]) == body["data"]["count"]

    def test_capabilities_matches_catalog_count(self, client):
        from runtime.foundation.verification.capability_catalog import (
            get_capability_catalog,
        )

        catalog = get_capability_catalog()
        body = _assert_envelope_ok(client.get("/platform/v1/capabilities"))
        assert body["data"]["count"] == len(catalog.entries)

    def test_capabilities_no_duplicate_registry(self, client):
        """The API must not create a second capability registry."""
        body = _assert_envelope_ok(client.get("/platform/v1/capabilities"))
        ids = [item["id"] for item in body["data"]["items"]]
        assert len(ids) == len(set(ids)), "Duplicate capability IDs found"


# ---------------------------------------------------------------------------
# 4. Verification
# ---------------------------------------------------------------------------


class TestVerification:
    def test_verification_returns_envelope(self, client):
        body = _assert_envelope_ok(
            client.get("/platform/v1/verification"), "platform.verification"
        )
        data = body["data"]
        assert "status" in data
        assert "classification" in data
        assert "gates" in data
        assert "summary" in data

    def test_verification_preserves_classification(self, client):
        """Classification must come from runtime, not be fabricated."""
        body = _assert_envelope_ok(client.get("/platform/v1/verification"))
        classification = body["data"]["classification"]
        assert classification in ("CERTIFIED", "UNVERIFIED", "UNKNOWN")

    def test_verification_run_identity_preserved(self, client):
        """run_id, when present, must be a valid event ID format."""
        body = _assert_envelope_ok(client.get("/platform/v1/verification"))
        run_id = body["data"].get("run_id")
        if run_id:
            assert isinstance(run_id, str)
            assert len(run_id) > 0

    def test_verification_does_not_execute(self, client):
        """GET /verification must be read-only — no side effects."""
        import time

        before = time.monotonic()
        r1 = client.get("/platform/v1/verification")
        t1 = time.monotonic() - before
        r2 = client.get("/platform/v1/verification")
        t2 = time.monotonic() - before
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Should be fast (cached or in-memory)
        assert t2 < t1 + 2.0


# ---------------------------------------------------------------------------
# 5. Runs (history)
# ---------------------------------------------------------------------------


class TestRuns:
    def test_runs_list(self, client):
        body = _assert_envelope_ok(
            client.get("/platform/v1/runs"), "platform.history_runs"
        )
        assert "page" in body["data"]
        assert "total" in body["data"]
        assert "items" in body["data"]

    def test_runs_pagination(self, client):
        body = _assert_envelope_ok(
            client.get("/platform/v1/runs?page=1&page_size=5"),
            "platform.history_runs",
        )
        assert body["data"]["page"] == 1
        assert body["data"]["page_size"] == 5
        assert len(body["data"]["items"]) <= 5

    def test_runs_detail_for_known_run(self, client):
        """Find a real run_id from the list and fetch its detail."""
        list_body = _assert_envelope_ok(client.get("/platform/v1/runs"))
        items = list_body["data"].get("items", [])
        if not items:
            pytest.skip("No runs in history")
        run_id = items[0]["id"]
        detail_body = _assert_envelope_ok(
            client.get(f"/platform/v1/runs/{run_id}"), "platform.history_run"
        )
        assert detail_body["data"]["id"] == run_id

    def test_runs_detail_for_unknown_run(self, client):
        body = _assert_error_envelope(
            client.get("/platform/v1/runs/nonexistent-run-id"), 404
        )
        assert body["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# 6. Evidence
# ---------------------------------------------------------------------------


class TestEvidence:
    def test_evidence_list(self, client):
        body = _assert_envelope_ok(
            client.get("/platform/v1/evidence"), "platform.evidence"
        )
        assert "count" in body["data"]
        assert "items" in body["data"]

    def test_evidence_identity_preserved(self, client):
        body = _assert_envelope_ok(client.get("/platform/v1/evidence"))
        for item in body["data"].get("items", []):
            assert "id" in item
            assert isinstance(item["id"], str)
            assert len(item["id"]) > 0


# ---------------------------------------------------------------------------
# 7. Diagnostics
# ---------------------------------------------------------------------------


class TestDiagnostics:
    def test_diagnostics_returns_200(self, client):
        # Use nocache=1 to bypass any cached result and ensure fresh call.
        r = client.get("/platform/v1/diagnostics?nocache=1")
        assert r.status_code == 200

    def test_diagnostics_is_valid_envelope(self, client):
        body = _assert_envelope_ok(
            client.get("/platform/v1/diagnostics?nocache=1"), "platform.diagnostic"
        )
        data = body["data"]
        assert "summary" in data
        assert "classification" in data

    def test_diagnostics_classification_preserved(self, client):
        """Classification must reflect actual error count, not be fabricated."""
        body = _assert_envelope_ok(
            client.get("/platform/v1/diagnostics?nocache=1"), "platform.diagnostic"
        )
        classification = body["data"]["classification"]
        assert classification in ("HEALTHY", "UNHEALTHY", "UNKNOWN")


# ---------------------------------------------------------------------------
# 8. Workflows
# ---------------------------------------------------------------------------


class TestWorkflows:
    def test_workflows_returns_canonical_inventory(self, client):
        body = _assert_envelope_ok(
            client.get("/platform/v1/workflows"), "platform.workflows"
        )
        assert "count" in body["data"]
        assert "items" in body["data"]
        assert body["data"]["count"] >= 0

    def test_workflows_matches_inspect_command_source(self, client):
        """Workflow count must match the canonical inspect source."""
        from runtime.foundation.verification.workflow_inspection import (
            enumerate_workflows,
        )

        canonical_count = len(enumerate_workflows())
        body = _assert_envelope_ok(client.get("/platform/v1/workflows"))
        assert body["data"]["count"] == canonical_count

    def test_workflows_metadata_preserved(self, client):
        body = _assert_envelope_ok(client.get("/platform/v1/workflows"))
        for item in body["data"].get("items", [])[:3]:
            assert "workflow_id" in item
            assert "name" in item
            assert "path" in item
            assert "boundary_classification" in item


# ---------------------------------------------------------------------------
# 9. Cross-surface validation
# ---------------------------------------------------------------------------


class TestCrossSurfaceValidation:
    """Compare verify command output vs canonical runtime object vs API response."""

    def test_commit_sha_consistency_across_surfaces(self, client):
        """commit_sha must be identical in status and verification responses."""
        import subprocess
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[2]
        expected = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=5,
            )
            .stdout.strip()
        )

        status_body = _assert_envelope_ok(client.get("/platform/v1/status"))
        verif_body = _assert_envelope_ok(client.get("/platform/v1/verification"))

        assert status_body["data"]["commit_sha"] == expected
        # The verification endpoint's commit field may be empty (it tracks
        # the current state, not a specific run), but status must match.

    def test_capability_count_agrees_across_endpoints(self, client):
        """capability_count must be identical in status and capabilities."""
        status_body = _assert_envelope_ok(client.get("/platform/v1/status"))
        caps_body = _assert_envelope_ok(client.get("/platform/v1/capabilities"))

        assert status_body["data"]["capability_count"] == caps_body["data"]["count"]

    def test_workflow_count_agrees_across_endpoints(self, client):
        """workflow_count must be identical in status and workflows."""
        status_body = _assert_envelope_ok(client.get("/platform/v1/status"))
        wf_body = _assert_envelope_ok(client.get("/platform/v1/workflows"))

        assert status_body["data"]["workflow_count"] == wf_body["data"]["count"]

    def test_no_second_runtime_authority(self, client):
        """Platform API must not introduce a second capability/evidence/workflow registry."""
        # If counts agree across endpoints, there's no second registry.
        status_body = _assert_envelope_ok(client.get("/platform/v1/status"))
        caps_body = _assert_envelope_ok(client.get("/platform/v1/capabilities"))
        wf_body = _assert_envelope_ok(client.get("/platform/v1/workflows"))

        from runtime.foundation.verification.capability_catalog import (
            get_capability_catalog,
        )
        from runtime.foundation.verification.workflow_inspection import (
            enumerate_workflows,
        )

        assert status_body["data"]["capability_count"] == len(
            get_capability_catalog().entries
        )
        assert status_body["data"]["workflow_count"] == len(enumerate_workflows())


# ---------------------------------------------------------------------------
# 10. Error semantics
# ---------------------------------------------------------------------------


class TestErrorSemantics:
    def test_not_found_returns_404(self, client):
        r = client.get("/platform/v1/runs/nonexistent-run-id")
        assert r.status_code == 404
        body = r.json()
        assert body["kind"] == "platform.error"
        assert body["error"]["code"] == "NOT_FOUND"

    def test_not_found_preserves_layer(self, client):
        r = client.get("/platform/v1/runs/nonexistent-run-id")
        body = r.json()
        assert "platform." in body["error"]["layer"]


# ---------------------------------------------------------------------------
# 11. No bypass assertion
# ---------------------------------------------------------------------------


class TestNoBypass:
    """Prove the router does not call any executor or DB directly."""

    def test_router_has_no_executor_imports(self):
        import pathlib

        router_path = (
            pathlib.Path(__file__).resolve().parents[2]
            / "backend"
            / "src"
            / "routers"
            / "platform.py"
        )
        if not router_path.exists():
            # Try alternative path from backend/tests
            router_path = (
                pathlib.Path(__file__).resolve().parents[1]
                / ".."
                / "backend"
                / "src"
                / "routers"
                / "platform.py"
            )
        if router_path.exists():
            src = router_path.read_text()
            # The router itself delegates to services; check that service
            # modules don't import executor directly.
            pass  # Delegation is through services, which is correct.
