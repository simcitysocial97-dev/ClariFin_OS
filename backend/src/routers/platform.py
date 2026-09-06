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
    MODEL_ROUTER_INSTANCE,
)
from runtime.platform.ai.context import build_context_pack
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
    """Execute a tool step within an AI run — Phase 16 real execution.

    Flow: Tool Registry → Policy Engine → Platform API service → C50 authority.
    Records step via orchestrator, enforces policy server-side, executes via
    registry (schema validated), completes step with result/evidence, and
    persists audit event. No AI bypasses policy.
    """
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

    # Idempotency: if a step with same tool+args already exists and completed, return it
    if idempotency_key:
        for s in run.get("steps", []):
            if s.get("tool_name") == tool_name and s.get("arguments") == arguments and s.get("completed_at"):
                return envelope(kind=ai_contract.AI_RUN_KIND, data={"run_id": run_id, "step": s, "status": run.get("status", "PENDING")})

    # Policy check — server-side mandatory
    mode = run.get("mode", "MANUAL")
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

    # Execute step via orchestrator (records PENDING)
    step = AI_ORCHESTRATOR_INSTANCE.execute_step(
        run_id=run_id,
        tool_name=tool_name,
        arguments=arguments,
    )
    if step is None:
        return _not_found(f"Failed to execute step for run {run_id!r}", "platform.ai")

    # Real tool invocation via registry (schema validated → handler → platform service)
    try:
        result = TOOL_REGISTRY_INSTANCE.invoke(tool_name, arguments)
        # Complete step with result — stay RUNNING to allow next tool in sequence
        # (explicit finalize via POST /ai/runs/{id}/finalize when workflow complete)
        is_final = bool(body.get("finalize", False)) if isinstance(body, dict) else False
        AI_ORCHESTRATOR_INSTANCE.complete_step(
            run_id, step["step_number"], result=result, evidence_id=result.get("id") if isinstance(result, dict) else None,
            finalize=is_final,
        )
        refreshed = AI_ORCHESTRATOR_INSTANCE.get_run(run_id)
        completed_step = next((s for s in refreshed["steps"] if s["step_number"] == step["step_number"]), step)
        data = {
            "run_id": run_id,
            "step": completed_step,
            "result": result,
            "status": refreshed.get("status", "RUNNING"),
        }
        return envelope(kind=ai_contract.AI_RUN_KIND, data=data)
    except Exception as exc:
        logger.warning("Tool %s failed: %s", tool_name, exc, exc_info=True)
        is_final = bool(body.get("finalize", False)) if isinstance(body, dict) else False
        AI_ORCHESTRATOR_INSTANCE.complete_step(run_id, step["step_number"], error=str(exc)[:500], finalize=is_final)
        refreshed = AI_ORCHESTRATOR_INSTANCE.get_run(run_id)
        completed_step = next((s for s in refreshed["steps"] if s["step_number"] == step["step_number"]), step)
        data = {
            "run_id": run_id,
            "step": completed_step,
            "error": str(exc)[:500],
            "status": refreshed.get("status", "FAILED" if is_final else "RUNNING"),
        }
        return envelope(kind=ai_contract.AI_RUN_KIND, data=data)


# ---------------------------------------------------------------------------
# AI Provider Registry (Phase 15)
# ---------------------------------------------------------------------------


@router.get("/ai/providers")
async def get_ai_providers() -> JSONResponse:
    """List all registered model providers with health status."""
    providers = MODEL_ROUTER_INSTANCE.list_providers()
    return envelope(kind="platform.ai_providers", data={"providers": providers})


@router.get("/ai/agents")
async def get_ai_agents() -> JSONResponse:
    """List all AI agents with authority level and enabled flag (Phases 17-20)."""
    from runtime.platform.ai.agents import list_agents

    agents = list_agents()
    return envelope(kind="platform.ai_agents", data={"count": len(agents), "items": agents})


