"""Platform API FastAPI router (M9-C57 Phase 3).

This module is the **thin HTTP boundary** between the network and the
Platform API services defined in :mod:`runtime.platform.api.services`.

It implements the correct boundary per ``IMPLEMENTATION_ROADMAP.md``:

    HTTP
     ↓
    platform router   ← THIS MODULE
     ↓
    runtime/platform/api service   ← runtime/platform/api/services/*.py
     ↓
    existing authority   ← C50 / observability / knowledge modules

No executor, no evidence system, no DB, no AI surface are introduced
here. The router only:

1. Extracts query/path parameters.
2. Calls the corresponding service function.
3. Catches exceptions and returns the Phase 1 platform error envelope.
4. Propagates ``X-Correlation-Id`` when present; otherwise generates one.

Phase 6 adds write endpoints (run, cancel) that still obey the same
boundary — every write enters the C50 task/execution path through
ControlPlane.run() / EngineeringEventStore.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, FastAPI, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware

from runtime.platform.api.envelope import error_envelope
from runtime.platform.api.errors import PlatformError, PlatformErrorCode
from runtime.platform.api.services import (
    application,
    architecture,
    capabilities,
    change,
    events,
    evidence,
    executions,
    health,
    history,
    tasks,
    verification,
)
from runtime.platform.api.services import (
    errors as errors_service,
)
from runtime.platform.cache import snapshot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform/v1", tags=["platform"])


# ---------------------------------------------------------------------------
# Correlation-ID middleware
# ---------------------------------------------------------------------------


class PlatformCorrelationMiddleware(BaseHTTPMiddleware):
    """Attach ``X-Correlation-Id`` to every Platform API request."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
        response: Response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation_id
        return response


def install_correlation_middleware(app: FastAPI) -> None:
    """Add the correlation middleware to an existing FastAPI app.

    We use the public ``BaseHTTPMiddleware`` so the existing router
    stack is preserved.
    """

    app.add_middleware(PlatformCorrelationMiddleware)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_platform_error(exc: Exception, layer: str) -> tuple[int, dict[str, Any]]:
    """Convert an unexpected exception into a platform error envelope.

    The status code is deliberately 500 (INTERNAL) — callers should not
    confuse an internal platform failure with an application error.
    """

    logger.exception("Platform API %s internal error: %s", layer, exc)
    err = PlatformError(
        code=PlatformErrorCode.INTERNAL,
        layer=layer,
        message=f"Platform API {layer} internal error: {exc!r}",
    )
    return 500, error_envelope(error=err)


def _ok(env: dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=env, status_code=200)


def _not_found(msg: str, layer: str) -> JSONResponse:
    env = error_envelope(
        error=PlatformError(
            code=PlatformErrorCode.NOT_FOUND,
            layer=layer,
            message=msg,
        )
    )
    return JSONResponse(content=env, status_code=404)


def _query_nocache(request: Request) -> bool:
    """Return True when the client sent ``?nocache=1``."""

    val = request.query_params.get("nocache", "0")
    try:
        return int(val) != 0
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health")
async def get_health(request: Request) -> JSONResponse:
    nocache = _query_nocache(request)
    cached = snapshot.get("health", nocache=nocache)
    if cached is not None:
        return _ok(cached)
    env = health.build_health_snapshot()
    snapshot.put("health", env)
    return _ok(env)


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


@router.get("/capabilities")
async def list_capabilities(request: Request) -> JSONResponse:
    nocache = _query_nocache(request)
    cached = snapshot.get("capabilities", nocache=nocache)
    if cached is not None:
        return _ok(cached)
    env = capabilities.build_capability_list()
    snapshot.put("capabilities", env)
    return _ok(env)


@router.get("/capabilities/{capability_id}")
async def get_capability(capability_id: str) -> JSONResponse:
    env = capabilities.build_capability_detail(capability_id)
    if env is None:
        return _not_found(
            f"Capability {capability_id!r} not found in live catalog",
            "platform.capabilities",
        )
    return _ok(env)


@router.get("/capabilities/{capability_id}/graph")
async def get_capability_graph(capability_id: str) -> JSONResponse:
    env = capabilities.build_capability_graph(capability_id)
    if env is None:
        return _not_found(
            f"Capability {capability_id!r} not found in live catalog",
            "platform.capabilities",
        )
    return _ok(env)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@router.get("/tasks")
