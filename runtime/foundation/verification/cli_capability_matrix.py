# runtime/foundation/verification/cli_capability_matrix.py
#
# M9-C52.3 — CLI Capability Matrix.
#
# Produces a complete, source-derived classification of every CLI route in
# verify.py against the capability catalog. Each route is classified with:
#   - command, implementation, owning capability, verification profile,
#   - evidence kind, executable/diagnostic/strengthening flags,
#   - alias relationship, derivation source, and classification rationale.
#
# This matrix closes the C51 gap (28 routes unmapped -> 12 explicitly
# classified as out-of-scope/superseded; the rest now owned by catalog).

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.capability_catalog import CapabilityCatalogBuilder
from runtime.foundation.verification.route_authority import analyze_dispatch_table

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_VERIFY_PY = REPO_ROOT / "runtime" / "verify.py"

_CLI_ROUTE_RE = re.compile(r"verify\.py\s+(\S+)")


def _command_routes(command: str) -> list[str]:
    """Extract route tokens from a catalog command string (same logic as catalog_certification)."""
    routes: list[str] = []
    if not command:
        return routes
    m = _CLI_ROUTE_RE.search(command)
    if not m:
        return routes
    tail = command[m.start(1) :]
    for part in tail.split(" | "):
        tok = re.sub(r"\[.*$", "", part).strip().split()[0] if part.strip() else ""
        if tok and re.match(r"^[a-z0-9._-]+$", tok) and tok not in routes:
            routes.append(tok)
    return routes


@dataclass
class CliRouteEntry:
    """Complete classification for one CLI route."""

    route: str
    implementation: str
    owning_capability: str
    verification_profile: str | None
    evidence_kind: str
    executable: bool
    diagnostic: bool
    strengthening_related: bool
    alias_of: str | None
    classification: str
    derivation_source: str
    notes: str


def _route_implementations() -> dict[str, str]:
    """Map route -> implementation module from dispatcher AST."""
    bindings = analyze_dispatch_table()
    return {r: entries[0]["target"] for r, entries in bindings.items() if entries}


def _catalog_claims() -> dict[str, str]:
    """Map route -> capability_id from catalog entries' commands."""
    catalog = CapabilityCatalogBuilder().build()
    claims: dict[str, str] = {}
    for e in catalog.entries:
        for route in _command_routes(e.command):
            claims[route] = e.capability_id
    return claims


