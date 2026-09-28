"""Level 0-1 Tool Handlers (Phase 16).

Wires governed AI tools to their actual platform service implementations.
Every tool path: Tool Registry → Policy Engine → Platform API Service → C50 Authority.
No direct AI → executor / DB / shell / filesystem mutation.
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.verification.structured_logging import get_logger
from runtime.platform.api.services import (
    architecture,
    capabilities,
    change,
    evidence,
    health,
    history,
)
from runtime.platform.api.services import (
    errors as errors_service,
)

logger = get_logger(__name__)

__all__ = [
    "LEVEL_0_HANDLERS",
    "LEVEL_1_HANDLERS",
    "execute_tool",
]


# ---------------------------------------------------------------------------
# Level 0 handlers (observe — read-only)
# ---------------------------------------------------------------------------


def _handle_inspect_health(args: dict[str, Any]) -> dict[str, Any]:
    """GET /platform/v1/health/deep"""
    return health.build_health_snapshot()


def _handle_inspect_capability(args: dict[str, Any]) -> dict[str, Any]:
    """GET /platform/v1/capabilities/{id}"""
    cap_id = args.get("capability_id", "")
    result = capabilities.build_capability_detail(cap_id)
    if result is None:
        raise ValueError(f"Capability {cap_id!r} not found")
    return result


def _handle_inspect_architecture(args: dict[str, Any]) -> dict[str, Any]:
    """GET /platform/v1/architecture/authorities"""
    return architecture.build_architecture_authorities()


def _handle_inspect_errors(args: dict[str, Any]) -> dict[str, Any]:
    """GET /platform/v1/errors/current"""
    window = args.get("window", "1h")
    if window == "24h":
        return errors_service.build_errors_recent()
    elif window == "7d":
        return errors_service.build_errors_recurring()
    return errors_service.build_errors_current()


def _handle_inspect_history(args: dict[str, Any]) -> dict[str, Any]:
    """GET /platform/v1/history/runs"""
    limit = args.get("limit", 20)
    return {
        "kind": "platform.history_runs",
        "data": {
            "items": history.build_history_runs()
            .get("data", {})
            .get("items", [])[:limit]
        },
    }


def _handle_inspect_evidence(args: dict[str, Any]) -> dict[str, Any]:
    """GET /platform/v1/evidence/{id}"""
    eid = args.get("evidence_id", "")
    result = evidence.build_evidence_detail(eid)
    if result is None:
        raise ValueError(f"Evidence {eid!r} not found")
    return result


def _handle_inspect_file(args: dict[str, Any]) -> dict[str, Any]:
    """Read a repository file (read-only)."""
    from pathlib import Path

    path_str = args.get("path", "")
    try:
        p = Path(path_str)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path_str}")
        return {
            "kind": "platform.file_content",
            "data": {"path": str(p), "content": p.read_text()[:4096]},
        }
    except Exception as exc:
        return {
            "kind": "platform.file_content",
            "data": {"path": path_str, "error": str(exc)},
        }


def _handle_search_code(args: dict[str, Any]) -> dict[str, Any]:
    """Search repository code."""
    query = args.get("query", "")
    limit = args.get("limit", 10)
    # Use ripgrep via subprocess for code search
    import subprocess

    try:
        result = subprocess.run(
            ["rg", "-n", "--color", "never", "-l", query, "--max-count", str(limit)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        return {
            "kind": "platform.code_search",
            "data": {"query": query, "results": files[:limit]},
        }
    except Exception as exc:
        return {
            "kind": "platform.code_search",
            "data": {"query": query, "error": str(exc), "results": []},
        }


def _handle_inspect_run(args: dict[str, Any]) -> dict[str, Any]:
    """GET /platform/v1/executions/{id}"""
    from runtime.platform.api.services import executions

    eid = args.get("execution_id", "")
    result = executions.build_execution_detail(eid)
    if result is None:
        raise ValueError(f"Execution {eid!r} not found")
    return result


def _handle_inspect_ai_run(args: dict[str, Any]) -> dict[str, Any]:
    """GET /platform/v1/ai/runs/{id}"""
    run_id = args.get("run_id", "")
    from runtime.platform.ai import AI_ORCHESTRATOR_INSTANCE

    run = AI_ORCHESTRATOR_INSTANCE.get_run(run_id)
    if run is None:
        raise ValueError(f"AI run {run_id!r} not found")
    return {"kind": "platform.ai_run", "data": run}


def _handle_list_capabilities(args: dict[str, Any]) -> dict[str, Any]:
    """GET /platform/v1/capabilities"""
    return capabilities.build_capability_list()


LEVEL_0_HANDLERS: dict[str, Any] = {
    "inspect_health": _handle_inspect_health,
    "inspect_capability": _handle_inspect_capability,
    "inspect_architecture": _handle_inspect_architecture,
    "inspect_errors": _handle_inspect_errors,
    "inspect_history": _handle_inspect_history,
    "inspect_evidence": _handle_inspect_evidence,
    "inspect_file": _handle_inspect_file,
    "search_code": _handle_search_code,
    "inspect_run": _handle_inspect_run,
    "inspect_ai_run": _handle_inspect_ai_run,
    "list_capabilities": _handle_list_capabilities,
}


# ---------------------------------------------------------------------------
# Level 1 handlers (analyze — read with side effects)
# ---------------------------------------------------------------------------


def _handle_diagnose_failure(args: dict[str, Any]) -> dict[str, Any]:
    """POST /platform/v1/diagnose"""
    from runtime.platform.diagnostics import engine

    return engine.diagnose(
        symptom=args.get("symptom", ""),
        error_code=args.get("error_code"),
        capability_id=args.get("capability_id"),
    ) or {"kind": "platform.diagnostic_result", "data": {"fact": "no_match"}}


def _handle_compare_runs(args: dict[str, Any]) -> dict[str, Any]:
    """POST /platform/v1/history/compare"""
    current = args.get("current_run_id", "LAST")
    baseline = args.get("baseline", "LAST_PASS")
    return history.build_history_compare(current_run_id=current, baseline=baseline) or {
        "kind": "platform.history_compare",
        "data": {"delta": {}},
    }


def _handle_compute_change_intelligence(args: dict[str, Any]) -> dict[str, Any]:
    """GET /platform/v1/change/intelligence"""
    return change.build_change_intelligence()


def _handle_run_verification_capability(args: dict[str, Any]) -> dict[str, Any]:
    """POST /platform/v1/verification/run"""
    from runtime.platform.api.services import verification_write

    cap_id = args.get("capability_id", "")
    return verification_write.build_run_result(capability_id=cap_id)


def _handle_run_diagnostic(args: dict[str, Any]) -> dict[str, Any]:
    """POST /platform/v1/diagnose"""
    return _handle_diagnose_failure(args)


def _handle_run_what_should_i_run(args: dict[str, Any]) -> dict[str, Any]:
    """POST /platform/v1/verification/what-should-i-run"""
    from runtime.foundation.verification.control_plane_facade import (
        ControlPlane,
        _collect_changed_files,
    )

    cp = ControlPlane()
    files = _collect_changed_files()
    plan = cp.planner.plan(files)
    recommendations = [t.task_id for t in plan.tasks[:5]]
    return {
        "kind": "platform.verification_recommendation",
        "data": {"recommendations": recommendations},
    }


def _handle_run_capability_group(args: dict[str, Any]) -> dict[str, Any]:
    """POST /platform/v1/verification/run/group"""
    from runtime.platform.api.services import verification_write

    cap_ids = args.get("capability_ids", [])
    results = []
    for cap_id in cap_ids[:3]:  # limit group size
        r = verification_write.build_run_result(capability_id=cap_id)
        results.append(r)
    return {"kind": "platform.verification_group_result", "data": {"results": results}}


def _handle_cancel_task(args: dict[str, Any]) -> dict[str, Any]:
    """POST /platform/v1/tasks/{id}/cancel"""
    task_id = args.get("task_id", "")
    from runtime.platform.api.services import tasks_write

    result = tasks_write.build_cancel_result(task_id=task_id)
    if result is None:
        raise ValueError(f"Task {task_id!r} not found")
    return result


LEVEL_1_HANDLERS: dict[str, Any] = {
    "diagnose_failure": _handle_diagnose_failure,
    "compare_runs": _handle_compare_runs,
    "compute_change_intelligence": _handle_compute_change_intelligence,
    "run_verification_capability": _handle_run_verification_capability,
    "run_diagnostic": _handle_run_diagnostic,
    "run_what_should_i_run": _handle_run_what_should_i_run,
    "run_capability_group": _handle_run_capability_group,
    "cancel_task": _handle_cancel_task,
}


# Combined handler map
ALL_HANDLERS = {**LEVEL_0_HANDLERS, **LEVEL_1_HANDLERS}


def execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a registered tool with its handler."""
    handler = ALL_HANDLERS.get(tool_name)
    if handler is None:
        raise ValueError(f"Tool '{tool_name}' not registered")
    return handler(arguments)
