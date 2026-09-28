"""
M9-C49 — Modular orchestration sub-package.

This package restructures the former single-file ``execution_orchestrator.py``
into focused modules without changing any runtime behaviour. Every public
name that was importable from ``runtime.foundation.verification.execution_orchestrator``
remains importable from this package (and the original module re-exports
them for backward compatibility during the transition).

Module map::

    orchestration.models      — enums, dataclasses, fingerprint helpers
    orchestration.orchestrator — ExecutionOrchestrator + convenience functions
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Re-export the full public API so existing imports continue to work.
# Individual submodule contents are imported lazily below.
# ---------------------------------------------------------------------------

__all__: list[str] = [
    "CompletionState",
    "NON_PASS_STATES",
    "PASSING_STATES",
    "FailureStage",
    "FinalDecision",
    "TaskOrigin",
    "RepositoryFingerprint",
    "CAPABILITY_TO_MUTATION_TARGET",
    "ExecutionTaskSpec",
    "ExecutionPlan",
    "TaskExecutionRecord",
    "ExecutionReport",
    "ExecutionOrchestrator",
    "_capability_components",
    "_measurement_kind_for_task",
    "_profile_from_command",
    "build_plan",
    "format_plan",
    "format_report",
]


def __getattr__(name: str):
    """Lazy one-shot imports — avoids circular-import headaches during
    package initialisation while keeping every public name resolvable."""
    import importlib  # noqa: PLC0415

    _MODULE_MAP: dict[str, tuple[str, str | None]] = {
        "CompletionState": ("runtime.foundation.verification.orchestration.models", "CompletionState"),
        "NON_PASS_STATES": ("runtime.foundation.verification.orchestration.models", "NON_PASS_STATES"),
        "PASSING_STATES": ("runtime.foundation.verification.orchestration.models", "PASSING_STATES"),
        "FailureStage": ("runtime.foundation.verification.orchestration.models", "FailureStage"),
        "FinalDecision": ("runtime.foundation.verification.orchestration.models", "FinalDecision"),
        "TaskOrigin": ("runtime.foundation.verification.orchestration.models", "TaskOrigin"),
        "RepositoryFingerprint": ("runtime.foundation.verification.orchestration.models", "RepositoryFingerprint"),
        "CAPABILITY_TO_MUTATION_TARGET": ("runtime.foundation.verification.orchestration.models", "CAPABILITY_TO_MUTATION_TARGET"),
        "ExecutionTaskSpec": ("runtime.foundation.verification.orchestration.models", "ExecutionTaskSpec"),
        "ExecutionPlan": ("runtime.foundation.verification.orchestration.models", "ExecutionPlan"),
        "TaskExecutionRecord": ("runtime.foundation.verification.orchestration.models", "TaskExecutionRecord"),
        "ExecutionReport": ("runtime.foundation.verification.orchestration.models", "ExecutionReport"),
        "_capability_components": ("runtime.foundation.verification.orchestration.models", "_capability_components"),
        "_measurement_kind_for_task": ("runtime.foundation.verification.orchestration.models", "_measurement_kind_for_task"),
        "ExecutionOrchestrator": ("runtime.foundation.verification.orchestration.orchestrator", "ExecutionOrchestrator"),
        "_profile_from_command": ("runtime.foundation.verification.orchestration.orchestrator", "_profile_from_command"),
        "build_plan": ("runtime.foundation.verification.orchestration.orchestrator", "build_plan"),
        "format_plan": ("runtime.foundation.verification.orchestration.orchestrator", "format_plan"),
        "format_report": ("runtime.foundation.verification.orchestration.orchestrator", "format_report"),
    }

    if name in _MODULE_MAP:
        mod_path, attr = _MODULE_MAP[name]
        mod = importlib.import_module(mod_path)
        return getattr(mod, attr) if attr else mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
