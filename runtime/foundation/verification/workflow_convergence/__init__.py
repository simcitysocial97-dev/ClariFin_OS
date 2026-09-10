"""
M9-C54 — Modular workflow_convergence sub-package.

This package restructures the former single-file ``workflow_convergence.py``
into focused modules without changing any runtime behaviour. Every public
name that was importable from ``runtime.foundation.verification.workflow_convergence``
remains importable from this package.

Module map::

    workflow_convergence.inventory         — Q1: WorkflowStep, WorkflowJob,
                                             WorkflowInventory, inventory_workflows
    workflow_convergence.equivalence       — Q5: EquivalenceResult, SemanticEquivalence
    workflow_convergence.failure_semantics — Q8: FailureSemantics, build_failure_semantics
    workflow_convergence.c53_integration   — Q14: C53IntegrationCheck, verify_c53_integration
    workflow_convergence.greenness         — Q3: GreennessStatus, GreennessAudit, audit_workflow_greenness
    workflow_convergence.emission          — Q6: CIEmissionAssessment, assess_ci_emission
    workflow_convergence.bypass            — Q7: BypassRisk, BypassAnalysis, analyze_workflow_bypass
    workflow_convergence.measurement_integrity — Q10: MeasurementIntegrity, assess_measurement_integrity
    workflow_convergence.duplication       — Q11: DuplicationFinding, analyze_duplication
    workflow_convergence.environment       — Q12: EnvironmentContract, build_environment_contract
    workflow_convergence.scenarios         — Q13: ScenarioResult, execute_scenarios
    workflow_convergence.efficiency        — Q16: EfficiencyMetric, measure_efficiency
    workflow_convergence.mapping           — Q2: CapabilityMapping, map_workflows_to_capabilities
    workflow_convergence.evidence_contract — Q4: EvidenceContractEntry, build_evidence_contract
    workflow_convergence.coverage          — Q9: CoverageRow, build_coverage_matrix
    workflow_convergence.failure_injection — Q15: FailureInjectionRow, build_failure_injection_matrix
    workflow_convergence.certification_gates — Q20: CertificationGate, evaluate_certification_gates
    workflow_convergence.artifacts         — get_repository_sha, generate_all_artifacts
"""
from __future__ import annotations


__all__: list[str] = [
    # Q1 — inventory
    "WorkflowStep",
    "WorkflowJob",
    "WorkflowInventory",
    "inventory_workflows",
    "resolve_extended_semantics",
    "_safe_parse_yaml",
    "_extract_env",
    "_extract_timeout",
    "_is_upload_step",
    "_is_verification_uses",
    "_build_additional_patterns",
    # Q2 — capability mapping
    "CapabilityMapping",
    "map_workflows_to_capabilities",
    "_infer_capability",
    # Q3 — greenness audit
    "GreennessStatus",
    "GreennessAudit",
    "audit_workflow_greenness",
    # Q4 — evidence contract
    "EvidenceContractEntry",
    "build_evidence_contract",
    "_infer_evidence_path",
    # Q5 — semantic equivalence
    "EquivalenceResult",
    "SemanticEquivalence",
    "check_semantic_equivalence",
    # Q6 — CI emission
    "CIEmissionAssessment",
    "assess_ci_emission",
    # Q7 — bypass analysis
    "BypassRisk",
    "BypassAnalysis",
    "analyze_workflow_bypass",
    # Q8 — failure semantics
    "FailureSemantics",
    "build_failure_semantics",
    # Q9 — coverage matrix
    "CoverageRow",
    "build_coverage_matrix",
    # Q10 — measurement integrity
    "MeasurementIntegrity",
    "assess_measurement_integrity",
    # Q11 — duplication
    "DuplicationFinding",
    "analyze_duplication",
    # Q12 — environment contract
    "EnvironmentContract",
    "build_environment_contract",
    # Q13 — scenarios
    "ScenarioResult",
    "execute_scenarios",
    # Q14 — C53 integration
    "C53IntegrationCheck",
    "verify_c53_integration",
    # Q15 — failure injection matrix
    "FailureInjectionRow",
    "build_failure_injection_matrix",
    # Q16 — efficiency
    "EfficiencyMetric",
    "measure_efficiency",
    # Q20 — certification gates
    "CertificationGate",
    "evaluate_certification_gates",
    # utilities
    "get_repository_sha",
    "generate_all_artifacts",
]