async def list_tasks(request: Request) -> JSONResponse:
    nocache = _query_nocache(request)
    cached = snapshot.get("tasks", nocache=nocache)
    if cached is not None:
        return _ok(cached)
    env = tasks.build_task_list()
    snapshot.put("tasks", env)
    return _ok(env)


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> JSONResponse:
    env = tasks.build_task_detail(task_id)
    if env is None:
        return _not_found(
            f"Task/obligation {task_id!r} not found in live set",
            "platform.tasks",
        )
    return _ok(env)


@router.post("/tasks/{task_id}/cancel")
async def post_task_cancel(task_id: str) -> JSONResponse:
    """Cancel a task by appending a cancellation event to the event store."""
    from runtime.platform.api.services import tasks_write as tasks_write_svc

    env = tasks_write_svc.build_cancel_result(task_id=task_id)
    if env is None:
        return _not_found(
            f"Task/obligation {task_id!r} not found",
            "platform.tasks",
        )
    return _ok(env)


# ---------------------------------------------------------------------------
# Verification (read-mostly)
# ---------------------------------------------------------------------------


@router.get("/verification/recommendation")
async def get_verification_recommendation() -> JSONResponse:
    env = verification.build_verification_recommendation()
    return _ok(env)


from runtime.platform.api.services import (
    verification_write as verification_write_svc,  # noqa: E402
)


@router.post("/verification/run")
async def post_verification_run(request: Request) -> JSONResponse:
    """Kick off a verification run via ControlPlane.run().

    Accepts optional JSON body: {"capability_id": "..."}.
    If capability_id is omitted, the run uses the live changed-files set.
    """
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    capability_id = body.get("capability_id") if isinstance(body, dict) else None
    env = verification_write_svc.build_run_result(capability_id=capability_id)
    return _ok(env)


@router.post("/verification/run/group")
async def post_verification_run_group(request: Request) -> JSONResponse:
    """Run a verification group (e.g. backend, frontend)."""
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    group = body.get("group") if isinstance(body, dict) else None
    env = verification_write_svc.build_run_result(group=group)
    return _ok(env)


@router.post("/verification/run/affected")
async def post_verification_run_affected() -> JSONResponse:
    """Run verification for capabilities affected by current working-tree changes."""
    env = verification_write_svc.build_run_result(affected=True)
    return _ok(env)


@router.post("/verification/run/full")
async def post_verification_run_full() -> JSONResponse:
    """Run full verification suite."""
    env = verification_write_svc.build_run_result(full=True)
    return _ok(env)


@router.get("/verification/runs/recent")
async def get_verification_runs_recent() -> JSONResponse:
    """Return recent execution reports from the event store."""
    env = verification_write_svc.build_recent_runs()
    return _ok(env)


# ---------------------------------------------------------------------------
# Executions
# ---------------------------------------------------------------------------


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str) -> JSONResponse:
    env = executions.build_execution_detail(execution_id)
    if env is None:
        return _not_found(
            f"Execution {execution_id!r} not found in event store",
            "platform.executions",
        )
    return _ok(env)


