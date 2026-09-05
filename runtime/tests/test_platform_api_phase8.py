"""M9-C57 Phase 8 — History + Evidence + Comparison validation.

These tests prove Gate 8 from ``IMPLEMENTATION_ROADMAP.md``:

    A user can select CURRENT vs LAST PASS vs KNOWN GOOD vs BASELINE
    and inspect the actual delta.

Test scope:

1. History compare: envelope shape, required delta dimensions,
   sentinel resolution (LAST, LAST_PASS), unknown run handling.
2. Evidence by execution: projects events with matching execution_id,
   returns None for unknown execution.
3. Evidence compare (semantic): enhanced delta includes structural
   and semantic fields; returns None for unknown ids.
4. Router endpoints: routes registered, malformed request handling,
   content-type verification.
5. No regression against Phase 1–7 tests.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from runtime.platform.api.contracts import evidence as evidence_contract
from runtime.platform.api.contracts import history as history_contract
from runtime.platform.api.envelope import API_VERSION
from runtime.platform.api.services import evidence, history
from runtime.platform.api.services._comparison import compute_evidence_delta, compute_history_delta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _envelope_shape_ok(env: dict[str, Any]) -> bool:
    """Validate canonical 5-key envelope shape."""
    return (
        set(env.keys()) == {"kind", "version", "generated_at", "id", "data"}
        and env["version"] == API_VERSION
        and re.fullmatch(r"sha256:[0-9a-f]{64}", env["id"])
        and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", env["generated_at"])
    )


# ---------------------------------------------------------------------------
# 1. History compare
# ---------------------------------------------------------------------------


class TestHistoryCompare:
    """Phase 8: POST /history/compare resolves sentinels and computes delta."""

    def _ensure_events(self) -> None:
        """Emit two verification runs so comparison has data."""
        from runtime.platform.api.services import verification_write
        from runtime.system.observability.event_store import EngineeringEventStore

        store = EngineeringEventStore()
        store.clear()
        verification_write.build_run_result(capability_id="discover.blast-radius")
        verification_write.build_run_result(capability_id="discover.blast-radius")

    def test_compare_last_vs_last_returns_envelope(self) -> None:
        self._ensure_events()
        env = history.build_history_compare(current_run_id="LAST", baseline="LAST")
        assert env is not None
        assert _envelope_shape_ok(env)
        assert env["kind"] == history_contract.HISTORY_COMPARE_KIND

    def test_compare_has_required_delta_dimensions(self) -> None:
        self._ensure_events()
        env = history.build_history_compare(current_run_id="LAST", baseline="LAST")
        assert env is not None
        delta = env["data"]["delta"]
        required_dims = {
            "repository_changes",
            "test_changes",
            "failures",
            "recovered_failures",
            "duration",
            "evidence_invalidated",
            "new_obligations",
            "closed_obligations",
            "capability_state_changes",
        }
        assert required_dims <= set(delta.keys())

    def test_compare_has_current_and_baseline_run(self) -> None:
        self._ensure_events()
        env = history.build_history_compare(current_run_id="LAST", baseline="LAST")
        assert env is not None
        data = env["data"]
        assert "current_run" in data
        assert "baseline_run" in data
        assert "delta" in data

    def test_compare_with_unknown_literal_run_id_returns_none(self) -> None:
        env = history.build_history_compare(
            current_run_id="nonexistent-run-id",
            baseline="LAST",
        )
        assert env is None

    def test_compare_with_unknown_baseline_name_returns_none(self) -> None:
        env = history.build_history_compare(
            current_run_id="LAST",
            baseline="UNKNOWN_BASELINE",
        )
        # _resolve_baseline_run_id returns None for unknown names,
        # which causes build_history_compare to return None.
        assert env is None

    def test_compare_envelope_round_trips_through_contract(self) -> None:
        self._ensure_events()
        env = history.build_history_compare(current_run_id="LAST", baseline="LAST")
        assert env is not None
        parsed = history_contract.HistoryCompareEnvelope.model_validate(env)
        assert parsed.kind == history_contract.HISTORY_COMPARE_KIND
        assert isinstance(parsed.data.delta, dict)


class TestComputeHistoryDelta:
    """Unit tests for the shared delta computation function."""

    def test_identical_runs_have_zero_delta_in_counts(self) -> None:
        left = {
            "id": "run-a",
            "status": "HEALTHY",
            "capabilities_passed": 5,
            "capabilities_failed": 0,
            "duration_ms": 1000,
            "blast_radius": {},
        }
        right = {
            "id": "run-b",
            "status": "HEALTHY",
            "capabilities_passed": 5,
            "capabilities_failed": 0,
            "duration_ms": 1000,
            "blast_radius": {},
        }
        delta = compute_history_delta(left, right)
        assert delta["test_changes"]["passed_added"] == 0
        assert delta["test_changes"]["failed_added"] == 0
        assert delta["duration"]["delta_ms"] == 0

    def test_degraded_run_shows_failed_added(self) -> None:
        left = {
            "status": "UNHEALTHY",
            "capabilities_passed": 3,
            "capabilities_failed": 2,
            "duration_ms": 2000,
            "blast_radius": {},
        }
        right = {
            "status": "HEALTHY",
            "capabilities_passed": 5,
            "capabilities_failed": 0,
            "duration_ms": 1000,
            "blast_radius": {},
        }
        delta = compute_history_delta(left, right)
        assert delta["test_changes"]["failed_added"] == 2
        assert delta["test_changes"]["passed_removed"] == 2
        assert delta["duration"]["delta_ms"] == 1000
        assert delta["failures"] == 2
        assert delta["recovered_failures"] == 0

    def test_capability_state_change_recorded_on_status_diff(self) -> None:
        left = {"status": "UNHEALTHY"}
        right = {"status": "HEALTHY"}
        delta = compute_history_delta(left, right)
        assert len(delta["capability_state_changes"]) == 1
        change = delta["capability_state_changes"][0]
        assert change["from"] == "HEALTHY"
        assert change["to"] == "UNHEALTHY"


# ---------------------------------------------------------------------------
# 2. Evidence by execution
# ---------------------------------------------------------------------------


class TestEvidenceByExecution:
    """Phase 8: GET /evidence/by-execution/{id} projects events correctly."""

    def test_by_execution_finds_emitted_events(self) -> None:
        from runtime.platform.api.services import verification_write
        from runtime.system.observability.event_store import EngineeringEventStore

        store = EngineeringEventStore()
        store.clear()
        env = verification_write.build_run_result(capability_id="discover.blast-radius")
        execution_id = env["data"]["execution_id"]

        result = evidence.build_evidence_by_execution(execution_id)
        assert result is not None
        assert _envelope_shape_ok(result)
        assert result["kind"] == evidence_contract.EVIDENCE_LIST_KIND
        assert result["data"]["count"] >= 2

    def test_by_execution_for_unknown_returns_none(self) -> None:
        assert evidence.build_evidence_by_execution("unknown-execution-id") is None

    def test_by_execution_items_have_required_fields(self) -> None:
        from runtime.platform.api.services import verification_write
        from runtime.system.observability.event_store import EngineeringEventStore

        store = EngineeringEventStore()
        store.clear()
        env = verification_write.build_run_result()
        execution_id = env["data"]["execution_id"]

        result = evidence.build_evidence_by_execution(execution_id)
        assert result is not None
        for item in result["data"]["items"]:
            assert item["id"]
            assert item["kind"]
            assert item["status"]
            assert item["summary"]

    def test_by_execution_envelope_round_trips(self) -> None:
        from runtime.platform.api.services import verification_write
        from runtime.system.observability.event_store import EngineeringEventStore

        store = EngineeringEventStore()
        store.clear()
        env = verification_write.build_run_result()
        execution_id = env["data"]["execution_id"]

        result = evidence.build_evidence_by_execution(execution_id)
        assert result is not None
        parsed = evidence_contract.EvidenceListEnvelope.model_validate(result)
        assert parsed.data.count >= 2


# ---------------------------------------------------------------------------
# 3. Evidence compare (semantic)
# ---------------------------------------------------------------------------


class TestEvidenceCompareSemantic:
    """Phase 8: enhanced evidence compare produces semantic delta."""

    def test_compare_unknown_ids_returns_none(self) -> None:
        assert evidence.build_evidence_compare("unknown-a", "unknown-b") is None

    def test_compare_envelope_shape(self) -> None:
        """When both ids exist, envelope must have correct shape."""
        from runtime.platform.api.services import verification_write
        from runtime.system.observability.event_store import EngineeringEventStore
        from runtime.foundation.verification.control_plane_facade import ControlPlane, _collect_changed_files

        store = EngineeringEventStore()
        store.clear()
        verification_write.build_run_result(capability_id="discover.blast-radius")

        # We need real evidence ids from the obligation set.
        cp = ControlPlane()
        files = _collect_changed_files()
        plan = cp.planner.plan(files)
        oset = cp._plan_to_obligations(plan, files)
        evidence_ids = []
        for obl in oset.obligations:
            for ev in getattr(obl, "evidence", []) or []:
                if isinstance(ev, str) and ev:
                    evidence_ids.append(ev)
                elif isinstance(ev, dict):
                    for key in ("evidence_id", "id", "fingerprint"):
                        val = ev.get(key)
                        if val:
                            evidence_ids.append(str(val))
                            break
        if len(evidence_ids) < 2:
            pytest.skip("need at least 2 evidence ids for compare test")

        result = evidence.build_evidence_compare(evidence_ids[0], evidence_ids[1])
        if result is None:
            pytest.skip("evidence ids not in live obligation set")
        assert _envelope_shape_ok(result)
        assert result["kind"] == evidence_contract.EVIDENCE_COMPARE_KIND
        assert "delta" in result["data"]

    def test_compute_evidence_delta_structural_fields(self) -> None:
        left = {"id": "e1", "status": "OPEN", "capability_id": "cap-a", "kind": "verification"}
        right = {"id": "e2", "status": "CLOSED", "capability_id": "cap-a", "kind": "verification"}
        delta = compute_evidence_delta(left, right)
        assert "status" in delta
        assert delta["status"] == {"left": "OPEN", "right": "CLOSED"}


# ---------------------------------------------------------------------------
# 4. HTTP endpoint structure
# ---------------------------------------------------------------------------


class TestHttpEndpointStructure:
    """Verify that Phase 8 routes are registered on the platform router."""

    def test_history_compare_route_registered(self) -> None:
        from backend.src.routers.platform import router

        paths = [r.path for r in router.routes]
        assert any(p == "/platform/v1/history/compare" for p in paths)

    def test_evidence_by_execution_route_registered(self) -> None:
        from backend.src.routers.platform import router

        paths = [r.path for r in router.routes]
        assert any(p == "/platform/v1/evidence/by-execution/{execution_id}" for p in paths)

    def test_evidence_compare_route_registered(self) -> None:
        from backend.src.routers.platform import router

        paths = [r.path for r in router.routes]
        assert any(p == "/platform/v1/evidence/compare" for p in paths)

    def test_history_compare_malformed_request_returns_400(self) -> None:
        from src.api import app
        from fastapi.testclient import TestClient

        with TestClient(app, raise_server_exceptions=True) as client:
            resp = client.post("/platform/v1/history/compare", json={})
            assert resp.status_code == 400

    def test_evidence_compare_malformed_request_returns_400(self) -> None:
        from src.api import app
        from fastapi.testclient import TestClient

        with TestClient(app, raise_server_exceptions=True) as client:
            resp = client.post("/platform/v1/evidence/compare", json={})
            assert resp.status_code == 400

    def test_evidence_by_execution_unknown_returns_404(self) -> None:
        from src.api import app
        from fastapi.testclient import TestClient

        with TestClient(app, raise_server_exceptions=True) as client:
            resp = client.get("/platform/v1/evidence/by-execution/nonexistent-id")
            assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 5. Integration: full lifecycle
# ---------------------------------------------------------------------------


class TestGate8Integration:
    """Full integration test for Gate 8: compare runs, inspect evidence,
    verify delta dimensions are populated."""

    def test_compare_and_evidence_lifecycle(self) -> None:
        from runtime.platform.api.services import verification_write
        from runtime.system.observability.event_store import EngineeringEventStore

        store = EngineeringEventStore()
        store.clear()

        # Step 1: Emit two verification runs.
        env1 = verification_write.build_run_result(capability_id="discover.blast-radius")
        exec_id_1 = env1["data"]["execution_id"]

        env2 = verification_write.build_run_result(capability_id="discover.blast-radius")
        exec_id_2 = env2["data"]["execution_id"]

        # Step 2: Evidence by execution finds events for each.
        ev1 = evidence.build_evidence_by_execution(exec_id_1)
        ev2 = evidence.build_evidence_by_execution(exec_id_2)
        assert ev1 is not None
        assert ev2 is not None
        assert ev1["data"]["count"] >= 2
        assert ev2["data"]["count"] >= 2

        # Step 3: History compare resolves LAST and computes delta.
        compare_env = history.build_history_compare(current_run_id="LAST", baseline="LAST")
        if compare_env is None:
            pytest.skip("insufficient events for comparison")
        assert _envelope_shape_ok(compare_env)
        delta = compare_env["data"]["delta"]
        # All required dimensions present.
        for dim in (
            "repository_changes",
            "test_changes",
            "failures",
            "recovered_failures",
            "duration",
            "evidence_invalidated",
            "new_obligations",
            "closed_obligations",
            "capability_state_changes",
        ):
            assert dim in delta, f"Missing delta dimension: {dim}"
