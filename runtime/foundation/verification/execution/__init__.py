"""
M9-C42.28 — Modular execution pipeline sub-package.

This package restructures the former single-file ``executor_pipeline.py``
into focused modules without changing any runtime behaviour. Every public
name that was importable from ``runtime.foundation.verification.executor_pipeline``
remains importable from this package (and the original module re-exports
them for backward compatibility during the transition).

Module map::

    execution.task          — ExecutableVerificationTask model
    execution.adapters      — TaskAdapter ABC + per-kind adapter instances
    execution.evidence      — EvidenceCapture
    execution.reconciliation — ReconciliationEngine
    execution.scope         — ScopeEnforcer
    execution.classification — FailureClassifier
    execution.identity      — IdentityKind + deterministic identity functions
    execution.dispatcher    — LineageViolationError + execute_task
    execution.decisions     — CacheDecision + VerificationDecision
    execution.forensic      — ForensicExecutionRecord
    execution.smoke         — fault_injection_smoke + main
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Re-export the full public API so existing imports continue to work.
# Individual submodule contents are imported lazily below.
# ---------------------------------------------------------------------------

__all__: list[str] = [
    # task
    "VerificationKind",
    "ExecutableStatus",
    "DEFAULT_TASK_TIMEOUT",
    "TaskFingerprints",
    "ExecutableVerificationTask",
    "ExecutableVerificationPlan",
    "build_executable_plan",
    # adapters
    "ADAPTERS",
    # classification
    "FailureKind",
    # evidence
    "ExecutionEvidence",
    # reconciliation
    "ReconciledComponent",
    "LabelledAggregate",
    "ReconciledVerificationState",
    "reconcile",
    # scope
    "execute_mutation_task",
    # identity
    "IdentityKind",
    "compute_identity",
    "task_identity",
    "evidence_identity",
    "environment_identity",
    "is_valid_transition",
    "assert_valid_transition",
    # dispatcher
    "LineageViolationError",
    "execute_task",
    # decisions
    "CacheDecision",
    "evaluate_cache",
    "VerificationDecision",
    "derive_decision",
    # forensic
    "ForensicExecutionRecord",
    "build_forensic_record",
    # smoke / cli
    "fault_injection_smoke",
    "main",
    "default_population",
    "default_prior_measurements",
]


def __getattr__(name: str):
    """Lazy one-shot imports — avoids circular-import headaches during
    package initialisation while keeping every public name resolvable."""
    import importlib  # noqa: PLC0415

    _MODULE_MAP: dict[str, tuple[str, str | None]] = {
        # task
        "VerificationKind": ("runtime.foundation.verification.executor_pipeline", "VerificationKind"),
        "ExecutableStatus": ("runtime.foundation.verification.executor_pipeline", "ExecutableStatus"),
        "DEFAULT_TASK_TIMEOUT": ("runtime.foundation.verification.executor_pipeline", "DEFAULT_TASK_TIMEOUT"),
        "TaskFingerprints": ("runtime.foundation.verification.executor_pipeline", "TaskFingerprints"),
        "ExecutableVerificationTask": ("runtime.foundation.verification.executor_pipeline", "ExecutableVerificationTask"),
        "ExecutableVerificationPlan": ("runtime.foundation.verification.executor_pipeline", "ExecutableVerificationPlan"),
        "build_executable_plan": ("runtime.foundation.verification.executor_pipeline", "build_executable_plan"),
        # adapters
        "ADAPTERS": ("runtime.foundation.verification.executor_pipeline", "ADAPTERS"),
        # classification
        "FailureKind": ("runtime.foundation.verification.executor_pipeline", "FailureKind"),
        # evidence
        "ExecutionEvidence": ("runtime.foundation.verification.executor_pipeline", "ExecutionEvidence"),
        # reconciliation
        "ReconciledComponent": ("runtime.foundation.verification.executor_pipeline", "ReconciledComponent"),
        "LabelledAggregate": ("runtime.foundation.verification.executor_pipeline", "LabelledAggregate"),
        "ReconciledVerificationState": ("runtime.foundation.verification.executor_pipeline", "ReconciledVerificationState"),
        "reconcile": ("runtime.foundation.verification.executor_pipeline", "reconcile"),
        # scope
        "execute_mutation_task": ("runtime.foundation.verification.executor_pipeline", "execute_mutation_task"),
        # identity
        "IdentityKind": ("runtime.foundation.verification.executor_pipeline", "IdentityKind"),
        "compute_identity": ("runtime.foundation.verification.executor_pipeline", "compute_identity"),
        "task_identity": ("runtime.foundation.verification.executor_pipeline", "task_identity"),
        "evidence_identity": ("runtime.foundation.verification.executor_pipeline", "evidence_identity"),
        "environment_identity": ("runtime.foundation.verification.executor_pipeline", "environment_identity"),
        "is_valid_transition": ("runtime.foundation.verification.executor_pipeline", "is_valid_transition"),
        "assert_valid_transition": ("runtime.foundation.verification.executor_pipeline", "assert_valid_transition"),
        # dispatcher
        "LineageViolationError": ("runtime.foundation.verification.executor_pipeline", "LineageViolationError"),
        "execute_task": ("runtime.foundation.verification.executor_pipeline", "execute_task"),
        # decisions
        "CacheDecision": ("runtime.foundation.verification.executor_pipeline", "CacheDecision"),
        "evaluate_cache": ("runtime.foundation.verification.executor_pipeline", "evaluate_cache"),
        "VerificationDecision": ("runtime.foundation.verification.executor_pipeline", "VerificationDecision"),
        "derive_decision": ("runtime.foundation.verification.executor_pipeline", "derive_decision"),
        # forensic
        "ForensicExecutionRecord": ("runtime.foundation.verification.executor_pipeline", "ForensicExecutionRecord"),
        "build_forensic_record": ("runtime.foundation.verification.executor_pipeline", "build_forensic_record"),
        # smoke / cli
        "fault_injection_smoke": ("runtime.foundation.verification.executor_pipeline", "fault_injection_smoke"),
        "main": ("runtime.foundation.verification.executor_pipeline", "main"),
        "default_population": ("runtime.foundation.verification.executor_pipeline", "default_population"),
        "default_prior_measurements": ("runtime.foundation.verification.executor_pipeline", "default_prior_measurements"),
    }

    if name in _MODULE_MAP:
        mod_path, attr = _MODULE_MAP[name]
        mod = importlib.import_module(mod_path)
        return getattr(mod, attr) if attr else mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