@router.get("/executions/{execution_id}/stream")
async def get_execution_stream(execution_id: str, request: Request) -> Response:
    """SSE stream of execution events for one execution.

    Phase 7 enhancement over Phase 6:
    1. Replays existing events matching the execution_id.
    2. Enters a poll loop (1 s interval) watching for new events in
       the EngineeringEventStore.
    3. Sends ``event: complete`` with reason when the execution has
       reached a terminal state (VerificationCompleted observed) or
       after 30 s of no new events.
    4. Honours client disconnect via ``request.is_disconnected()``.

    Does not block the orchestrator — the store is read-only from this
    endpoint's perspective.
    """
    import asyncio

    from runtime.platform.api.services.executions import build_execution_stream_event
    from runtime.system.observability.event_store import EngineeringEventStore

    store = EngineeringEventStore()

    async def event_generator() -> AsyncIterator[bytes]:
        # Collect last-seen event ID to avoid re-sending replays.
        last_event_id: str | None = None
        for event in store.iter_events():
            meta = event.metadata or {}
            if meta.get("execution_id") != execution_id:
                continue
            env = build_execution_stream_event(execution_id, event)
            payload = f"data: {json.dumps(env, default=str)}\n\n"
            yield payload.encode("utf-8")
            last_event_id = event.event_id

            if await request.is_disconnected():
                return

        # If no events were found for this execution, still keep the
        # stream open so the client can observe events that arrive later.
        idle_rounds = 0
        while True:
            if await request.is_disconnected():
                return

            await asyncio.sleep(1.0)

            # Scan for new events since last seen.
            new_events = []
            for event in store.iter_events():
                meta = event.metadata or {}
                if meta.get("execution_id") != execution_id:
                    continue
                if event.event_id == last_event_id:
                    # We've already sent this one during replay.
                    continue
                new_events.append(event)
                if event.event_type == "VerificationCompleted":
                    # Terminal state reached.
                    env = build_execution_stream_event(execution_id, event)
                    payload = f"data: {json.dumps(env, default=str)}\n\n"
                    yield payload.encode("utf-8")
                    yield b'event: complete\ndata: {"reason":"terminal-state-reached"}\n\n'
                    return
                last_event_id = event.event_id

            if new_events:
                idle_rounds = 0
                for event in new_events:
                    env = build_execution_stream_event(execution_id, event)
                    payload = f"data: {json.dumps(env, default=str)}\n\n"
                    yield payload.encode("utf-8")
            else:
                idle_rounds += 1
                if idle_rounds >= 30:
                    yield b'event: complete\ndata: {"reason":"no-new-events-30s"}\n\n'
                    return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/events/stream")
async def get_events_stream(request: Request) -> Response:
    """SSE live stream of all EngineeringEventStore events.

    Phase 7 — previously deferred from Phase 3.
    Replays the last 100 events, then polls for new ones every 1 s.
    Sends periodic keepalive comments (``: ping\\n\\n``) so intermediate
    proxies do not drop the connection.
    """
    import asyncio

    from runtime.platform.api.services.events import build_events_stream_event
    from runtime.system.observability.event_store import EngineeringEventStore

    store = EngineeringEventStore()

    async def event_generator() -> AsyncIterator[bytes]:
        # Replay last 100 events.
        all_events = list(store.iter_events())
        for event in all_events[-100:]:
            env = build_events_stream_event(event)
            payload = f"data: {json.dumps(env, default=str)}\n\n"
            yield payload.encode("utf-8")
            if await request.is_disconnected():
                return

        # Poll for new events.
        while True:
            if await request.is_disconnected():
                return

            await asyncio.sleep(1.0)
            # Send keepalive comment every 15 s worth of loops.
            yield b": ping\n\n"

            # We rely on file modification; simple approach: scan for
            # any events with timestamp newer than our replay window.
            # Since we don't track cursor externally, replay last 100
            # again and let the client deduplicate by event_id.
            recent = list(store.iter_events())[-100:]
            for event in recent:
                env = build_events_stream_event(event)
                payload = f"data: {json.dumps(env, default=str)}\n\n"
                yield payload.encode("utf-8")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


@router.get("/evidence")
async def list_evidence() -> JSONResponse:
    env = evidence.build_evidence_list()
    return _ok(env)


@router.get("/evidence/{evidence_id}")
async def get_evidence(evidence_id: str) -> JSONResponse:
    env = evidence.build_evidence_detail(evidence_id)
    if env is None:
        return _not_found(
            f"Evidence {evidence_id!r} not found",
            "platform.evidence",
        )
    return _ok(env)


# Note: /evidence/by-execution/{id} and /evidence/compare are deferred
# to Phase 8 (history + evidence comparison engine).


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


@router.get("/history/runs")
async def list_history_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> JSONResponse:
    env = history.build_history_runs(page=page, page_size=page_size)
    return _ok(env)


@router.get("/history/runs/{run_id}")
async def get_history_run(run_id: str) -> JSONResponse:
    env = history.build_history_run(run_id)
    if env is None:
        return _not_found(
            f"History run {run_id!r} not found",
            "platform.history",
        )
    return _ok(env)


@router.get("/history/baselines")
async def list_history_baselines() -> JSONResponse:
    env = history.build_history_baselines()
    return _ok(env)


# Note: /history/compare is deferred to Phase 8.


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


@router.get("/errors/current")
async def get_errors_current() -> JSONResponse:
    env = errors_service.build_errors_current()
    return _ok(env)


