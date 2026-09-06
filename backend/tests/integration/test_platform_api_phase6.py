"""M9-C57 Phase 6 — Verification Center validation (Gate 6).

Gate 6: A user can execute a real verification run from the browser and
observe the resulting real evidence. Every run enters the C50
task/execution path through ControlPlane (no second executor / no mock).

This file is: backend/tests/integration/test_platform_api_phase6.py
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from src.api import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


class TestVerificationWrite:
    def test_post_run_single(self, client):
        r = client.post(
            "/platform/v1/verification/run",
            json={"capability_id": "discover.blast-radius"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["kind"] == "platform.verification_run_result"
        assert body["data"]["capability_id"] == "discover.blast-radius"
        assert "message" in body["data"]
        assert "execution_id" in body["data"]

    def test_post_run_empty_body(self, client):
        r = client.post("/platform/v1/verification/run", json={})
        assert r.status_code == 200
        assert r.json()["kind"] == "platform.verification_run_result"

    def test_post_run_affected(self, client):
        r = client.post("/platform/v1/verification/run/affected")
        assert r.status_code == 200
        assert r.json()["kind"] == "platform.verification_run_result"
        assert r.json()["data"]["capability_id"] == "affected"

    def test_post_run_full(self, client):
        r = client.post("/platform/v1/verification/run/full")
        assert r.status_code == 200
        assert r.json()["kind"] == "platform.verification_run_result"

    def test_post_run_group(self, client):
        r = client.post(
            "/platform/v1/verification/run/group", json={"group": "backend"}
        )
        assert r.status_code == 200
        assert r.json()["kind"] == "platform.verification_run_result"
        assert r.json()["data"]["capability_id"] == "backend"

    def test_get_recent_runs(self, client):
        r = client.get("/platform/v1/verification/runs/recent")
        assert r.status_code == 200
        body = r.json()
        assert body["kind"] == "platform.verification_runs_recent"
        assert "count" in body["data"]
        assert "items" in body["data"]


class TestTaskCancel:
    def test_cancel_unknown_returns_404(self, client):
        r = client.post("/platform/v1/tasks/obl-nonexistent-nope/cancel")
        assert r.status_code == 404
        body = r.json()
        assert body["kind"] == "platform.error"
        assert body["error"]["code"] == "NOT_FOUND"

    def test_cancel_existing_task(self, client):
        # Fetch a real task id from the live obligation set, then cancel it.
        resp = client.get("/platform/v1/tasks")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        if not items:
            pytest.skip("no live obligations to cancel")
        task_id = items[0]["id"]
        r = client.post(f"/platform/v1/tasks/{task_id}/cancel")
        assert r.status_code == 200
        body = r.json()
        assert body["kind"] == "platform.task_cancel_result"
        assert body["data"]["id"] == task_id
        assert body["data"]["cancelled"] is True


class TestExecutionStream:
    def test_stream_returns_event_stream(self, client):
        # Any id is readable; the stream replays events filtered by execution_id.
        # We probe the real event store with a bogus id — the stream must still
        # 200 and return text/event-stream.
        r = client.get("/platform/v1/executions/does-not-exist/stream")
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")
        assert b"data:" in r.content or b"event:" in r.content
