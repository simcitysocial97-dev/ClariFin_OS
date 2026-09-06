"""
M9-C49 — Canonical Public CLI Surface.

This module defines the SINGLE authoritative operator-facing command tree for
the ClariFin_OS verification runtime. Every public command maps to one
canonical control-plane operation; no operator decision is exposed about
internal verification capabilities.

The canonical tree:

    verify
    ├── check        — primary verification entrypoint
    ├── plan         — plan-only mode (no execution)
    ├── run          — execute an explicit plan
    ├── diagnose     — failure/survivor diagnostic
    ├── strengthen   — test-strengthening control plane
    ├── inspect      — read-only inspection queries
    │   ├── capabilities
    │   ├── evidence
    │   ├── plan
    │   ├── mutation
    │   ├── workflows
    │   └── health
    ├── certify      — certification (evidence-gated)
    ├── ci           — CI orchestration / reconciliation
    └── doctor       — framework health / integrity

Each top-level operation is a public verb; the control plane selects the
required internal services automatically.

The legacy surface (≈97 dispatchable tokens) is exposed as COMPATIBILITY
aliases that route through the canonical control-plane operations and never
introduce a second semantic authority. See `migration_map()` for the full
compatibility matrix.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CanonicalOperation(str, Enum):
    """The single canonical operator-facing operation vocabulary."""

    CHECK = "check"
    PLAN = "plan"
    RUN = "run"
    DIAGNOSE = "diagnose"
    STRENGTHEN = "strengthen"
    INSPECT = "inspect"
    CERTIFY = "certify"
    CI = "ci"
    DOCTOR = "doctor"


# Public inspect sub-queries. These are not new top-level commands — they are
# routing parameters under `verify inspect`.
class InspectQuery(str, Enum):
    CAPABILITIES = "capabilities"
    EVIDENCE = "evidence"
    PLAN = "plan"
    MUTATION = "mutation"
    WORKFLOWS = "workflows"
    HEALTH = "health"


@dataclass(frozen=True)
class CLINode:
    """A canonical entry on the public command tree."""

    operation: CanonicalOperation
    description: str
    sub_queries: tuple[InspectQuery, ...] = ()


def canonical_tree() -> dict[str, Any]:
    """Return the canonical public CLI tree as a structured document."""
    return {
        "verify": {
            "check": CLINode(
                CanonicalOperation.CHECK,
                "Plan + execute the required verification for the current change "
                "and return evidence + verdict.",
            ).operation.value,
            "plan": CLINode(
                CanonicalOperation.PLAN,
                "Plan-only mode: derive verification obligations without executing.",
            ).operation.value,
            "run": CLINode(
                CanonicalOperation.RUN,
                "Execute an explicit verification plan (machine-readable).",
            ).operation.value,
            "diagnose": CLINode(
                CanonicalOperation.DIAGNOSE,
                "Evidence-backed failure / survivor diagnosis.",
            ).operation.value,
            "strengthen": CLINode(
                CanonicalOperation.STRENGTHEN,
                "Automatic test strengthening pipeline (capability-aware).",
            ).operation.value,
            "inspect": CLINode(
                CanonicalOperation.INSPECT,
                "Read-only inspection queries. Sub-queries: capabilities, "
                "evidence, plan, mutation, workflows, health.",
                sub_queries=tuple(InspectQuery),
            ).operation.value,
            "certify": CLINode(
                CanonicalOperation.CERTIFY,
                "Certification gate (evidence-gated).",
            ).operation.value,
            "ci": CLINode(
                CanonicalOperation.CI,
                "CI-specific orchestration / reconciliation.",
            ).operation.value,
            "doctor": CLINode(
                CanonicalOperation.DOCTOR,
                "Verification framework health / integrity diagnostic.",
            ).operation.value,
        },
        "inspect_subqueries": [q.value for q in InspectQuery],
        "total_top_level_commands": 9,
    }


# Compatibility alias table — every legacy token maps to exactly one canonical
# operation. Adding a new alias requires explicit classification:
#   CANONICAL — direct alias for an operator-facing public verb (rare)
#   INTERNAL — routed internally, hidden from public help
#   COMPATIBILITY — retained for backward compatibility, prints deprecation
#   LEGACY — routed through canonical; printed in `--legacy-list`
#   DEPRECATED — emits hard deprecation warning + canonical redirect
#   DUPLICATE — historically existed but collapsed into canonical; rejected
#   UNREACHABLE — never reachable; preserved only as evidence
#   TEST-ONLY — used only in tests; never exposed
_CLASSIFICATION: dict[str, str] = {
    # compatibility / legacy / deprecated
    "status": "COMPATIBILITY",
    "metrics": "COMPATIBILITY",
    "history": "COMPATIBILITY",
    "deps": "COMPATIBILITY",
    "verify-status": "COMPATIBILITY",
    "analytics": "COMPATIBILITY",
    "health": "DUPLICATE",  # canonical: doctor
    "doctor": "CANONICAL",
    "ci-doctor": "COMPATIBILITY",
    "diagnose": "DUPLICATE",  # canonical: diagnose
    "diagnose-failures": "DEPRECATED",
    "plan": "DUPLICATE",  # canonical: plan (legacy alias)
    "reconcile": "DEPRECATED",  # canonical: ci
    "exec-evidence": "DEPRECATED",  # canonical: ci
    "deep-contract": "DEPRECATED",  # canonical: inspect plan
    "local-gate": "DEPRECATED",  # canonical: plan
    "affected": "DEPRECATED",  # canonical: plan
    "repair": "DEPRECATED",  # canonical: plan
    "risk": "DEPRECATED",  # canonical: plan
    "integrity": "DEPRECATED",  # canonical: doctor
    "knowledge": "DEPRECATED",  # canonical: inspect capabilities
    "dashboard": "DEPRECATED",
    "intelligence": "DEPRECATED",
    "certify-v4": "COMPATIBILITY",
    "certify-v5": "COMPATIBILITY",
    "intelligence-audit": "DEPRECATED",
    "audit": "DEPRECATED",
    "api-contracts": "CANONICAL_ALIAS",  # canonical: contracts profile
    "contract-governance": "DEPRECATED",
    "mutation": "DEPRECATED",  # canonical: strengthen
    "measurement-truth": "DEPRECATED",
    "measurement": "DEPRECATED",
    "evidence-plan": "DEPRECATED",  # canonical: plan
    "verification-contract": "DEPRECATED",
    "evidence-execute": "DEPRECATED",  # canonical: run
    "evidence-reconcile": "DEPRECATED",  # canonical: ci
    "evidence-certify": "DEPRECATED",  # canonical: certify
    "enforce": "DEPRECATED",
    "mutation-inventory": "DEPRECATED",
    "mutation-intel": "DEPRECATED",
    "forensic-diagnose": "DEPRECATED",  # canonical: diagnose
    "forensic-report": "DEPRECATED",
    "strengthen-analyze": "DEPRECATED",  # canonical: strengthen
    "strengthen-discover": "DEPRECATED",
    "strengthen-propose": "DEPRECATED",
    "strengthen-validate": "DEPRECATED",
    "strengthen-survivor-forensic": "DEPRECATED",
    "strengthen-report": "DEPRECATED",
    "env-check": "COMPATIBILITY",
    "env-contract": "DEPRECATED",
    "what-should-i-run": "DEPRECATED",  # canonical: plan
    "capability-inventory": "DEPRECATED",  # canonical: inspect capabilities
    "control-plane-plan": "DEPRECATED",
    "resolve-capabilities": "DEPRECATED",
    "strengthen-capability": "DEPRECATED",  # canonical: strengthen
    "strengthen-survivor": "DEPRECATED",
    "measurement-truth-report": "DEPRECATED",
    "blast-radius": "DEPRECATED",
    "execution-plan": "DEPRECATED",  # canonical: plan
    "execute": "DEPRECATED",  # canonical: run
    "execution-status": "DEPRECATED",  # canonical: inspect evidence
    "execution-report": "DEPRECATED",
    "capabilities": "DEPRECATED",  # canonical: inspect capabilities
    "capability-for": "DEPRECATED",
    "capability-graph": "DEPRECATED",
    "bypass-audit": "DEPRECATED",
    "bypass-enforcement": "DEPRECATED",
    "pipeline-enforcement": "DEPRECATED",
    "scenarios": "DEPRECATED",
    "evidence-integrity": "DEPRECATED",
    "strengthening-integration": "DEPRECATED",
    "cross-capability-impact": "DEPRECATED",
    "config-authority-verify": "DEPRECATED",
    "efficiency": "DEPRECATED",
    "regression": "DEPRECATED",  # canonical: check
    "certify": "CANONICAL",
    "latent-audit": "DEPRECATED",
    "config-authority": "DEPRECATED",
    "generate-test": "DEPRECATED",  # canonical: strengthen
    "c53-scenarios": "DEPRECATED",
    "c53-certify": "DEPRECATED",
    "convergence-status": "DEPRECATED",
    "coverage-analysis": "DEPRECATED",
    "mutation-analysis": "DEPRECATED",
    "gap-analysis": "DEPRECATED",
    "convergence-plan": "DEPRECATED",
    "threshold-assessment": "DEPRECATED",
    "converge": "DEPRECATED",
    "help-resolve": "DEPRECATED",
    # profiles — top-level alias for check (legacy: profile invocation)
    "quick": "CANONICAL_ALIAS",  # canonical: check
    "backend": "CANONICAL_ALIAS",
    "frontend": "CANONICAL_ALIAS",
    "contracts": "CANONICAL_ALIAS",
    "graph": "CANONICAL_ALIAS",
    "full": "CANONICAL_ALIAS",
    "runtime": "CANONICAL_ALIAS",
    "golden": "CANONICAL_ALIAS",
    "playwright": "CANONICAL_ALIAS",
}


def classification_for(token: str) -> str:
    return _CLASSIFICATION.get(token, "UNREACHABLE")


# Migration table: legacy token -> (canonical_operation, internal_route).
# Routes are the *intent* of the legacy command; the control plane selects
# the actual capability implementations. No semantic authority is
# duplicated: legacy invocation dispatches to exactly one canonical op.
_MIGRATION: dict[str, tuple[str, str]] = {
    # legacy diagnostic / planning → plan / diagnose
    "diagnose": ("diagnose", "forensic_diagnose"),
    "diagnose-failures": ("diagnose", "blast_radius_diagnose"),
    "plan": ("plan", "tier_plan"),
    "affected": ("plan", "blast_radius_plan"),
    "repair": ("plan", "repair_plan"),
    "risk": ("plan", "risk_assessment"),
    "intelligence": ("plan", "intelligence_plan"),
    "control-plane-plan": ("plan", "control_plane_plan"),
    "blast-radius": ("plan", "blast_radius"),
    "what-should-i-run": ("plan", "what_should_i_run"),
    "help-resolve": ("plan", "help_resolve"),
    "execution-plan": ("plan", "execution_plan"),
    "evidence-plan": ("plan", "evidence_plan"),
    "verification-contract": ("plan", "verification_contract"),
    "local-gate": ("plan", "local_gate"),
    "deep-contract": ("plan", "deep_contract"),
    "resolve-capabilities": ("plan", "resolve_capabilities"),
    "capability-inventory": ("plan", "capability_inventory"),
    "capabilities": ("plan", "capabilities_query"),
    "capability-for": ("plan", "capability_for_query"),
    "capability-graph": ("plan", "capability_graph_query"),
    "latent-audit": ("plan", "latent_audit"),
    "config-authority": ("plan", "config_authority"),
    # execute / run
    "execute": ("run", "execution_orchestrator_run"),
    "evidence-execute": ("run", "executor_pipeline_run"),
    "enforce": ("run", "execution_enforcer"),
    "regression": ("run", "regression_runner"),
    # diagnose
    "forensic-diagnose": ("diagnose", "forensic_diagnose"),
    "forensic-report": ("diagnose", "forensic_report"),
    "evidence-integrity": ("diagnose", "evidence_integrity"),
    "mutation-intel": ("diagnose", "survivor_intel"),
    "mutation-inventory": ("diagnose", "mutation_inventory"),
    "audit": ("diagnose", "audit_runner"),
    "intelligence-audit": ("diagnose", "intelligence_audit"),
    # strengthen
    "mutation": ("strengthen", "mutation_runner"),
    "strengthen-analyze": ("strengthen", "strengthen_analyze"),
    "strengthen-discover": ("strengthen", "strengthen_discover"),
    "strengthen-propose": ("strengthen", "strengthen_propose"),
    "strengthen-validate": ("strengthen", "strengthen_validate"),
    "strengthen-survivor": ("strengthen", "strengthen_survivor"),
    "strengthen-survivor-forensic": ("strengthen", "strengthen_survivor_forensic"),
    "strengthen-report": ("strengthen", "strengthen_report"),
    "strengthen-capability": ("strengthen", "strengthen_capability"),
    "generate-test": ("strengthen", "test_generation"),
    "converge": ("strengthen", "convergence_pipeline"),
    "c53-scenarios": ("strengthen", "c53_scenarios"),
    "c53-certify": ("strengthen", "c53_certification"),
    "cross-capability-impact": ("strengthen", "cross_capability_impact"),
    "strengthening-integration": ("strengthen", "strengthening_integration"),
    "convergence-status": ("strengthen", "convergence_status"),
    "coverage-analysis": ("strengthen", "coverage_analysis"),
    "mutation-analysis": ("strengthen", "mutation_analysis"),
    "gap-analysis": ("strengthen", "gap_analysis"),
    "convergence-plan": ("strengthen", "convergence_plan"),
    "threshold-assessment": ("strengthen", "threshold_assessment"),
    # inspect
    "knowledge": ("inspect", "knowledge_index"),
    "measurement-truth": ("inspect", "measurement_truth"),
    "measurement": ("inspect", "measurement"),
    "measurement-truth-report": ("inspect", "measurement_truth_report"),
    "execution-report": ("inspect", "execution_report"),
    "execution-status": ("inspect", "execution_status"),
    "contract-governance": ("inspect", "contract_governance"),
    "dashboard": ("inspect", "dashboard"),
    "bypass-audit": ("inspect", "bypass_audit"),
    "scenarios": ("inspect", "scenarios"),
    # certify
    "certify": ("certify", "certification"),
    "certify-v4": ("certify", "certification_v4"),
    "certify-v5": ("certify", "certification_v5"),
    "evidence-certify": ("certify", "evidence_certify"),
    "efficiency": ("certify", "control_plane_efficiency"),
    "config-authority-verify": ("certify", "config_authority_verify"),
    "pipeline-enforcement": ("certify", "pipeline_enforcement"),
    "bypass-enforcement": ("certify", "bypass_enforcement"),
    # ci
    "reconcile": ("ci", "reconcile"),
    "exec-evidence": ("ci", "exec_evidence"),
    "evidence-reconcile": ("ci", "evidence_reconcile"),
    # doctor
    "integrity": ("doctor", "integrity"),
    "health": ("doctor", "health"),
    "env-check": ("doctor", "env_check"),
    "env-contract": ("doctor", "env_contract"),
    "ci-doctor": ("doctor", "ci_doctor"),
    "metrics": ("doctor", "metrics"),
    "history": ("doctor", "history"),
    "verify-status": ("doctor", "verify_status"),
    "analytics": ("doctor", "analytics"),
    "status": ("doctor", "status"),
    "deps": ("doctor", "dependencies"),
}


def migration_map() -> dict[str, dict[str, str]]:
    """Full legacy → canonical migration table for the CLI surface audit."""
    out: dict[str, dict[str, str]] = {}
    for token, (op, route) in _MIGRATION.items():
        out[token] = {
            "canonical_operation": op,
            "internal_route": route,
            "classification": classification_for(token),
        }
    return out


def canonical_help() -> str:
    """Operator-facing help text for the canonical CLI."""
    canonical_tree()
    lines = ["verify <operation> [args]", ""]
    lines.append("Canonical operations:")
    for op in CanonicalOperation:
        node = CLINode(op, "")
        lines.append(f"  {op.value:<12} {node.description}")
    lines.append("")
    lines.append("Inspect sub-queries (under `verify inspect`):")
    for q in InspectQuery:
        lines.append(f"  {q.value}")
    lines.append("")
    lines.append("Examples:")
    lines.append(
        "  verify check                # plan + execute verification for current change"
    )
    lines.append("  verify plan                 # plan only, no execution")
    lines.append("  verify plan --json          # machine-readable plan")
    lines.append("  verify run --plan plan.json # execute a plan")
    lines.append("  verify diagnose             # failure diagnosis")
    lines.append("  verify strengthen           # auto-strengthening pipeline")
    lines.append("  verify inspect capabilities # list capabilities")
    lines.append("  verify inspect evidence     # list open obligations")
    lines.append("  verify certify              # certification gate")
    lines.append("  verify ci                   # CI reconciliation")
    lines.append("  verify doctor               # framework health")
    return "\n".join(lines)


# Number of top-level canonical public commands. Used by governance tests
# to enforce the "small canonical surface" invariant.
CANONICAL_PUBLIC_COMMAND_COUNT = len(CanonicalOperation)