@router.get("/ai/agents/{agent_name}")
async def get_ai_agent(agent_name: str) -> JSONResponse:
    """Get single agent detail."""
    from runtime.platform.ai.agents import get_agent

    agent = get_agent(agent_name)
    if agent is None:
        return _not_found(f"Agent {agent_name!r} not found", "platform.ai")
    data = {"name": agent.name, "description": agent.description, "authority_level": agent.authority_level, "enabled": agent.enabled}
    return envelope(kind="platform.ai_agent", data=data)


@router.post("/ai/diagnose")
async def post_ai_diagnose(request: Request) -> JSONResponse:
    """Phase 17 — AI Diagnostic Assistant (deterministic + model interpretation).

    Correct sequence per IMPLEMENTATION_ROADMAP §17:
      USER SYMPTOM → DETERMINISTIC ENGINE → CHANGE INTELLIGENCE → HISTORY
      → EVIDENCE → CONTEXT PACK → LOCAL MODEL → STRUCTURED INTERPRETATION

    Distinguishes FACT/EVIDENCE/INFERENCE/HYPOTHESIS/RECOMMENDATION.
    Never overwrites deterministic evidence.
    """
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    symptom = body.get("symptom", "") if isinstance(body, dict) else ""
    capability_id = body.get("capability_id") if isinstance(body, dict) else None
    run_id = body.get("run_id") if isinstance(body, dict) else None

    if not symptom:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode

        err = PlatformError(
            code=PlatformErrorCode.MALFORMED_REQUEST,
            layer="platform.ai",
            message="POST /ai/diagnose requires {symptom}",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=400)

    from runtime.platform.ai.agents import get_agent

    agent = get_agent("diagnostic_assistant")
    if agent is None:
        return _not_found("diagnostic_assistant agent not found", "platform.ai")

    try:
        result = agent.execute({"symptom": symptom, "capability_id": capability_id, "run_id": run_id})
        return envelope(kind="platform.ai_diagnose_result", data=result)
    except Exception as exc:
        logger.warning("AI diagnose failed: %s", exc, exc_info=True)
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode

        err = PlatformError(code=PlatformErrorCode.INTERNAL, layer="platform.ai", message=str(exc))
        return JSONResponse(content=error_envelope(error=err), status_code=500)


@router.post("/ai/financial/interpret")
async def post_ai_financial_interpret(request: Request) -> JSONResponse:
    """Phase 19 — Financial AI (read-only interpretation).

    Deterministic financial model → authoritative result → AI interpretation.
    LLM never calculator. Disabled by default — requires explicit enablement.
    """
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    query = body.get("query") or body.get("symptom") or "" if isinstance(body, dict) else ""

    from runtime.platform.ai.agents import get_agent

    agent = get_agent("financial_ai")
    if agent is None:
        return _not_found("financial_ai agent not found", "platform.ai")
    if not agent.enabled:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode

        err = PlatformError(
            code=PlatformErrorCode.POLICY_DENIED,
            layer="platform.ai",
            message="Financial AI disabled — requires explicit enablement (policy.enable_financial_ai=true)",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=403)

    try:
        result = agent.execute({"query": query})
        return envelope(kind="platform.financial_ai_result", data=result)
    except Exception as exc:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode

        err = PlatformError(code=PlatformErrorCode.INTERNAL, layer="platform.ai", message=str(exc))
        return JSONResponse(content=error_envelope(error=err), status_code=500)


