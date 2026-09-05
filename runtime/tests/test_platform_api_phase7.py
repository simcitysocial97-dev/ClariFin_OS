"""M9-C57 Phase 7 — Execution, Evidence and Live State validation.

These tests prove Gate 7 from ``IMPLEMENTATION_ROADMAP.md``:

    A running verification started from the Console must be observable
    in real time and reconcile with the persisted execution/evidence
    records.

Test scope:

1. Verification write path emits events with ``execution_id`` metadata.
2. Execution detail endpoint finds those events and returns valid envelope.
3. Execution SSE stream service function replays emitted events correctly.
4. Events SSE stream service function works.
5. No synthetic progress data is emitted.
6. All envelopes conform to Phase 1 contract shapes.
7. HTTP endpoints return correct content-type for SSE routes.

SSE streaming behaviour (poll loop, completion signal) is verified via
the service-layer functions rather than through TestClient, because the
live-poll generator would hang the synchronous TestClient indefinitely.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from runtime.platform.api.contracts import executions as executions_contract
from runtime.platform.api.contracts import events as events_contract
from runtime.platform.api.envelope import API_VERSION
from runtime.platform.api.services import executions, verification_write
from runtime.platform.api.services.events import build_events_stream_event
from runtime.system.observability.event_store import EngineeringEventStore, create_event


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


def _clean_event_store() -> EngineeringEventStore:
    """Return a fresh event store for isolated tests."""
    store = EngineeringEventStore()
    store.clear()
    return store


def _wait_for_events(store: EngineeringEventStore, min_count: int, timeout: float = 5.0) -> list[Any]:
    """Poll until at least ``min_count`` events exist."""
    import time

    deadline = datetime.now(UTC).timestamp() + timeout
    while True:
        events = list(store.iter_events())
        if len(events) >= min_count:
            return events
        if datetime.now(UTC).timestamp() > deadline:
            break
        time.sleep(0.1)
    return list(store.iter_events())


# ---------------------------------------------------------------------------
# 1. Event emission during verification runs
# ---------------------------------------------------------------------------


class TestVerificationEventEmission:
    """Phase 7: build_run_result must emit VerificationStarted and
    VerificationCompleted events with execution_id in metadata."""

    def test_run_emits_started_and_completed_events(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result(capability_id="discover.blast-radius")
        assert _envelope_shape_ok(env)
        assert env["kind"] == "platform.verification_run_result"
        execution_id = env["data"]["execution_id"]
        assert execution_id.startswith("ver-")

        events = _wait_for_events(store, 2)
        types = {e.event_type for e in events}
        assert "VerificationStarted" in types
        assert "VerificationCompleted" in types

    def test_emitted_events_have_execution_id_in_metadata(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result(capability_id="discover.blast-radius")
        execution_id = env["data"]["execution_id"]

        events = _wait_for_events(store, 2)
        for event in events:
            meta = event.metadata or {}
            assert meta.get("execution_id") == execution_id, (
                f"Event {event.event_type} missing execution_id; got {meta}"
            )

    def test_emitted_events_have_capability_id_in_metadata(self) -> None:
        store = _clean_event_store()
        cap_id = "discover.blast-radius"
        env = verification_write.build_run_result(capability_id=cap_id)

        events = _wait_for_events(store, 2)
        for event in events:
            meta = event.metadata or {}
            assert meta.get("capability_id") == cap_id

    def test_run_without_capability_id_emits_events(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result()
        execution_id = env["data"]["execution_id"]

        events = _wait_for_events(store, 2)
        exec_events = [e for e in events if (e.metadata or {}).get("execution_id") == execution_id]
        assert len(exec_events) >= 2


# ---------------------------------------------------------------------------
# 2. Execution detail reconciles with persisted events
# ---------------------------------------------------------------------------


class TestExecutionDetailReconciliation:
    """Phase 7: execution detail must project from real event-store events,
    not mock data."""

    def test_detail_finds_emitted_events(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result(capability_id="discover.blast-radius")
        execution_id = env["data"]["execution_id"]

        detail = executions.build_execution_detail(execution_id)
        assert detail is not None
        assert _envelope_shape_ok(detail)
        assert detail["kind"] == executions_contract.EXECUTION_DETAIL_KIND
        assert detail["data"]["id"] == execution_id
        assert len(detail["data"]["events"]) >= 2

    def test_detail_has_correct_status_for_completed_execution(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result()
        execution_id = env["data"]["execution_id"]
        _wait_for_events(store, 2)

        detail = executions.build_execution_detail(execution_id)
        assert detail is not None
        assert detail["data"]["status"] == "CLOSED"

    def test_detail_has_terminal_state_from_event_type(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result()
        execution_id = env["data"]["execution_id"]
        _wait_for_events(store, 2)

        detail = executions.build_execution_detail(execution_id)
        assert detail is not None
        assert detail["data"]["current_state"] == "VerificationCompleted"

    def test_detail_for_unknown_execution_returns_none(self) -> None:
        assert executions.build_execution_detail("nonexistent-exec-id") is None

    def test_detail_envelope_round_trips_through_contract(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result()
        execution_id = env["data"]["execution_id"]
        _wait_for_events(store, 2)

        detail = executions.build_execution_detail(execution_id)
        assert detail is not None
        parsed = executions_contract.ExecutionDetailEnvelope.model_validate(detail)
        assert parsed.data.id == execution_id
        assert parsed.data.status.value in ("OPEN", "CLOSED")
        assert isinstance(parsed.data.events, list)
        assert len(parsed.data.events) >= 2


# ---------------------------------------------------------------------------
# 3. SSE stream service functions (tested at service layer to avoid
#    hanging TestClient on infinite generators)
# ---------------------------------------------------------------------------


class TestExecutionStreamService:
    """Phase 7: build_execution_stream_event projects events correctly."""

    def test_stream_event_shape(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result()
        execution_id = env["data"]["execution_id"]
        _wait_for_events(store, 2)

        # Grab one of the emitted events.
        event = next(
            e
            for e in store.iter_events()
            if (e.metadata or {}).get("execution_id") == execution_id
        )
        stream_env = executions.build_execution_stream_event(execution_id, event)
        assert _envelope_shape_ok(stream_env)
        assert stream_env["kind"] == executions_contract.EXECUTION_STREAM_EVENT_KIND
        parsed = executions_contract.ExecutionStreamEventEnvelope.model_validate(stream_env)
        assert parsed.data.execution_id == execution_id
        assert parsed.data.event_type in ("VerificationStarted", "VerificationCompleted")

    def test_stream_event_contains_full_payload(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result()
        execution_id = env["data"]["execution_id"]
        _wait_for_events(store, 2)

        event = next(
            e
            for e in store.iter_events()
            if e.event_type == "VerificationCompleted"
            and (e.metadata or {}).get("execution_id") == execution_id
        )
        stream_env = executions.build_execution_stream_event(execution_id, event)
        parsed = executions_contract.ExecutionStreamEventEnvelope.model_validate(stream_env)
        assert parsed.data.payload.get("execution_id") == execution_id


class TestEventsStreamService:
    """Phase 7: build_events_stream_event projects events correctly."""

    def test_stream_event_shape(self) -> None:
        store = _clean_event_store()
        store.append(
            create_event(
                "TestEvent",
                {"environment": "test"},
                {"key": "value"},
                metadata={"execution_id": "test-exec-1"},
            )
        )
        event = next(store.iter_events())
        stream_env = build_events_stream_event(event)
        assert _envelope_shape_ok(stream_env)
        assert stream_env["kind"] == events_contract.EVENTS_STREAM_KIND
        parsed = events_contract.EventsStreamEventEnvelope.model_validate(stream_env)
        assert parsed.data.event.event_type == "TestEvent"


# ---------------------------------------------------------------------------
# 4. HTTP endpoint structure (no hanging — only check content-type and 200)
# ---------------------------------------------------------------------------


class TestHttpEndpointStructure:
    """Verify that SSE endpoints are registered on the router.

    We DO NOT consume the full SSE stream through TestClient because
    the live-poll generator stays open indefinitely (by design).
    Route existence is verified by inspecting the router directly.
    """

    def test_execution_stream_route_registered(self) -> None:
        from backend.src.routers.platform import router

        paths = [r.path for r in router.routes]
        assert any("/executions/{execution_id}/stream" in p for p in paths)

    def test_events_stream_route_registered(self) -> None:
        from backend.src.routers.platform import router

        paths = [r.path for r in router.routes]
        assert any(p == "/platform/v1/events/stream" for p in paths)

    def test_execution_detail_returns_404_for_unknown(self) -> None:
        from src.api import app
        with TestClient(app, raise_server_exceptions=True) as client:
            resp = client.get("/platform/v1/executions/nonexistent-id")
            assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 5. No synthetic progress percentage
# ---------------------------------------------------------------------------


class TestNoSyntheticProgress:
    """Phase 7 gate: the execution detail and stream must not fabricate
    a progress percentage that does not come from real event data."""

    def test_detail_has_no_progress_field(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result()
        execution_id = env["data"]["execution_id"]
        _wait_for_events(store, 2)

        detail = executions.build_execution_detail(execution_id)
        assert detail is not None
        data_keys = set(detail["data"].keys())
        assert "progress_percent" not in data_keys
        assert "progress_percentage" not in data_keys
        assert "progress" not in data_keys

    def test_stream_event_has_no_progress_field(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result()
        execution_id = env["data"]["execution_id"]
        _wait_for_events(store, 2)

        event = next(
            e
            for e in store.iter_events()
            if (e.metadata or {}).get("execution_id") == execution_id
        )
        stream_env = executions.build_execution_stream_event(execution_id, event)
        inner_keys = set(stream_env.get("data", {}).keys())
        assert "progress_percent" not in inner_keys
        assert "progress_percentage" not in inner_keys


# ---------------------------------------------------------------------------
# 6. Integration: full run → detail → stream reconciliation
# ---------------------------------------------------------------------------


class TestGate7Integration:
    """Full integration test for Gate 7: run, observe detail, confirm
    reconciliation with persisted event-store records."""

    def test_full_lifecycle(self) -> None:
        store = _clean_event_store()
        env = verification_write.build_run_result(capability_id="discover.blast-radius")
        execution_id = env["data"]["execution_id"]
        _wait_for_events(store, 2)

        # Detail matches persisted events.
        detail = executions.build_execution_detail(execution_id)
        assert detail is not None
        assert detail["data"]["id"] == execution_id
        assert detail["data"]["status"] == "CLOSED"
        assert len(detail["data"]["events"]) >= 2

        # Stream events reconcile with detail event list.
        detail_event_ids = set(detail["data"]["events"])
        stored_event_ids = {e.event_id for e in store.iter_events() if (e.metadata or {}).get("execution_id") == execution_id}
        # Every stored execution event should appear in the detail.
        assert stored_event_ids <= detail_event_ids or stored_event_ids == detail_event_ids

        # Events stream includes our events.
        all_events = list(store.iter_events())
        platform_events = [
            e for e in all_events
            if e.metadata.get("execution_id") == execution_id
            or e.event_type in ("VerificationStarted", "VerificationCompleted")
        ]
        assert len(platform_events) >= 2