# ---------------------------------------------------------------------------
# Module map for lazy one-shot imports via __getattr__
# ---------------------------------------------------------------------------

_MODULE_MAP: dict[str, tuple[str, str | None]] = {
    # Q1 — inventory
    "WorkflowStep": ("runtime.foundation.verification.workflow_convergence.inventory", "WorkflowStep"),
    "WorkflowJob": ("runtime.foundation.verification.workflow_convergence.inventory", "WorkflowJob"),
    "WorkflowInventory": ("runtime.foundation.verification.workflow_convergence.inventory", "WorkflowInventory"),
    "inventory_workflows": ("runtime.foundation.verification.workflow_convergence.inventory", "inventory_workflows"),
    "resolve_extended_semantics": ("runtime.foundation.verification.workflow_convergence.inventory", "resolve_extended_semantics"),
    "_safe_parse_yaml": ("runtime.foundation.verification.workflow_convergence.inventory", "_safe_parse_yaml"),
    "_extract_env": ("runtime.foundation.verification.workflow_convergence.inventory", "_extract_env"),
    "_extract_timeout": ("runtime.foundation.verification.workflow_convergence.inventory", "_extract_timeout"),
    "_is_upload_step": ("runtime.foundation.verification.workflow_convergence.inventory", "_is_upload_step"),
    "_is_verification_uses": ("runtime.foundation.verification.workflow_convergence.inventory", "_is_verification_uses"),
    "_build_additional_patterns": ("runtime.foundation.verification.workflow_convergence.inventory", "_build_additional_patterns"),
    # Q2 — capability mapping
    "CapabilityMapping": ("runtime.foundation.verification.workflow_convergence.mapping", "CapabilityMapping"),
    "map_workflows_to_capabilities": ("runtime.foundation.verification.workflow_convergence.mapping", "map_workflows_to_capabilities"),
    "_infer_capability": ("runtime.foundation.verification.workflow_convergence.mapping", "_infer_capability"),
    # Q3 — greenness audit
    "GreennessStatus": ("runtime.foundation.verification.workflow_convergence.greenness", "GreennessStatus"),
    "GreennessAudit": ("runtime.foundation.verification.workflow_convergence.greenness", "GreennessAudit"),
    "audit_workflow_greenness": ("runtime.foundation.verification.workflow_convergence.greenness", "audit_workflow_greenness"),
    # Q4 — evidence contract
    "EvidenceContractEntry": ("runtime.foundation.verification.workflow_convergence.evidence_contract", "EvidenceContractEntry"),
    "build_evidence_contract": ("runtime.foundation.verification.workflow_convergence.evidence_contract", "build_evidence_contract"),
    "_infer_evidence_path": ("runtime.foundation.verification.workflow_convergence.evidence_contract", "_infer_evidence_path"),
    # Q5 — semantic equivalence
    "EquivalenceResult": ("runtime.foundation.verification.workflow_convergence.equivalence", "EquivalenceResult"),
    "SemanticEquivalence": ("runtime.foundation.verification.workflow_convergence.equivalence", "SemanticEquivalence"),
    "check_semantic_equivalence": ("runtime.foundation.verification.workflow_convergence.equivalence", "check_semantic_equivalence"),
    # Q6 — CI emission
    "CIEmissionAssessment": ("runtime.foundation.verification.workflow_convergence.emission", "CIEmissionAssessment"),
    "assess_ci_emission": ("runtime.foundation.verification.workflow_convergence.emission", "assess_ci_emission"),
    # Q7 — bypass analysis
    "BypassRisk": ("runtime.foundation.verification.workflow_convergence.bypass", "BypassRisk"),
    "BypassAnalysis": ("runtime.foundation.verification.workflow_convergence.bypass", "BypassAnalysis"),
    "analyze_workflow_bypass": ("runtime.foundation.verification.workflow_convergence.bypass", "analyze_workflow_bypass"),
    # Q8 — failure semantics
    "FailureSemantics": ("runtime.foundation.verification.workflow_convergence.failure_semantics", "FailureSemantics"),
    "build_failure_semantics": ("runtime.foundation.verification.workflow_convergence.failure_semantics", "build_failure_semantics"),
    # Q9 — coverage matrix
    "CoverageRow": ("runtime.foundation.verification.workflow_convergence.coverage", "CoverageRow"),
    "build_coverage_matrix": ("runtime.foundation.verification.workflow_convergence.coverage", "build_coverage_matrix"),
    # Q10 — measurement integrity
    "MeasurementIntegrity": ("runtime.foundation.verification.workflow_convergence.measurement_integrity", "MeasurementIntegrity"),
    "assess_measurement_integrity": ("runtime.foundation.verification.workflow_convergence.measurement_integrity", "assess_measurement_integrity"),
    # Q11 — duplication
    "DuplicationFinding": ("runtime.foundation.verification.workflow_convergence.duplication", "DuplicationFinding"),
    "analyze_duplication": ("runtime.foundation.verification.workflow_convergence.duplication", "analyze_duplication"),
    # Q12 — environment contract
    "EnvironmentContract": ("runtime.foundation.verification.workflow_convergence.environment", "EnvironmentContract"),
    "build_environment_contract": ("runtime.foundation.verification.workflow_convergence.environment", "build_environment_contract"),
    # Q13 — scenarios
    "ScenarioResult": ("runtime.foundation.verification.workflow_convergence.scenarios", "ScenarioResult"),
    "execute_scenarios": ("runtime.foundation.verification.workflow_convergence.scenarios", "execute_scenarios"),
    # Q14 — C53 integration
    "C53IntegrationCheck": ("runtime.foundation.verification.workflow_convergence.c53_integration", "C53IntegrationCheck"),
    "verify_c53_integration": ("runtime.foundation.verification.workflow_convergence.c53_integration", "verify_c53_integration"),
    # Q15 — failure injection matrix
    "FailureInjectionRow": ("runtime.foundation.verification.workflow_convergence.failure_injection", "FailureInjectionRow"),
    "build_failure_injection_matrix": ("runtime.foundation.verification.workflow_convergence.failure_injection", "build_failure_injection_matrix"),
    # Q16 — efficiency
    "EfficiencyMetric": ("runtime.foundation.verification.workflow_convergence.efficiency", "EfficiencyMetric"),
    "measure_efficiency": ("runtime.foundation.verification.workflow_convergence.efficiency", "measure_efficiency"),
    # Q20 — certification gates
    "CertificationGate": ("runtime.foundation.verification.workflow_convergence.certification_gates", "CertificationGate"),
    "evaluate_certification_gates": ("runtime.foundation.verification.workflow_convergence.certification_gates", "evaluate_certification_gates"),
    # utilities
    "get_repository_sha": ("runtime.foundation.verification.workflow_convergence.artifacts", "get_repository_sha"),
    "generate_all_artifacts": ("runtime.foundation.verification.workflow_convergence.artifacts", "generate_all_artifacts"),
}


def __getattr__(name: str):
    """Lazy one-shot imports — avoids circular-import headaches during
    package initialisation while keeping every public name resolvable."""
    import importlib  # noqa: PLC0415

    if name in _MODULE_MAP:
        mod_path, attr = _MODULE_MAP[name]
        mod = importlib.import_module(mod_path)
        return getattr(mod, attr) if attr else mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