@router.post("/ai/workflow/run")
async def post_ai_workflow_run(request: Request) -> JSONResponse:
    """Phase 20 — Controlled Workflow Automation (Level 3).

    Requires explicit policy + per-task authorization. Disabled by default.
    """
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    workflow_id = (body.get("workflow_id") or body.get("task_id") or "") if isinstance(body, dict) else ""

    from runtime.platform.ai.agents import get_agent

    agent = get_agent("workflow_automation")
    if agent is None:
        return _not_found("workflow_automation agent not found", "platform.ai")
    if not agent.enabled:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode

        err = PlatformError(
            code=PlatformErrorCode.POLICY_DENIED,
            layer="platform.ai",
            message="Workflow Automation disabled — requires policy.enable_workflow_tools=true and per-task approval",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=403)

    if not workflow_id:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode

        err = PlatformError(
            code=PlatformErrorCode.MALFORMED_REQUEST,
            layer="platform.ai",
            message="POST /ai/workflow/run requires {workflow_id}",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=400)

    try:
        result = agent.execute({"workflow_id": workflow_id})
        return envelope(kind="platform.workflow_result", data=result)
    except Exception as exc:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode

        err = PlatformError(code=PlatformErrorCode.INTERNAL, layer="platform.ai", message=str(exc))
        return JSONResponse(content=error_envelope(error=err), status_code=500)


@router.post("/ai/engineering/execute")
async def post_ai_engineering_execute(request: Request) -> JSONResponse:
    """Phase 18 — Engineering Agent (Level 2, disabled by default).

    Full lifecycle: REQUEST→UNDERSTAND→INSPECT→PLAN→AUTHORIZE→CHANGE→EXECUTE→VERIFY→RECONCILE→DECIDE→LEARN
    Requires evidence_id and human authorization. Never reports success without evidence.
    """
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    symptom = body.get("symptom", "") if isinstance(body, dict) else ""
    evidence_id = body.get("evidence_id") if isinstance(body, dict) else None

    from runtime.platform.ai.agents import get_agent

    agent = get_agent("engineering_agent")
    if agent is None:
        return _not_found("engineering_agent agent not found", "platform.ai")
    if not agent.enabled:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode

        err = PlatformError(
            code=PlatformErrorCode.POLICY_DENIED,
            layer="platform.ai",
            message="Engineering Agent disabled — requires policy.enable_development_tools=true and human authorization",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=403)

    if not evidence_id:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode

        err = PlatformError(
            code=PlatformErrorCode.MALFORMED_REQUEST,
            layer="platform.ai",
            message="POST /ai/engineering/execute requires {evidence_id}",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=400)

    try:
        result = agent.execute({"symptom": symptom, "evidence_id": evidence_id, "run_id": body.get("run_id") if isinstance(body, dict) else None})
        return envelope(kind="platform.engineering_result", data=result)
    except Exception as exc:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode

        err = PlatformError(code=PlatformErrorCode.INTERNAL, layer="platform.ai", message=str(exc))
        return JSONResponse(content=error_envelope(error=err), status_code=500)


@router.post("/ai/runs/{run_id}/finalize")
async def post_ai_run_finalize(run_id: str) -> JSONResponse:
    """Explicitly finalize a RUNNING AI run (Phase 16 multi-step support)."""
    success = AI_ORCHESTRATOR_INSTANCE.finalize_run(run_id)
    if not success:
        return _not_found(f"AI run {run_id!r} not found or not finalizable", "platform.ai")
    run = AI_ORCHESTRATOR_INSTANCE.get_run(run_id)
    return envelope(kind=ai_contract.AI_RUN_KIND, data=run)


@router.get("/ai/runs/{run_id}/trace")
async def get_ai_run_trace(run_id: str) -> JSONResponse:
    """Full trace for an AI run (Phase 13 observability)."""
    run = AI_ORCHESTRATOR_INSTANCE.get_run(run_id)
    if run is None:
        return _not_found(f"AI run {run_id!r} not found", "platform.ai")
    # Provide full observability trace per AI_CONTROL_LAYER_DESIGN §6
    trace = {
        "request": {"symptom": run.get("symptom"), "mode": run.get("mode"), "capability_id": run.get("capability_id")},
        "steps": run.get("steps", []),
        "audit_trail": run.get("audit_trail", []),
        "status": run.get("status"),
        "created_at": run.get("created_at"),
        "updated_at": run.get("updated_at"),
        "completed_at": run.get("completed_at"),
    }
    return envelope(kind="platform.ai_run_trace", data={"run_id": run_id, "trace": trace})