def _classify_route(
    route: str,
    impl: str,
    catalog_claim: str | None,
) -> CliRouteEntry:
    """Classify a single route with full derivation."""

    # ---- 11 NEW_CAPABILITY (added to catalog in M52.3) ----
    new_caps = {
        "capability-graph": CliRouteEntry(
            route="capability-graph",
            implementation="runtime.foundation.verification.capability_graph",
            owning_capability="discover.capability-graph",
            verification_profile=None,
            evidence_kind="capability_graph",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.3: C51 control-plane route, absent from catalog. "
                "Added as discover.capability-graph (stage DISCOVERY)."
            ),
            notes="Derived from capability_discovery->capability_graph pipeline.",
        ),
        "latent-audit": CliRouteEntry(
            route="latent-audit",
            implementation="runtime.foundation.verification.capability_latent_audit",
            owning_capability="discover.latent-capability-audit",
            verification_profile=None,
            evidence_kind="latent_capability_audit",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.3: C51 control-plane route, absent from catalog. "
                "Added as discover.latent-capability-audit (stage DISCOVERY)."
            ),
            notes="Classifies latent capabilities; never deletes.",
        ),
        "bypass-audit": CliRouteEntry(
            route="bypass-audit",
            implementation="runtime.foundation.verification.capability_discovery",
            owning_capability="diagnose.bypass-audit",
            verification_profile=None,
            evidence_kind="bypass_risk_analysis",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.3: C51 control-plane route, absent from catalog. "
                "Added as diagnose.bypass-audit (stage DIAGNOSIS)."
            ),
            notes="Feeds M52.6 bypass-enforcement.",
        ),
        "env-check": CliRouteEntry(
            route="env-check",
            implementation="runtime.foundation.verification.env",
            owning_capability="exec.environment-check",
            verification_profile=None,
            evidence_kind="environment_fingerprint",
            executable=True,
            diagnostic=False,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.3: C42.5 canonical environment check, absent from catalog. "
                "Added as exec.environment-check (stage EXECUTION)."
            ),
            notes="Precondition for blast-radius + config-authority.",
        ),
        "env-contract": CliRouteEntry(
            route="env-contract",
            implementation="runtime.foundation.verification.env_contract",
            owning_capability="exec.environment-contract",
            verification_profile=None,
            evidence_kind="environment_contract",
            executable=True,
            diagnostic=False,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M9-C55: Authoritative environment contract for reproducible "
                "verification. Extends env-check with full identity dimensions."
            ),
            notes="C55 convergence milestone — single authoritative environment contract.",
        ),
        "evidence-execute": CliRouteEntry(
            route="evidence-execute",
            implementation="runtime.foundation.verification.executor_pipeline",
            owning_capability="exec.evidence-execute",
            verification_profile=None,
            evidence_kind="execution_evidence",
            executable=True,
            diagnostic=False,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.3: C42.28 evidence-pipeline execute route, absent from catalog. "
                "Added as exec.evidence-execute (stage EXECUTION)."
            ),
            notes="Runs plan with targeted mutation scope.",
        ),
        "exec-evidence": CliRouteEntry(
            route="exec-evidence",
            implementation="runtime/verify.py:cmd_exec_evidence",
            owning_capability="exec.execution-evidence",
            verification_profile=None,
            evidence_kind="execution_evidence",
            executable=True,
            diagnostic=False,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.3: VEA-5 M5-C execution evidence emission, absent from catalog. "
                "Added as exec.execution-evidence (stage EXECUTION)."
            ),
            notes="Emits unit_id -> attempt -> artifact.",
        ),
        "config-authority": CliRouteEntry(
            route="config-authority",
            implementation="runtime.foundation.verification.configuration_authority",
            owning_capability="evidence.config-authority",
            verification_profile=None,
            evidence_kind="configuration_authority_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.3: C51 configuration authority CLI, absent from catalog. "
                "Added as evidence.config-authority (stage EVIDENCE_INSPECTION)."
            ),
            notes="Detects toolchain config drift.",
        ),
        "evidence-reconcile": CliRouteEntry(
            route="evidence-reconcile",
            implementation="runtime.foundation.verification.executor_pipeline",
            owning_capability="evidence.reconcile-pipeline",
            verification_profile=None,
            evidence_kind="reconciliation_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.3: C42.28 evidence-pipeline reconciliation route, absent from catalog. "
                "Added as evidence.reconcile-pipeline (stage EVIDENCE_INSPECTION)."
            ),
            notes="Reconciles plan vs evidence without mutation.",
        ),
        "reconcile": CliRouteEntry(
            route="reconcile",
            implementation="runtime/verify.py:cmd_reconcile",
            owning_capability="evidence.reconcile",
            verification_profile=None,
            evidence_kind="reconciliation_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.3: VEA-5 M4/M5 CI reconciliation gate, absent from catalog. "
                "Added as evidence.reconcile (stage EVIDENCE_INSPECTION)."
            ),
            notes="CI gate: same-plan or environment-divergence.",
        ),
        "evidence-certify": CliRouteEntry(
            route="evidence-certify",
            implementation="runtime.foundation.verification.executor_pipeline",
            owning_capability="certify.evidence-pipeline",
            verification_profile=None,
            evidence_kind="certification_report",
            executable=True,
            diagnostic=False,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.3: C42.28 evidence-pipeline certify route, absent from catalog. "
                "Added as certify.evidence-pipeline (stage CERTIFICATION)."
            ),
            notes="Canonical evidence-driven certification path.",
        ),
        "knowledge": CliRouteEntry(
            route="knowledge",
            implementation="runtime.foundation.knowledge.indexer",
            owning_capability="evidence.knowledge-base",
            verification_profile=None,
            evidence_kind="knowledge_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.3: C3/C42 knowledge base CLI, absent from catalog. "
                "Added as evidence.knowledge-base (stage EVIDENCE_INSPECTION)."
            ),
            notes="Sub-routes: endpoint|capability|workspace|rule|component.",
        ),
    }

    if route in new_caps:
        return new_caps[route]

    # M9-C52.4 — verification-contract (new control-plane entry point)
    if route == "verification-contract":
        return CliRouteEntry(
            route="verification-contract",
            implementation="runtime.foundation.verification.verification_contract",
            owning_capability="plan.verification-contract",
            verification_profile=None,
            evidence_kind="verification_decision",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.4: Unified change→capability→plan contract. Composes C50 "
                "blast-radius + C51 capability resolution + C42.27 evidence "
                "planner into a single canonical decision object."
            ),
            notes="Single source of truth for 'given this change, what verification is required?'.",
        )

    # M9-C52.5 — enforce (new control-plane execution enforcer)
    if route == "enforce":
        return CliRouteEntry(
            route="enforce",
            implementation="runtime.foundation.verification.execution_enforcer",
            owning_capability="exec.enforce",
            verification_profile=None,
            evidence_kind="enforcement_result",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.5: Execution enforcement boundary. Fail-closed executor that "
                "enforces the VerificationDecision: refuses out-of-scope, stale "
                "evidence, scope creep, fingerprint mismatches."
            ),
            notes="The enforcement gate; no silent bypass of the contract.",
        )

    # M9-C52.6 — bypass-enforcement (new control-plane bypass auditor)
    if route == "bypass-enforcement":
        return CliRouteEntry(
            route="bypass-enforcement",
            implementation="runtime.foundation.verification.bypass_enforcement",
            owning_capability="audit.bypass-enforcement",
            verification_profile=None,
            evidence_kind="bypass_enforcement_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.6: Bypass resistance. Enumerates and classifies all executable "
                "bypass paths (direct pytest, direct mutmut, stale evidence, etc.) "
                "with SAFE/CONTROLLED/INTENTIONAL_LOW_LEVEL_ESCAPE/BYPASS_RISK/"
                "BLOCKING_BYPASS classification."
            ),
            notes="The bypass auditor; no silent bypass path unclassified.",
        )

    # M9-C52.7 — pipeline-enforcement (new control-plane pipeline auditor)
    if route == "pipeline-enforcement":
        return CliRouteEntry(
            route="pipeline-enforcement",
            implementation="runtime.foundation.verification.pipeline_enforcement",
            owning_capability="audit.pipeline-enforcement",
            verification_profile=None,
            evidence_kind="pipeline_enforcement_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.7: Pipeline spine enforcement. Proves the executable runtime "
                "follows the certified 9-stage pipeline spine (changed-file → "
                "blast-radius → capability-resolution → execution-plan → execute → "
                "measurement-truth → diagnostic → strengthening → certification)."
            ),
            notes="The pipeline auditor; no stage silently disappears.",
        )

    # M9-C52.8 — scenarios (new control-plane scenario runner)
    if route == "scenarios":
        return CliRouteEntry(
            route="scenarios",
            implementation="runtime.foundation.verification.scenario_harness",
            owning_capability="audit.scenarios",
            verification_profile=None,
            evidence_kind="scenario_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.8: Real repository change scenarios. Executes 10 real scenarios "
                "(A-J) through the live framework: no change, engine change, test change, "
                "config change, workflow change, new capability, drift, duplicate route, "
                "bypass attempt, stale evidence."
            ),
            notes="The scenario runner; validates end-to-end behavior.",
        )

    # M52.9 — evidence-integrity (new control-plane evidence auditor)
    if route == "evidence-integrity":
        return CliRouteEntry(
            route="evidence-integrity",
            implementation="runtime.foundation.verification.evidence_integrity",
            owning_capability="audit.evidence-integrity",
            verification_profile=None,
            evidence_kind="evidence_integrity_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.9: Evidence/certification integrity. Verifies fail-closed verdicts "
                "for missing change detection, missing capability resolution, missing "
                "planner output, missing execution evidence, stale evidence, invalid "
                "evidence, missing diagnostic stage, missing strengthening stage, missing "
                "certification inputs, contradictory evidence, scope mismatch."
            ),
            notes="The evidence auditor; certifies the certification integrity.",
        )

    # M52.10 — strengthening-integration (new control-plane strengthening handoff verifier)
    if route == "strengthening-integration":
        return CliRouteEntry(
            route="strengthening-integration",
            implementation="runtime.foundation.verification.strengthening_integration",
            owning_capability="audit.strengthening-integration",
            verification_profile=None,
            evidence_kind="strengthening_integration_report",
            executable=True,
            diagnostic=True,
            strengthening_related=True,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.10: Strengthening handoff verification. Verifies equivalent/defensive "
                "survivors don't become tests, measurement failures don't become tests, "
                "production-defect candidates don't become tests automatically, human auth mandatory."
            ),
            notes="The strengthening auditor; verifies evidence-driven handoff.",
        )

    # M52.11 — cross-capability-impact (new control-plane dependency enforcer)
    if route == "cross-capability-impact":
        return CliRouteEntry(
            route="cross-capability-impact",
            implementation="runtime.foundation.verification.cross_capability_impact",
            owning_capability="audit.cross-capability-impact",
            verification_profile=None,
            evidence_kind="cross_capability_impact_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.11: Cross-capability dependency enforcement. Uses C51 capability "
                "graph to determine DIRECTLY_AFFECTED | DEPENDENCY_AFFECTED | "
                "SHARED_INFRASTRUCTURE_AFFECTED | UNAFFECTED."
            ),
            notes="The dependency auditor; verifies impact propagation.",
        )

    # M52.12 — config-authority-verify (new control-plane config enforcer)
    if route == "config-authority-verify":
        return CliRouteEntry(
            route="config-authority-verify",
            implementation="runtime.foundation.verification.configuration_authority_enforcement",
            owning_capability="audit.config-authority-verify",
            verification_profile=None,
            evidence_kind="configuration_authority_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.12: Configuration authority enforcement. Verifies canonical "
                "pytest/ruff/black/mypy/mutmut configs, detects drift, enforces authority."
            ),
            notes="The config auditor; verifies toolchain configuration authority.",
        )

    # M52.13 — efficiency (new control-plane efficiency measurer)
    if route == "efficiency":
        return CliRouteEntry(
            route="efficiency",
            implementation="runtime.foundation.verification.control_plane_efficiency",
            owning_capability="audit.efficiency",
            verification_profile=None,
            evidence_kind="efficiency_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.13: Control-plane efficiency measurement. Measures planning latency, "
                "discovery latency, execution latency, evidence reconciliation latency, "
                "mutation work avoided, tests avoided, total certification latency."
            ),
            notes="The efficiency measurer; measures control-plane overhead.",
        )

    # M52.14 — regression (new control-plane regression runner)
    if route == "regression":
        return CliRouteEntry(
            route="regression",
            implementation="runtime.foundation.verification.regression",
            owning_capability="audit.regression",
            verification_profile=None,
            evidence_kind="regression_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.14: Full regression. Runs C42/C48/C50/C51/C52 tests, static checks, "
                "CLI smoke tests, scenario harnesses."
            ),
            notes="The regression runner; verifies all prior milestones.",
        )

    # M52.15 — certify (new control-plane certification engine)
    if route == "certify":
        return CliRouteEntry(
            route="certify",
            implementation="runtime.foundation.verification.certification",
            owning_capability="certify.control-plane",
            verification_profile=None,
            evidence_kind="certification_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M52.15: Final control-plane certification engine. Verifies all gates "
                "G1-G30. Every claim reproducible from artifacts."
            ),
            notes="The final certifier; produces the certification verdict.",
        )

    # ── M9-C53 — Automatic Test Generation & Evidence-Driven Strengthening ───

    if route == "generate-test":
        return CliRouteEntry(
            route="generate-test",
            implementation="runtime.foundation.verification.generation_engine",
            owning_capability="strengthen.auto-test-generation",
            verification_profile=None,
            evidence_kind="generation_result",
            executable=True,
            diagnostic=True,
            strengthening_related=True,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M9-C53: Automatic test generation engine. Composes gap classification "
                "(A-G), generation eligibility, candidate generation, 8-dimension "
                "validation, authorization boundary, and targeted revalidation into "
                "one coherent pipeline."
            ),
            notes="Evidence-driven test generation; never self-approves.",
        )

    if route == "c53-scenarios":
        return CliRouteEntry(
            route="c53-scenarios",
            implementation="runtime.foundation.verification.c53_scenarios",
            owning_capability="audit.c53-scenarios",
            verification_profile=None,
            evidence_kind="scenario_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M9-C53: Real repository scenarios A-N. Validates genuine-gap detection, "
                "refusal behavior, generation, validation, authorization, and "
                "cross-capability targeting."
            ),
            notes="The C53 scenario runner; validates end-to-end generation behavior.",
        )

    if route == "c53-certify":
        return CliRouteEntry(
            route="c53-certify",
            implementation="runtime.foundation.verification.c53_certification",
            owning_capability="certify.c53",
            verification_profile=None,
            evidence_kind="certification_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="NEW_CAPABILITY",
            derivation_source=(
                "M9-C53: C53 certification engine. Verifies all gates G1-G16. "
                "Every claim derived from artifacts and executable evidence."
            ),
            notes="The C53 certifier; produces the C53 certification verdict.",
        )

    # ---- 4 OWNED_BY_EXISTING (route-claim extension) ----
    if route in (
        "capabilities",
        "execution-report",
        "strengthen-analyze",
        "strengthen-report",
    ):
        owned = {
            "capabilities": CliRouteEntry(
                route="capabilities",
                implementation="runtime.foundation.verification.capability_catalog",
                owning_capability="discover.capability-inventory",
                verification_profile=None,
                evidence_kind="capability_catalog",
                executable=True,
                diagnostic=True,
                strengthening_related=False,
                alias_of=None,
                classification="OWNED_BY_EXISTING",
                derivation_source=(
                    "M52.3: C51 route, claimed by discover.capability-inventory "
                    "(alternate display surface: stage filter vs capability/profile/category)."
                ),
                notes="Extended discover.capability-inventory command with '| capabilities'.",
            ),
            "execution-report": CliRouteEntry(
                route="execution-report",
                implementation="runtime/verify.py:execution-report",
                owning_capability="evidence.execution-status",
                verification_profile=None,
                evidence_kind="execution_report",
                executable=True,
                diagnostic=True,
                strengthening_related=False,
                alias_of=None,
                classification="OWNED_BY_EXISTING",
                derivation_source=(
                    "M52.3: Same data source as execution-status, different output format. "
                    "Extended evidence.execution-status command with '| execution-report'."
                ),
                notes="Inline argparse reading C49 report JSON.",
            ),
            "strengthen-analyze": CliRouteEntry(
                route="strengthen-analyze",
                implementation="runtime.foundation.verification.forensic_cli",
                owning_capability="strengthen.forensic",
                verification_profile=None,
                evidence_kind="forensic_report",
                executable=True,
                diagnostic=True,
                strengthening_related=True,
                alias_of=None,
                classification="OWNED_BY_EXISTING",
                derivation_source=(
                    "M52.3: C42.31 strengthen-analyze route, claimed by strengthen.forensic. "
                    "Extended strengthen.forensic command with '| strengthen-analyze'."
                ),
                notes="Part of forensic family: discover->analyze->propose->validate.",
            ),
            "strengthen-report": CliRouteEntry(
                route="strengthen-report",
                implementation="runtime.foundation.verification.forensic_cli",
                owning_capability="strengthen.forensic",
                verification_profile=None,
                evidence_kind="forensic_report",
                executable=True,
                diagnostic=True,
                strengthening_related=True,
                alias_of=None,
                classification="OWNED_BY_EXISTING",
                derivation_source=(
                    "M52.3: C42.31 strengthen-report route, claimed by strengthen.forensic. "
                    "Extended strengthen.forensic command with '| strengthen-report'."
                ),
                notes="Part of forensic family: discover->analyze->propose->validate->report.",
            ),
        }
        return owned[route]

    # ---- 1 ALIAS ----
    if route == "doctor":
        return CliRouteEntry(
            route="doctor",
            implementation="runtime/verify.py:cmd_doctor -> runtime.system.observability.health_report",
            owning_capability="(alias of health)",
            verification_profile=None,
            evidence_kind="environment_fingerprint",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of="health",
            classification="ALIAS",
            derivation_source=(
                "M52.3: cmd_doctor literally returns cmd_health(). True alias."
            ),
            notes="No separate capability needed.",
        )

    # ---- 7 LEGACY_SUPERSEDED (preserved, explicitly marked) ----
    legacy = {
        "affected": CliRouteEntry(
            route="affected",
            implementation="runtime.foundation.intelligence (blast_radius+verification_plan)",
            owning_capability="(superseded by discover.blast-radius)",
            verification_profile=None,
            evidence_kind="blast_radius_contract",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="LEGACY_SUPERSEDED",
            derivation_source=(
                "M52.3: C42 legacy blast radius (intelligence.blast_radius). "
                "Superseded by C50's discover.blast-radius (canonical, verified)."
            ),
            notes="Preserved; operator should use discover.blast-radius.",
        ),
        "certify-v4": CliRouteEntry(
            route="certify-v4",
            implementation="runtime.foundation.intelligence.platform.certification",
            owning_capability="(superseded by C42.38/C48 certification family)",
            verification_profile=None,
            evidence_kind="certification_report",
            executable=True,
            diagnostic=False,
            strengthening_related=False,
            alias_of=None,
            classification="LEGACY_SUPERSEDED",
            derivation_source=(
                "M52.3: Program 14.0 legacy platform certification. "
                "Superseded by C42.38/C48 certified verification certification family."
            ),
            notes="Preserved for historical auditability.",
        ),
        "certify-v5": CliRouteEntry(
            route="certify-v5",
            implementation="runtime.foundation.intelligence.platform.certification",
            owning_capability="(superseded by C42.38/C48 certification family)",
            verification_profile=None,
            evidence_kind="certification_report",
            executable=True,
            diagnostic=False,
            strengthening_related=False,
            alias_of=None,
            classification="LEGACY_SUPERSEDED",
            derivation_source=(
                "M52.3: Program 14.1 legacy platform certification. "
                "Superseded by C42.38/C48 certified verification certification family."
            ),
            notes="Preserved for historical auditability.",
        ),
        "diagnose": CliRouteEntry(
            route="diagnose",
            implementation="runtime.foundation.intelligence.analyze (change+blast+risk+repair)",
            owning_capability="(superseded by discover.blast-radius + diagnose.failure-attribution)",
            verification_profile=None,
            evidence_kind="diagnostic_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="LEGACY_SUPERSEDED",
            derivation_source=(
                "M52.3: C42 composite diagnostic (analyze on changed files). "
                "Superseded by C50 blast-radius (change impact) + C42.30 diagnose-failures (failure attribution)."
            ),
            notes="Preserved; use discover.blast-radius for change impact.",
        ),
        "intelligence-audit": CliRouteEntry(
            route="intelligence-audit",
            implementation="runtime.foundation.intelligence.platform.migration",
            owning_capability="(superseded by C42.38 certification)",
            verification_profile=None,
            evidence_kind="migration_report",
            executable=True,
            diagnostic=False,
            strengthening_related=False,
            alias_of=None,
            classification="LEGACY_SUPERSEDED",
            derivation_source=(
                "M52.3: Program 14.1 migration artifact generation. "
                "Superseded by C42.38/C48 certification architecture."
            ),
            notes="Preserved for historical auditability.",
        ),
        "repair": CliRouteEntry(
            route="repair",
            implementation="runtime.foundation.intelligence.repair_plan",
            owning_capability="(superseded by diagnose.failure-attribution + strengthening)",
            verification_profile=None,
            evidence_kind="diagnostic_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="LEGACY_SUPERSEDED",
            derivation_source=(
                "M52.3: C42 legacy repair planning. "
                "Superseded by C42.30 failure-attribution + C48 strengthening pipeline."
            ),
            notes="Preserved; use diagnose.failure-attribution + strengthen-capability.",
        ),
        "risk": CliRouteEntry(
            route="risk",
            implementation="runtime.foundation.intelligence.engineering_risk",
            owning_capability="(superseded by discover.blast-radius escalation)",
            verification_profile=None,
            evidence_kind="diagnostic_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="LEGACY_SUPERSEDED",
            derivation_source=(
                "M52.3: C42 legacy risk analysis. "
                "Superseded by C50 blast-radius escalation conditions."
            ),
            notes="Preserved; use discover.blast-radius for escalation.",
        ),
    }
    if route in legacy:
        return legacy[route]

    # ---- 4 OPERATIONAL_OBSERVABILITY (outside verification scope) ----
    observ = {
        "analytics": CliRouteEntry(
            route="analytics",
            implementation="runtime.system.observability.analytics",
            owning_capability="(outside verification scope)",
            verification_profile=None,
            evidence_kind="analytics_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="OPERATIONAL_OBSERVABILITY",
            derivation_source=(
                "M52.3: runtime.system.observability.analytics. Engineering health "
                "analytics — not a verification capability. Control plane does not gate it."
            ),
            notes="Safe: no impact on certification.",
        ),
        "ci-doctor": CliRouteEntry(
            route="ci-doctor",
            implementation=".github/scripts/validate_actions.py",
            owning_capability="(outside verification scope)",
            verification_profile=None,
            evidence_kind="ci_validation_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="OPERATIONAL_OBSERVABILITY",
            derivation_source=(
                "M52.3: GitHub Actions workflow validation tooling. "
                "Operational CI diagnostic; canonical workflow authority is CI evidence."
            ),
            notes="Safe: no impact on certification.",
        ),
        "dashboard": CliRouteEntry(
            route="dashboard",
            implementation="runtime.system.observability.dashboard",
            owning_capability="(outside verification scope)",
            verification_profile=None,
            evidence_kind="dashboard_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="OPERATIONAL_OBSERVABILITY",
            derivation_source=(
                "M52.3: runtime.system.observability.dashboard. Engineering health "
                "dashboard — not a verification capability. Control plane does not gate it."
            ),
            notes="Safe: no impact on certification.",
        ),
        "health": CliRouteEntry(
            route="health",
            implementation="runtime.system.observability.health_report",
            owning_capability="(outside verification scope)",
            verification_profile=None,
            evidence_kind="health_report",
            executable=True,
            diagnostic=True,
            strengthening_related=False,
            alias_of=None,
            classification="OPERATIONAL_OBSERVABILITY",
            derivation_source=(
                "M52.3: runtime.system.observability.health_report. Engineering health "
                "report — not a verification capability. Control plane does not gate it."
            ),
            notes="Safe: no impact on certification.",
        ),
    }
    if route in observ:
        return observ[route]

    # ---- Catalog-owned routes (should have catalog_claim) ----
    if catalog_claim:
        return CliRouteEntry(
            route=route,
            implementation=impl,
            owning_capability=catalog_claim,
            verification_profile=None,
            evidence_kind="catalog",
            executable=True,
            diagnostic=(catalog_claim.startswith("diagnose.")),
            strengthening_related=(catalog_claim.startswith("strengthen.")),
            alias_of=None,
            classification="CATALOG_OWNED",
            derivation_source=f"Catalog entry: {catalog_claim}",
            notes="",
        )

    # Fallback: unknown (should not happen)
    return CliRouteEntry(
        route=route,
        implementation=impl,
        owning_capability="UNCLASSIFIED",
        verification_profile=None,
        evidence_kind="unknown",
        executable=False,
        diagnostic=False,
        strengthening_related=False,
        alias_of=None,
        classification="UNCLASSIFIED",
        derivation_source="No classification found",
        notes="BUG: route slipped through classification",
    )


def build_cli_capability_matrix() -> dict[str, Any]:
    """Build the complete CLI capability matrix."""
    impls = _route_implementations()
    claims = _catalog_claims()

    routes = sorted(impls.keys())
    entries = []
    for r in routes:
        entry = _classify_route(r, impls[r], claims.get(r))
        entries.append(asdict(entry))

    # Statistics
    stats = {}
    for e in entries:
        c = e["classification"]
        stats[c] = stats.get(c, 0) + 1

    return {
        "schema": "m9-c52-cli-capability-matrix/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "total_routes": len(routes),
        "statistics": stats,
        "entries": entries,
    }


def main() -> int:
    matrix = build_cli_capability_matrix()
    out = (
        REPO_ROOT
        / "runtime"
        / "generated"
        / "m9-c52"
        / "m9-c52-cli-capability-matrix.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(matrix, indent=2))
    print(f"routes={matrix['total_routes']} stats={matrix['statistics']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