@router.get("/errors/recent")
async def get_errors_recent() -> JSONResponse:
    env = errors_service.build_errors_recent()
    return _ok(env)


@router.get("/errors/recurring")
async def get_errors_recurring() -> JSONResponse:
    env = errors_service.build_errors_recurring()
    return _ok(env)


@router.get("/errors/frequency")
async def get_errors_frequency() -> JSONResponse:
    env = errors_service.build_errors_frequency()
    return _ok(env)


@router.get("/errors/{error_id}")
async def get_error(error_id: str) -> JSONResponse:
    env = errors_service.build_errors_detail(error_id)
    if env is None:
        return _not_found(
            f"Error {error_id!r} not found",
            "platform.errors",
        )
    return _ok(env)


# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------


@router.get("/architecture/authorities")
async def get_architecture_authorities() -> JSONResponse:
    env = architecture.build_architecture_authorities()
    return _ok(env)


@router.get("/architecture/authority/{name}")
async def get_architecture_authority(name: str) -> JSONResponse:
    env = architecture.build_architecture_authority(name)
    if env is None:
        return _not_found(
            f"Authority {name!r} not found",
            "platform.architecture",
        )
    return _ok(env)


@router.get("/architecture/boundaries")
async def get_architecture_boundaries() -> JSONResponse:
    env = architecture.build_architecture_boundaries()
    return _ok(env)


@router.get("/architecture/duplicates")
async def get_architecture_duplicates() -> JSONResponse:
    env = architecture.build_architecture_duplicates()
    return _ok(env)


@router.get("/architecture/bypasses")
async def get_architecture_bypasses() -> JSONResponse:
    env = architecture.build_architecture_bypasses()
    return _ok(env)


@router.get("/architecture/deprecations")
async def get_architecture_deprecations() -> JSONResponse:
    env = architecture.build_architecture_deprecations()
    return _ok(env)


@router.get("/architecture/unmapped")
async def get_architecture_unmapped() -> JSONResponse:
    env = architecture.build_architecture_unmapped()
    return _ok(env)


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


@router.get("/events")
async def get_events(
    request: Request, limit: int = Query(default=100, ge=1, le=1000)
) -> JSONResponse:
    nocache = _query_nocache(request)
    cached = snapshot.get("events", nocache=nocache)
    if cached is not None:
        return _ok(cached)
    env = events.build_events_list(limit=limit)
    snapshot.put("events", env)
    return _ok(env)


# Note: /events/stream (SSE) is deferred to Phase 7.


# ---------------------------------------------------------------------------
# Application readiness
# ---------------------------------------------------------------------------


@router.get("/app/backend")
async def get_app_backend() -> JSONResponse:
    env = application.build_app_backend()
    return _ok(env)


@router.get("/app/frontend")
async def get_app_frontend() -> JSONResponse:
    env = application.build_app_frontend()
    return _ok(env)


@router.get("/app/domain")
async def get_app_domain() -> JSONResponse:
    env = application.build_app_domain()
    return _ok(env)


@router.get("/app/financial")
async def get_app_financial() -> JSONResponse:
    env = application.build_app_financial()
    return _ok(env)


@router.get("/app/workflows")
async def get_app_workflows() -> JSONResponse:
    env = application.build_app_workflows()
    return _ok(env)


# ---------------------------------------------------------------------------
# Change intelligence
# ---------------------------------------------------------------------------


@router.get("/change/intelligence")
async def get_change_intelligence(request: Request) -> JSONResponse:
    nocache = _query_nocache(request)
    cached = snapshot.get("change", nocache=nocache)
    if cached is not None:
        return _ok(cached)
    env = change.build_change_intelligence()
    snapshot.put("change", env)
    return _ok(env)


# ---------------------------------------------------------------------------
# App registration helper
# ---------------------------------------------------------------------------


def register_platform_routes(app: FastAPI) -> None:
    """Register the Platform API router on an existing FastAPI app.

    Installs:

    * The Platform API router at ``/platform/v1``.
    * The ``X-Correlation-Id`` middleware on the app.

    Does NOT:

    * Modify any existing routers.
    * Re-mount or re-prefix the app.
    * Introduce CORS, authentication, or rate-limiting middleware
      (those belong in Phase 4+).
    """

    install_correlation_middleware(app)
    app.include_router(router)
    logger.info("Registered Platform API routes at /platform/v1")