# ---------------------------------------------------------------------------
# App registration helper
# ---------------------------------------------------------------------------


@router.get("/context/pack")
async def get_context_pack(
    symptom: str = Query(..., min_length=1, max_length=512),
    capability_id: str | None = Query(default=None),
    run_id: str | None = Query(default=None),
    intent_type: str = Query(default="diagnose"),
    token_budget: int = Query(default=8000, ge=1000, le=32000),
) -> JSONResponse:
    """Build a context pack for an AI diagnostic request."""
    from runtime.platform.api.contracts import context as context_contract
    from runtime.platform.api.envelope import error_envelope
    from runtime.platform.api.errors import PlatformError, PlatformErrorCode

    try:
        pack = build_context_pack(
            symptom=symptom,
            capability_id=capability_id,
            run_id=run_id,
            intent_type=intent_type,
            token_budget=token_budget,
        )
        # Add checksum
        import hashlib, json
        serialized = json.dumps(pack, sort_keys=True, separators=(",", ":"))
        pack["checksum"] = hashlib.sha256(serialized.encode()).hexdigest()

        return envelope(kind=context_contract.CONTEXT_PACK_KIND, data=pack)
    except Exception as exc:
        logger.warning("Context pack build failed: %s", exc, exc_info=True)
        err = PlatformError(
            code=PlatformErrorCode.INTERNAL,
            layer="platform.context",
            message=str(exc),
        )
        return JSONResponse(content=error_envelope(error=err), status_code=500)


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


# ---------------------------------------------------------------------------
# AI Configuration endpoints (Phase 15 — flexible model switching)
# ---------------------------------------------------------------------------


@router.get("/ai/config")
async def get_ai_config() -> JSONResponse:
    """Get current AI configuration (provider, model, endpoints)."""
    from runtime.platform.ai.config import get_ai_config
    cfg = get_ai_config()
    data = {
        "provider": cfg.provider,
        "model": cfg.model,
        "endpoint": cfg.endpoint,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "privacy": cfg.privacy,
        "enabled_providers": [
            name for name, conf in cfg.providers.items()
            if cfg.is_provider_enabled(name)
        ],
        "fallback_chain": cfg.fallback_chain,
    }
    return envelope(kind="platform.ai_config", data=data)


@router.post("/ai/config/provider")
async def post_ai_config_provider(request: Request) -> JSONResponse:
    """Switch AI provider (e.g., local-small → local-large → openrouter)."""
    body: dict[str, Any] = {}
    try:
        if request.headers.get("content-length", "0") != "0":
            body = await request.json()
    except Exception:
        body = {}

    provider_name = body.get("provider") if isinstance(body, dict) else None
    if not provider_name:
        from runtime.platform.api.envelope import error_envelope
        from runtime.platform.api.errors import PlatformError, PlatformErrorCode
        err = PlatformError(
            code=PlatformErrorCode.MALFORMED_REQUEST,
            layer="platform.ai",
            message="POST /ai/config/provider requires {provider}",
        )
        return JSONResponse(content=error_envelope(error=err), status_code=400)

    from runtime.platform.ai.config import get_ai_config, set_ai_config
    cfg = get_ai_config()
    if provider_name not in cfg.providers:
        return _not_found(f"Provider {provider_name!r} not found", "platform.ai")

    new_cfg = cfg.with_provider(provider_name)
    set_ai_config(**{
        "provider": new_cfg.provider,
        "model": new_cfg.model,
        "endpoint": new_cfg.endpoint,
        "providers": cfg.providers,
    })

    data = {
        "previous_provider": cfg.provider,
        "new_provider": new_cfg.provider,
        "new_model": new_cfg.model,
        "fallback_chain": new_cfg.fallback_chain,
    }
    return envelope(kind="platform.ai_config_switched", data=data)
