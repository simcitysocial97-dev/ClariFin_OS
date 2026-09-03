"""M9-C44 — Enterprise Mutation Execution Architecture.

Canonical mutation execution subsystem for ClariFin_OS.
Third-party tools (mutmut) are adapters behind a strict backend interface.
ClariFin_OS owns mutation execution semantics.
"""

from runtime.foundation.verification.mutation_execution.backend_interface import (
    MutationBackendBase,
    MutationBackendProtocol,
)
from runtime.foundation.verification.mutation_execution.cache import (
    CacheEntry,
    MutationCache,
    build_cache_key,
    build_fingerprint_for_run,
)
from runtime.foundation.verification.mutation_execution.domain_model import (
    InfrastructureFailureKind,
    MutationCampaign,
    MutationCandidate,
    MutationExecution,
    MutationResult,
    MutationResultState,
    TimeoutKind,
    derive_canonical_mutant_id,
)
from runtime.foundation.verification.mutation_execution.evidence import (
    SCHEMA_VERSION,
    merge_shard_results,
    normalize_backend_results,
    result_to_evidence_artifact,
    result_to_measurement_truth,
)
from runtime.foundation.verification.mutation_execution.forensics import (
    write_forensics,
)
from runtime.foundation.verification.mutation_execution.health import (
    CampaignHealth,
    FailureBudget,
    certification_check,
    compute_health_metrics,
)
from runtime.foundation.verification.mutation_execution.mutmut_adapter import (
    MutmutAdapter,
    create_adapter,
)
from runtime.foundation.verification.mutation_execution.orchestrator import (
    DEFAULT_TIMEOUTS,
    MAX_RETRIES,
    RETRYABLE_FAILURES,
    MutationOrchestrator,
    create_orchestrator,
)
from runtime.foundation.verification.mutation_execution.verify_result import (
    MutationCorrectnessGate,
    classify_invalid_executions,
    verify_campaign_results,
)
from runtime.foundation.verification.mutation_execution.workspace import (
    CAMPAIGNS_ROOT,
    MutationWorkspace,
    create_workspace,
    list_campaigns,
    resume_workspace,
)

__all__ = [
    # Domain model
    "MutationResultState",
    "TimeoutKind",
    "InfrastructureFailureKind",
    "MutationCampaign",
    "MutationCandidate",
    "MutationExecution",
    "MutationResult",
    "derive_canonical_mutant_id",
    # Backend interface
    "MutationBackendProtocol",
    "MutationBackendBase",
    # Adapter
    "MutmutAdapter",
    "create_adapter",
    # Workspace
    "MutationWorkspace",
    "create_workspace",
    "resume_workspace",
    "list_campaigns",
    "CAMPAIGNS_ROOT",
    # Cache
    "MutationCache",
    "CacheEntry",
    "build_cache_key",
    "build_fingerprint_for_run",
    # Orchestrator
    "MutationOrchestrator",
    "create_orchestrator",
    "DEFAULT_TIMEOUTS",
    "MAX_RETRIES",
    "RETRYABLE_FAILURES",
    # Evidence
    "result_to_measurement_truth",
    "result_to_evidence_artifact",
    "normalize_backend_results",
    "merge_shard_results",
    "SCHEMA_VERSION",
    # Verification
    "MutationCorrectnessGate",
    "verify_campaign_results",
    "classify_invalid_executions",
    # Health
    "CampaignHealth",
    "FailureBudget",
    "compute_health_metrics",
    "certification_check",
    # Forensics
    "write_forensics",
]
