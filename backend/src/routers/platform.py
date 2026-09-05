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
    errors as errors_service,
    events,
    evidence,
    executions,
    health,
    history,
    tasks,
    verification,
)
from runtime.platform.ai import (
    AIOrchestrator,
    AI_ORCHESTRATOR_INSTANCE,
    POLICY_ENGINE_INSTANCE,
    TOOL_REGISTRY_INSTANCE,
    register_builtin_tools,
    evaluate_policy,
)
from runtime.platform.cache import snapshot
from runtime.platform.diagnostics import engine as diagnostics_engine
from runtime.platform.api.services._helpers import now_iso, envelope
from runtime.platform.api.contracts import health as health_contract
from runtime.platform.api.contracts import ai as ai_contract

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform/v1", tags=["platform"])

# Register built-in tools at module load
register_builtin_tools(TOOL_REGISTRY_INSTANCE)


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


@router.get("/evidence/by-execution/{execution_id}")
async def get_evidence_by_execution(execution_id: str) -> JSONResponse:
    env = evidence.build_evidence_by_execution(execution_id)
    if env is None:
        return _not_found(
            f"Evidence for execution {execution_id!r} not found",
            "platform.evidence",
        )
    return _ok(env)


@router.post("/evidence/compare")
async def post_evidence_compare(request: Request) -> JSONResponse:
    """Compare two evidence ids with semantic delta."""
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    left_id = body.get("left_id") if isinstance(body, dict) else None
    right_id = body.get("right_id") if isinstance(body, dict) else None
    if not left_id or not right_id:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode
        err = PlatformError(
            code=PlatformErrorCode.MALFORMED_REQUEST,
            layer="platform.evidence",
            message="POST /evidence/compare requires {left_id, right_id}",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=400)

    env = evidence.build_evidence_compare(left_id, right_id)
    if env is None:
        return _not_found(
            f"Evidence compare: one or both ids not found (left={left_id!r}, right={right_id!r})",
            "platform.evidence",
        )
    return _ok(env)


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


@router.post("/history/compare")
async def post_history_compare(request: Request) -> JSONResponse:
    """Compare two history runs (CURRENT vs LAST/LAST_PASS/KNOWN_GOOD/BASELINE)."""
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    current_run_id = body.get("current_run_id") if isinstance(body, dict) else None
    baseline = body.get("baseline") if isinstance(body, dict) else None
    include_evidence = bool(body.get("include_evidence", False)) if isinstance(body, dict) else False

    if not current_run_id or not baseline:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode
        err = PlatformError(
            code=PlatformErrorCode.MALFORMED_REQUEST,
            layer="platform.history",
            message="POST /history/compare requires {current_run_id, baseline}",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=400)

    env = history.build_history_compare(
        current_run_id=current_run_id,
        baseline=baseline,
        include_evidence=include_evidence,
    )
    if env is None:
        return _not_found(
            f"History compare: could not resolve runs (current={current_run_id!r}, baseline={baseline!r})",
            "platform.history",
        )
    return _ok(env)


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
# Diagnostics (Phase 11)
# ---------------------------------------------------------------------------


@router.post("/diagnose")
async def post_diagnose(request: Request) -> JSONResponse:
    """Deterministic diagnostic engine — Phase 11."""
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    symptom = body.get("symptom", "") if isinstance(body, dict) else ""
    error_code = body.get("error_code") if isinstance(body, dict) else None
    capability_id = body.get("capability_id") if isinstance(body, dict) else None

    if not symptom:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode
        err = PlatformError(
            code=PlatformErrorCode.MALFORMED_REQUEST,
            layer="platform.diagnose",
            message="POST /diagnose requires {symptom}",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=400)

    env = diagnostics_engine.diagnose(
        symptom=symptom,
        error_code=error_code,
        capability_id=capability_id,
    )
    if env is None:
        return _not_found("No diagnostic result could be produced", "platform.diagnose")
    return _ok(env)


@router.post("/diagnose/register")
async def post_diagnose_register(request: Request) -> JSONResponse:
    """Register a failure signature and get a recommendation — Phase 11."""
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    error_code = body.get("error_code") if isinstance(body, dict) else None
    capability_id = body.get("capability_id") if isinstance(body, dict) else None
    description = body.get("description", "") if isinstance(body, dict) else ""
    severity = body.get("severity", "medium") if isinstance(body, dict) else "medium"

    if not error_code or not capability_id or not description:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode
        err = PlatformError(
            code=PlatformErrorCode.MALFORMED_REQUEST,
            layer="platform.diagnose",
            message="POST /diagnose/register requires {error_code, capability_id, description}",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=400)

    rec = diagnostics_engine.build_diagnostic_recommendation(
        error_code=error_code,
        capability_id=capability_id,
        description=description,
        severity=severity,
    )
    return _ok(rec)


