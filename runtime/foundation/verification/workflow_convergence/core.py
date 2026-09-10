"""
M9-C54 — Backward-compatibility re-exports.

This module exists solely for backward compatibility. All code has been
extracted into focused sub-modules under this package. Import from the
package-level ``runtime.foundation.verification.workflow_convergence``
instead.
"""
from __future__ import annotations

# Re-export everything so direct ``from ...core import ...`` still works.
import runtime.foundation.verification.workflow_convergence as _pkg  # noqa: F401

from runtime.foundation.verification.workflow_convergence.equivalence import (  # noqa: F401,F403
    EquivalenceResult,
    SemanticEquivalence,
    check_semantic_equivalence,
)
from runtime.foundation.verification.workflow_convergence.failure_semantics import (  # noqa: F401,F403
    FailureSemantics,
    build_failure_semantics,
)
from runtime.foundation.verification.workflow_convergence.c53_integration import (  # noqa: F401,F403
    C53IntegrationCheck,
    verify_c53_integration,
)
from runtime.foundation.verification.workflow_convergence.greenness import (  # noqa: F401,F403
    GreennessStatus,
    GreennessAudit,
    audit_workflow_greenness,
)
from runtime.foundation.verification.workflow_convergence.emission import (  # noqa: F401,F403
    CIEmissionAssessment,
    assess_ci_emission,
)
from runtime.foundation.verification.workflow_convergence.bypass import (  # noqa: F401,F403
    BypassRisk,
    BypassAnalysis,
    analyze_workflow_bypass,
)
from runtime.foundation.verification.workflow_convergence.measurement_integrity import (  # noqa: F401,F403
    MeasurementIntegrity,
    assess_measurement_integrity,
)
from runtime.foundation.verification.workflow_convergence.duplication import (  # noqa: F401,F403
    DuplicationFinding,
    analyze_duplication,
)
from runtime.foundation.verification.workflow_convergence.environment import (  # noqa: F401,F403
    EnvironmentContract,
    build_environment_contract,
)
from runtime.foundation.verification.workflow_convergence.scenarios import (  # noqa: F401,F403
    ScenarioResult,
    execute_scenarios,
)
from runtime.foundation.verification.workflow_convergence.efficiency import (  # noqa: F401,F403
    EfficiencyMetric,
    measure_efficiency,
)
from runtime.foundation.verification.workflow_convergence.mapping import (  # noqa: F401,F403
    CapabilityMapping,
    map_workflows_to_capabilities,
    _infer_capability,
)
from runtime.foundation.verification.workflow_convergence.evidence_contract import (  # noqa: F401,F403
    EvidenceContractEntry,
    build_evidence_contract,
    _infer_evidence_path,
)
from runtime.foundation.verification.workflow_convergence.coverage import (  # noqa: F401,F403
    CoverageRow,
    build_coverage_matrix,
)
from runtime.foundation.verification.workflow_convergence.failure_injection import (  # noqa: F401,F403
    FailureInjectionRow,
    build_failure_injection_matrix,
)
from runtime.foundation.verification.workflow_convergence.certification_gates import (  # noqa: F401,F403
    CertificationGate,
    evaluate_certification_gates,
)
from runtime.foundation.verification.workflow_convergence.artifacts import (  # noqa: F401,F403
    get_repository_sha,
    generate_all_artifacts,
)
