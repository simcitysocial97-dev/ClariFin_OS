# runtime/foundation/verification/mutation_authority.py
#
# M9-C48 A2 — Single canonical mutation execution authority (GAP-001).
#
# This module declares and enforces ONE canonical mutation execution path.
#
# Canonical path (M9-C42.5, proven production):
#     runtime/verify.py
#       -> runtime.foundation.verification.mutation_runner.run_mutation_cli
#       -> runtime.foundation.verification.mutation_runner.execute_mutation
#       -> mutmut
#
# The MutationOrchestrator (M9-C44) in mutation_execution/orchestrator.py is
# preserved as a NON-CANONICAL future backend / migration target. It is
# explicitly NOT wired into the production path because:
#   1. It has never been exercised end-to-end against real mutmut runs.
#   2. Its result vocabulary (10 buckets) does not match the public
#      evidence serialization (mutation_contract.MutationResult, 6 buckets).
#   3. Wiring it would invalidate every existing mutation-summary.json
#      and downstream consumer.
#
# Future migration: M44 → M42.5 unification is tracked in EXECUTION_PROGRESS
# as a SUPERSEDED milestone. Do not introduce new call sites to
# mutation_execution.orchestrator until a dedicated M44-acceptance campaign
# (with all three gates verified) is run.
#
# This module exposes:
#   * CANONICAL_ENTRYPOINT
#   * CANONICAL_RUNNER_FUNCTION  (the callable everyone should import)
#   * NON_CANONICAL_BACKENDS     (frozen tuple — explicitly listed)
#   * assert_canonical_path_is_used()  — runtime guard for new code paths
#   * authority_audit()          — produce a machine-readable audit report

from __future__ import annotations

import importlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


# ── Canonical declaration ──────────────────────────────────────────────────
CANONICAL_ENTRYPOINT = "runtime.foundation.verification.mutation_runner.run_mutation_cli"
CANONICAL_RUNNER_FUNCTION = (
    "runtime.foundation.verification.mutation_runner.execute_mutation"
)
CANONICAL_RESULT_TYPE = "runtime.foundation.verification.mutation_contract.MutationResult"

# Non-canonical / future-migration backends (declared, not promoted).
NON_CANONICAL_BACKENDS: tuple[str, ...] = (
    "runtime.foundation.verification.mutation_execution.orchestrator.MutationOrchestrator",
    "runtime.foundation.verification.mutation_execution.orchestrator.create_orchestrator",
)


@dataclass(frozen=True, slots=True)
class AuthorityAudit:
    canonical_entrypoint: str
    canonical_runner_function: str
    canonical_result_type: str
    non_canonical_backends: tuple[str, ...]
    canonical_resolvable: bool
    canonical_runner_callable: bool
    canonical_result_resolvable: bool
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["non_canonical_backends"] = list(self.non_canonical_backends)
        return d


def _resolve(dotted: str) -> Any:
    mod_name, _, attr = dotted.rpartition(".")
    if not mod_name:
        return None
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return None
    return getattr(mod, attr, None)


def authority_audit() -> AuthorityAudit:
    """Return a snapshot describing the canonical mutation authority."""
    entry_obj = _resolve(CANONICAL_ENTRYPOINT)
    runner_obj = _resolve(CANONICAL_RUNNER_FUNCTION)
    result_obj = _resolve(CANONICAL_RESULT_TYPE)
    return AuthorityAudit(
        canonical_entrypoint=CANONICAL_ENTRYPOINT,
        canonical_runner_function=CANONICAL_RUNNER_FUNCTION,
        canonical_result_type=CANONICAL_RESULT_TYPE,
        non_canonical_backends=NON_CANONICAL_BACKENDS,
        canonical_resolvable=entry_obj is not None,
        canonical_runner_callable=callable(runner_obj),
        canonical_result_resolvable=result_obj is not None,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


def assert_canonical_path_is_used() -> AuthorityAudit:
    """Raise if any canonical anchor is unresolvable. Use at module-import
    time of new mutation entry points."""
    audit = authority_audit()
    missing = []
    if not audit.canonical_resolvable:
        missing.append(audit.canonical_entrypoint)
    if not audit.canonical_runner_callable:
        missing.append(audit.canonical_runner_function)
    if not audit.canonical_result_resolvable:
        missing.append(audit.canonical_result_type)
    if missing:
        raise RuntimeError(
            "Canonical mutation authority is broken; missing: " + ", ".join(missing)
        )
    return audit


def write_audit(path: str | Path) -> Path:
    """Persist the authority audit as JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(authority_audit().to_dict(), indent=2, sort_keys=True))
    return p


__all__ = [
    "CANONICAL_ENTRYPOINT",
    "CANONICAL_RUNNER_FUNCTION",
    "CANONICAL_RESULT_TYPE",
    "NON_CANONICAL_BACKENDS",
    "AuthorityAudit",
    "authority_audit",
    "assert_canonical_path_is_used",
    "write_audit",
]