# ---------------------------------------------------------------------------
# Health deep (Phase 12)
# ---------------------------------------------------------------------------


@router.get("/health/deep")
async def get_health_deep() -> JSONResponse:
    """Deep health: per-domain readiness with source and last-check.

    Phase 12 — aggregates all subsystems into a single envelope.
    """
    from runtime.platform.api.services import (
        application,
        architecture,
        capabilities,
        errors as errors_service,
        health,
    )

    base = health.build_health_snapshot()
    app_backend = application.build_app_backend()
    app_frontend = application.build_app_frontend()
    app_domain = application.build_app_domain()
    app_financial = application.build_app_financial()
    app_workflows = application.build_app_workflows()
    arch = architecture.build_architecture_authorities()
    err_current = errors_service.build_errors_current()

    domains = list(base["data"].get("domains", []))
    extra_domains = [
        {
            "name": "Backend",
            "status": app_backend["data"]["status"],
            "last_check": app_backend["data"]["last_check"],
            "source": "/platform/v1/app/backend",
            "detail": app_backend["data"]["summary"],
        },
        {
            "name": "Frontend",
            "status": app_frontend["data"]["status"],
            "last_check": app_frontend["data"]["last_check"],
            "source": "/platform/v1/app/frontend",
            "detail": app_frontend["data"]["summary"],
        },
        {
            "name": "Domain Model",
            "status": app_domain["data"]["status"],
            "last_check": app_domain["data"]["last_check"],
            "source": "/platform/v1/app/domain",
            "detail": app_domain["data"]["summary"],
        },
        {
            "name": "Financial Arithmetic",
            "status": app_financial["data"]["status"],
            "last_check": app_financial["data"]["last_check"],
            "source": "/platform/v1/app/financial",
            "detail": app_financial["data"]["summary"],
        },
        {
            "name": "Workflows",
            "status": app_workflows["data"]["status"],
            "last_check": app_workflows["data"]["last_check"],
            "source": "/platform/v1/app/workflows",
            "detail": app_workflows["data"]["summary"],
        },
        {
            "name": "Architecture",
            "status": arch["data"]["items"][0]["status"] if arch["data"]["items"] else "UNKNOWN",
            "last_check": now_iso(),
            "source": "/platform/v1/architecture/authorities",
            "detail": f"authority_count={arch['data']['count']}",
        },
        {
            "name": "Errors",
            "status": "UNHEALTHY" if err_current["data"]["count"] > 0 else "HEALTHY",
            "last_check": now_iso(),
            "source": "/platform/v1/errors/current",
            "detail": f"active_errors={err_current['data']['count']}",
        },
    ]
    domains.extend(extra_domains)

    data = {
        **base["data"],
        "domains": domains,
        "application": {
            "backend": app_backend["data"],
            "frontend": app_frontend["data"],
            "domain": app_domain["data"],
            "financial": app_financial["data"],
            "workflows": app_workflows["data"],
        },
    }
    return envelope(kind=health_contract.HEALTH_KIND, data=data)


# ---------------------------------------------------------------------------
# AI Control Layer (Phase 13)
# ---------------------------------------------------------------------------


@router.get("/ai/mode")
async def get_ai_mode() -> JSONResponse:
    """Get current AI operating mode and authority configuration."""
    from runtime.platform.api.contracts.ai import AIMode, AUTHORITY_LEVELS

    data = {
        "current_mode": "MANUAL",  # Default mode - can be made configurable later
        "available_modes": [m.value for m in AIMode],
        "authority_levels": [
            {
                "level": l.level,
                "name": l.name,
                "description": l.description,
                "enabled_by_default": l.enabled_by_default,
            }
            for l in AUTHORITY_LEVELS
        ],
    }
    return envelope(kind=ai_contract.AI_MODE_KIND, data=data)


@router.post("/ai/runs")
async def post_ai_run(request: Request) -> JSONResponse:
    """Start a new AI run."""
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    symptom = body.get("symptom", "") if isinstance(body, dict) else ""
    mode = body.get("mode", "MANUAL") if isinstance(body, dict) else "MANUAL"
    capability_id = body.get("capability_id") if isinstance(body, dict) else None

    if not symptom:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode
        err = PlatformError(
            code=PlatformErrorCode.MALFORMED_REQUEST,
            layer="platform.ai",
            message="POST /ai/runs requires {symptom}",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=400)

    run = AI_ORCHESTRATOR_INSTANCE.start_run(
        symptom=symptom,
        mode=mode,
        capability_id=capability_id,
    )
    return envelope(kind=ai_contract.AI_RUN_KIND, data=run)


@router.get("/ai/runs")
async def get_ai_runs(
    limit: int = Query(default=50, ge=1, le=200),
    status: str | None = Query(default=None),
) -> JSONResponse:
    """List AI runs with optional status filter."""
    runs = AI_ORCHESTRATOR_INSTANCE.list_runs(limit=limit, status=status)
    data = {"count": len(runs), "items": runs}
    return envelope(kind=ai_contract.AI_RUN_LIST_KIND, data=data)


@router.get("/ai/runs/{run_id}")
async def get_ai_run(run_id: str) -> JSONResponse:
    """Get AI run detail by ID."""
    run = AI_ORCHESTRATOR_INSTANCE.get_run(run_id)
    if run is None:
        return _not_found(f"AI run {run_id!r} not found", "platform.ai")
    return envelope(kind=ai_contract.AI_RUN_KIND, data=run)


@router.post("/ai/runs/{run_id}/cancel")
async def post_ai_run_cancel(run_id: str) -> JSONResponse:
    """Cancel a pending or running AI run."""
    success = AI_ORCHESTRATOR_INSTANCE.cancel_run(run_id)
    if not success:
        return _not_found(f"AI run {run_id!r} not found or not cancellable", "platform.ai")
    run = AI_ORCHESTRATOR_INSTANCE.get_run(run_id)
    return envelope(kind=ai_contract.AI_RUN_KIND, data=run)


@router.get("/ai/tools")
async def get_ai_tools(
    authority_level: int | None = Query(default=None, ge=0, le=4),
) -> JSONResponse:
    """List registered AI tools, optionally filtered by authority level."""
    tools = TOOL_REGISTRY_INSTANCE.list_tools(authority_level=authority_level)
    data = {"count": len(tools), "items": [t.model_dump() for t in tools]}
    return envelope(kind=ai_contract.AI_TOOL_LIST_KIND, data=data)


@router.get("/ai/tools/{tool_name}")
async def get_ai_tool(tool_name: str) -> JSONResponse:
    """Get tool schema by name."""
    schema = TOOL_REGISTRY_INSTANCE.get(tool_name)
    if schema is None:
        return _not_found(f"Tool {tool_name!r} not found", "platform.ai")
    return _ok(schema.model_dump())


@router.post("/ai/runs/{run_id}/steps")
async def post_ai_step(run_id: str, request: Request) -> JSONResponse:
    """Execute a tool step within an AI run."""
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    tool_name = body.get("tool_name") if isinstance(body, dict) else None
    arguments = body.get("arguments", {}) if isinstance(body, dict) else {}
    idempotency_key = body.get("idempotency_key") if isinstance(body, dict) else None

    if not tool_name:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode
        err = PlatformError(
            code=PlatformErrorCode.MALFORMED_REQUEST,
            layer="platform.ai",
            message="POST /ai/runs/{run_id}/steps requires {tool_name}",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=400)

    # Get run to check mode and authorization
    run = AI_ORCHESTRATOR_INSTANCE.get_run(run_id)
    if run is None:
        return _not_found(f"AI run {run_id!r} not found", "platform.ai")

    # Policy check
    mode = run.get("mode", "MANUAL")
    # Map mode to max authorization level
    mode_levels = {"MANUAL": 0, "ASSISTED": 1, "AUTONOMOUS": 4}
    run_authorization_level = mode_levels.get(mode, 0)
    
    policy = evaluate_policy(
        tool_name=tool_name,
        run_mode=run.get("mode", "MANUAL"),
        run_authorization_level=run_authorization_level,
        run_id=run_id,
    )
    if not policy.allowed:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode
        err = PlatformError(
            code=PlatformErrorCode.POLICY_DENIED,
            layer="platform.ai",
            message=policy.reason,
        )
        return JSONResponse(content=error_envelope(error=err), status_code=403)

    # Execute step via orchestrator
    step = AI_ORCHESTRATOR_INSTANCE.execute_step(
        run_id=run_id,
        tool_name=tool_name,
        arguments=arguments,
    )
    if step is None:
        return _not_found(f"Failed to execute step for run {run_id!r}", "platform.ai")

    # For Phase 13, we just record the step initiation
    # Actual tool execution will be implemented in Phase 16+
    data = {
        "run_id": run_id,
        "step": step,
        "status": "PENDING",
    }
    return envelope(kind=ai_contract.AI_RUN_KIND, data=data)


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
