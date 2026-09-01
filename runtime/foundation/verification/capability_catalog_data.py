# runtime/foundation/verification/capability_catalog_data.py
#
# M9-C51 — Canonical capability inventory data table.
#
# One _Registration row per real capability. Derived from inspecting the
# implementation that realizes it — not from prose documentation.
# Ordering: lifecycle stage (discovery → certification), then alphabetical.
# Total entries: ~70. This file is DATA only; it is imported by the
# CapabilityCatalogBuilder in capability_catalog.py.

from __future__ import annotations

from runtime.foundation.verification.capability_catalog import (
    PROBLEM_CHANGED_FILE,
    PROBLEM_COVERAGE_DROP,
    PROBLEM_MUTATION_SURVIVOR,
    PROBLEM_PROPOSED_CHANGE,
    PROBLEM_QUALITY_FAILURE,
    PROBLEM_STALE_EVIDENCE,
    PROBLEM_TEST_FAILURE,
    PROBLEM_UNKNOWN_FAILURE,
    PROBLEM_WORKFLOW_FAILURE,
    AuthorizationLevel,
    CapabilityStage,
    _Registration,
)
from runtime.foundation.verification.command_inventory import CommandCategory

_ROOT_PYPROJECT = "pyproject.toml"
_BACKEND_PYPROJECT = "backend/pyproject.toml"
_VERIFICATION_YAML = "runtime/foundation/verification/verification.yaml"


def _reg(**kwargs) -> _Registration:
    """Compact constructor for a registration row."""
    return _Registration(**kwargs)


# ── DISCOVERY ──────────────────────────────────────────────────────────────

_REGISTRATIONS_DISCOVERY = [
    _reg(
        capability_id="discover.capability-for",
        name="Capability-For (problem -> capability resolver)",
        stage=CapabilityStage.DISCOVERY,
        purpose=(
            "Given a structured problem (changed file, test failure, "
            "mutation survivor, coverage drop, workflow/quality failure, "
            "proposed change, stale evidence, unknown failure), "
            "deterministically resolve the existing canonical capability, "
            "its exact command, prerequisites, expected evidence, and "
            "the next capability to invoke."
        ),
        command=(
            "python runtime/verify.py capability-for --type <problem> "
            "[--changed FILE] [--test PATH] [--survivor ID] "
            "[--capability ID] [--engine NAME] [--scope SCOPE] "
            "[--workflow ID] [--record PATH] [--error TEXT] "
            "[--json] [--out PATH]"
        ),
        implementation="runtime.foundation.verification.capability_discovery:cmd_capability_for",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(
            PROBLEM_CHANGED_FILE,
            PROBLEM_TEST_FAILURE,
            PROBLEM_MUTATION_SURVIVOR,
            PROBLEM_COVERAGE_DROP,
            PROBLEM_WORKFLOW_FAILURE,
            PROBLEM_QUALITY_FAILURE,
            PROBLEM_PROPOSED_CHANGE,
            PROBLEM_STALE_EVIDENCE,
            PROBLEM_UNKNOWN_FAILURE,
        ),
        produces=("capability_resolution", "blast_radius_contract"),
        consumes=("environment_fingerprint",),
        evidence_type="capability_resolution",
        authorization=AuthorizationLevel.NONE,
        preconditions=(),
        related_capabilities=("discover.blast-radius", "plan.execution-plan"),
        notes=(
            "Canonical operator entry point for 'what should I run?'. "
            "Refuses to silently fall back to a traditional/manual path; "
            "unknown failures escalate explicitly."
        ),
    ),
    _reg(
        capability_id="discover.blast-radius",
        name="Blast-Radius Contract (C50)",
        stage=CapabilityStage.DISCOVERY,
        purpose=(
            "Compute the canonical deterministic blast-radius contract "
            "for changed files: affected capabilities/components, "
            "verification surfaces, evidence invalidation, minimum safe "
            "scope, escalation conditions, fail-closed status."
        ),
        command=(
            "python runtime/verify.py blast-radius "
            "[--files FILE...] [--base REF] [--head REF] [--json] [--out PATH]"
        ),
        implementation="runtime.foundation.verification.blast_radius:compute_blast_radius",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_CHANGED_FILE, PROBLEM_PROPOSED_CHANGE),
        input_types=("changed_files",),
        input_sources=("explicit_argument", "git_working_tree"),
        produces=("blast_radius_contract", "evidence_invalidations"),
        consumes=("environment_fingerprint",),
        evidence_type="blast_radius_contract",
        configuration_authority=(_VERIFICATION_YAML, _ROOT_PYPROJECT),
        notes=(
            "C50 certified. The single canonical representation of change "
            "impact; every other planning capability consumes it rather "
            "than recomputing impact independently."
        ),
    ),
    _reg(
        capability_id="discover.resolve-capabilities",
        name="Capability Resolution (C48)",
        stage=CapabilityStage.DISCOVERY,
        purpose=(
            "Resolve changed files to directly/transitively affected "
            "capabilities, invalidated vs reusable evidence, and mandatory "
            "vs optional verification."
        ),
        command="python runtime/verify.py resolve-capabilities FILE... [--json] [--out PATH]",
        implementation="runtime.foundation.verification.operational_cli:cmd_resolve_capabilities",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_CHANGED_FILE, PROBLEM_PROPOSED_CHANGE),
        input_types=("changed_files",),
        input_sources=("explicit_argument", "git_working_tree"),
        produces=("capability_resolution", "evidence_invalidations"),
        consumes=("environment_fingerprint",),
        evidence_type="capability_resolution",
    ),
    _reg(
        capability_id="discover.capability-inventory",
        name="Command Inventory (C48)",
        stage=CapabilityStage.DISCOVERY,
        purpose=(
            "Return the machine-readable command/capability inventory: "
            "command, purpose, prerequisites, evidence produced/consumed, "
            "failure semantics, escalation behavior, certifiability."
        ),
        command=(
            "python runtime/verify.py "
            "capability-inventory [--capability X] [--profile X] [--category X] [--json] | "
            "capabilities [--stage X] [--json]"
        ),
        implementation="runtime.foundation.verification.operational_cli:cmd_capability_inventory",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_CHANGED_FILE,),
        produces=("capability_catalog",),
        consumes=(),
        evidence_type="capability_catalog",
    ),
    _reg(
        capability_id="discover.what-should-i-run",
        name="What-Should-I-Run (C50)",
        stage=CapabilityStage.DISCOVERY,
        purpose=(
            "Answer 'what should I run?' given a set of changed files: "
            "minimum safe verification scope and escalation conditions."
        ),
        command="python runtime/verify.py what-should-i-run [--files FILE...] [--json]",
        implementation="runtime.foundation.verification.blast_radius_cli:cmd_what_should_i_run_c50",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_CHANGED_FILE, PROBLEM_PROPOSED_CHANGE),
        input_types=("changed_files",),
        input_sources=("explicit_argument", "git_working_tree"),
        produces=("blast_radius_contract",),
        consumes=("environment_fingerprint",),
        evidence_type="blast_radius_contract",
    ),
    # M9-C52.3 — C51 control-plane routes added to the catalog (were in code,
    # absent from catalog). One _row per real executable surface.
    _reg(
        capability_id="discover.capability-graph",
        name="Capability Dependency Graph (C51)",
        stage=CapabilityStage.DISCOVERY,
        purpose=(
            "Render the machine-readable capability dependency graph "
            "(44 nodes, edges) used for blast-radius propagation and "
            "cross-capability impact analysis."
        ),
        command="python runtime/verify.py capability-graph [--json] [--out PATH]",
        implementation=(
            "runtime.foundation.verification.capability_graph:cmd_capability_graph"
        ),
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_CHANGED_FILE,),
        input_types=("none",),
        input_sources=("generated_evidence",),
        produces=("capability_graph",),
        consumes=("capability_catalog",),
        evidence_type="capability_graph",
        related_capabilities=(
            "discover.blast-radius",
            "discover.resolve-capabilities",
        ),
        notes=(
            "C52.3: closed the in-code-absent-from-catalog gap. Graph is "
            "derived from the catalog; no second capability taxonomy is created."
        ),
    ),
    _reg(
        capability_id="discover.latent-capability-audit",
        name="Latent Capability Audit (C51)",
        stage=CapabilityStage.DISCOVERY,
        purpose=(
            "Audit for latent (registered/implemented but not fully "
            "operationalized) verification capabilities. Classifies them; "
            "never deletes them."
        ),
        command="python runtime/verify.py latent-audit [--json] [--out PATH]",
        implementation=(
            "runtime.foundation.verification.capability_latent_audit:"
            "cmd_latent_audit"
        ),
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_PROPOSED_CHANGE,),
        input_types=("none",),
        input_sources=("generated_evidence",),
        produces=("latent_capability_audit",),
        consumes=("capability_catalog",),
        evidence_type="latent_capability_audit",
        notes=(
            "C52.3: closed the in-code-absent-from-catalog gap. Latent "
            "capabilities are classified, not removed."
        ),
    ),
]

# ── PLANNING ───────────────────────────────────────────────────────────────

_REGISTRATIONS_PLANNING = [
    _reg(
        capability_id="plan.control-plane",
        name="Control-Plane Plan (C48)",
        stage=CapabilityStage.PLANNING,
        purpose=(
            "Build the minimum defensible verification plan (mandatory, "
            "escalation, measurement and certification requirements) from a "
            "capability resolution."
        ),
        command="python runtime/verify.py control-plane-plan FILE... [--json] [--out PATH]",
        implementation="runtime.foundation.verification.operational_cli:cmd_control_plane_plan",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_CHANGED_FILE, PROBLEM_PROPOSED_CHANGE),
        input_types=("changed_files",),
        input_sources=("explicit_argument", "git_working_tree"),
        produces=("control_plane_plan",),
        consumes=("capability_resolution",),
        evidence_type="control_plane_plan",
        preconditions=("discover.resolve-capabilities",),
        related_capabilities=("plan.execution-plan",),
    ),
    _reg(
        capability_id="plan.tier-plan",
        name="Tier-Aware Plan (VEA-5)",
        stage=CapabilityStage.PLANNING,
        purpose=(
            "Emit the tier-aware (local/pr/deep) verification plan manifest "
            "that the CI reconciliation gate validates."
        ),
        command="python runtime/verify.py plan --tier <local|pr|deep> [--base REF] [--changed FILE...]",
        implementation="runtime/verify.py:cmd_plan",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_CHANGED_FILE, PROBLEM_PROPOSED_CHANGE),
        input_types=("changed_files",),
        input_sources=("explicit_argument", "git_range"),
        produces=("tier_plan_manifest",),
        consumes=(),
        evidence_type="tier_plan_manifest",
        configuration_authority=(_VERIFICATION_YAML,),
    ),
    _reg(
        capability_id="plan.execution-plan",
        name="Execution Plan (C49)",
        stage=CapabilityStage.PLANNING,
        purpose=(
            "Turn a change (or the C50 blast-radius answer) into an "
            "executable, observable, deterministic C49 ExecutionPlan of "
            "ordered verification tasks."
        ),
        command="python runtime/verify.py execution-plan FILE... [--json] [--out PATH]",
        implementation="runtime.foundation.verification.execution_orchestrator:ExecutionOrchestrator.build_execution_plan",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_CHANGED_FILE, PROBLEM_PROPOSED_CHANGE),
        input_types=("changed_files",),
        input_sources=("explicit_argument", "git_working_tree"),
        produces=("execution_plan",),
        consumes=("blast_radius_contract", "control_plane_plan"),
        evidence_type="execution_plan",
        preconditions=("discover.blast-radius", "plan.control-plane"),
        related_capabilities=("exec.orchestrator",),
    ),
    _reg(
        capability_id="plan.local-gate",
        name="Local Gate (pre-push)",
        stage=CapabilityStage.PLANNING,
        purpose=(
            "Developer-side LOCAL plan artifact (pre-push closure): emits "
            "the LOCAL TierPlan manifest from the working-tree delta."
        ),
        command="python runtime/verify.py local-gate [--out PATH]",
        implementation="runtime/verify.py:cmd_local_gate",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_CHANGED_FILE,),
        input_types=("changed_files",),
        input_sources=("git_working_tree",),
        produces=("tier_plan_manifest",),
        consumes=(),
        evidence_type="tier_plan_manifest",
    ),
    _reg(
        capability_id="plan.deep-contract",
        name="Deep Contract Manifest",
        stage=CapabilityStage.PLANNING,
        purpose=(
            "Emit the machine-readable DEEP ownership contract: the "
            "explicit categorization of functional/regression/test-"
            "effectiveness/UI/performance/security surfaces."
        ),
        command="python runtime/verify.py deep-contract [--out PATH]",
        implementation="runtime/verify.py:cmd_deep_contract",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(),
        produces=("certification_report",),
        consumes=(),
        evidence_type="certification_report",
    ),
]

# Aggregate all registrations so far.
REGISTRATIONS = list(_REGISTRATIONS_DISCOVERY) + list(_REGISTRATIONS_PLANNING)

# ── EXECUTION (profiles are auto-derived; these are the hand-registered items) ─

_REGISTRATIONS_EXECUTION = [
    _reg(
        capability_id="exec.orchestrator",
        name="Execution Orchestrator (C49)",
        stage=CapabilityStage.EXECUTION,
        purpose=(
            "Execute a C49 ExecutionPlan, observe every task, reuse valid "
            "evidence, stop at deterministic stop rules, and return a final "
            "certifiable/not-certifiable decision."
        ),
        command="python runtime/verify.py execute FILE... [--json] [--out PATH]",
        implementation="runtime.foundation.verification.execution_orchestrator:ExecutionOrchestrator.execute",
        category=CommandCategory.QUALITY_GATE,
        trigger_conditions=(PROBLEM_CHANGED_FILE,),
        input_types=("changed_files", "plan_id"),
        input_sources=("explicit_argument", "git_working_tree", "generated_evidence"),
        produces=("execution_report", "evidence_invalidations"),
        consumes=("execution_plan", "tier_plan_manifest"),
        evidence_type="execution_report",
        authorization=AuthorizationLevel.OPERATOR,
        preconditions=("plan.execution-plan",),
        notes=(
            "Reuses C47 measurement truth and C45 durable survivor intel; "
            "never treats transient mutmut workspaces as evidence."
        ),
    ),
    _reg(
        capability_id="evidence.pipeline-plan",
        name="Evidence Plan Pipeline (C42)",
        stage=CapabilityStage.EXECUTION,
        purpose=(
            "Plan backend evidence through the existing C42.28-C42.31 "
            "evidence-aware pipeline."
        ),
        command="python runtime/verify.py evidence-plan",
        implementation="runtime.foundation.verification.executor_pipeline:main",
        category=CommandCategory.QUALITY_GATE,
        trigger_conditions=(PROBLEM_CHANGED_FILE,),
        input_types=("changed_files",),
        input_sources=("git_working_tree",),
        produces=("execution_report", "evidence_invalidations"),
        consumes=("capability_resolution",),
        evidence_type="execution_report",
        authorization=AuthorizationLevel.OPERATOR,
        related_capabilities=("exec.orchestrator",),
        profile_name="evidence-plan",
    ),
    # M9-C52.3 — C42.28 evidence-pipeline execution routes + env-check, which
    # were in code but absent from the catalog.
    _reg(
        capability_id="exec.evidence-execute",
        name="Evidence Pipeline Execute (C42.28)",
        stage=CapabilityStage.EXECUTION,
        purpose=(
            "Execute the C42.28 evidence-aware pipeline plan and run the "
            "matched units, including the targeted mutation scope, capturing "
            "per-unit execution evidence."
        ),
        command="python runtime/verify.py evidence-execute [--run-mutation]",
        implementation="runtime.foundation.verification.executor_pipeline:main",
        category=CommandCategory.QUALITY_GATE,
        trigger_conditions=(PROBLEM_CHANGED_FILE,),
        input_types=("changed_files",),
        input_sources=("git_working_tree",),
        produces=("execution_report", "execution_evidence"),
        consumes=("capability_resolution",),
        evidence_type="execution_evidence",
        authorization=AuthorizationLevel.OPERATOR,
        related_capabilities=(
            "evidence.pipeline-plan",
            "evidence.reconcile-pipeline",
            "certify.evidence-pipeline",
        ),
        notes="C52.3: closed the in-code-absent-from-catalog gap.",
    ),
    _reg(
        capability_id="exec.execution-evidence",
        name="Execution Evidence Emission (VEA-5 M5-C)",
        stage=CapabilityStage.EXECUTION,
        purpose=(
            "Emit the persisted execution-evidence artifact "
            "(unit_id -> attempt -> artifact) from the plan manifest and "
            "recorded outcomes."
        ),
        command="python runtime/verify.py exec-evidence",
        implementation="runtime/verify.py:cmd_exec_evidence",
        category=CommandCategory.RECONCILIATION,
        trigger_conditions=(PROBLEM_CHANGED_FILE,),
        input_types=("plan_manifest", "recorded_outcome"),
        input_sources=("generated_evidence",),
        produces=("execution_evidence",),
        consumes=("execution_plan",),
        evidence_type="execution_evidence",
        notes="C52.3: closed the in-code-absent-from-catalog gap.",
    ),
    _reg(
        capability_id="exec.environment-check",
        name="Canonical Environment Check (C42.5)",
        stage=CapabilityStage.EXECUTION,
        purpose=(
            "Verify the canonical repository .venv environment and emit a "
            "machine-readable fingerprint; fail-closed if the sanctioned "
            "environment is missing or drifted."
        ),
        command="python runtime/verify.py env-check",
        implementation="runtime.foundation.verification.env:main_env_check",
        category=CommandCategory.QUALITY_GATE,
        trigger_conditions=(PROBLEM_QUALITY_FAILURE, PROBLEM_WORKFLOW_FAILURE),
        input_types=("none",),
        input_sources=("filesystem",),
        produces=("environment_fingerprint",),
        consumes=(),
        evidence_type="environment_fingerprint",
        notes=(
            "C52.3: closed the in-code-absent-from-catalog gap. The "
            "environment fingerprint is a precondition consumed by "
            "blast-radius and configuration-authority."
        ),
    ),
]

# Extend the aggregate list with execution rows.
REGISTRATIONS.extend(_REGISTRATIONS_EXECUTION)
del _REGISTRATIONS_DISCOVERY, _REGISTRATIONS_PLANNING, _REGISTRATIONS_EXECUTION

# ── MEASUREMENT (C47) ───────────────────────────────────────────────────────

_REGISTRATIONS_MEASUREMENT = [
    _reg(
        capability_id="measure.mutation",
        name="Mutation Testing (C47 authoritative)",
        stage=CapabilityStage.MEASUREMENT,
        purpose=(
            "Run the canonical mutation measurement (full campaign, bounded "
            "smoke, or targeted engine) and persist an authoritative "
            "measurement-truth record plus durable survivor intel."
        ),
        command=(
            "python runtime/verify.py mutation "
            "[--smoke | --target <engine>] [--restore] [--json]"
        ),
        implementation="runtime.foundation.verification.mutation_runner:run_mutation_cli",
        category=CommandCategory.MUTATION_TEST,
        trigger_conditions=(PROBLEM_MUTATION_SURVIVOR,),
        input_types=("engine", "scope"),
        input_sources=("explicit_argument",),
        produces=("mutation_score", "survivor_intel"),
        consumes=("environment_fingerprint",),
        evidence_type="mutation_score",
        measurement_kind="mutation",
        authorization=AuthorizationLevel.HUMAN,
        configuration_authority=(_BACKEND_PYPROJECT, _ROOT_PYPROJECT),
        notes=(
            "Subordinate MEASUREMENT capability: full campaigns require "
            "explicit human authorization and are a CI escalation, never the "
            "default. Smoke/target modes are bounded. Mutates the repository "
            "temporarily; --restore reverts."
        ),
    ),
    _reg(
        capability_id="measure.mutation-inventory",
        name="Mutation Population Inventory",
        stage=CapabilityStage.MEASUREMENT,
        purpose=(
            "Inventory the certified mutation population per engine and "
            "report mutation-corpus completeness/certification state."
        ),
        command="python runtime/verify.py mutation-inventory [--json]",
        implementation="runtime.foundation.verification.mutation_inventory:run_mutation_inventory_cli",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_MUTATION_SURVIVOR,),
        input_types=("scope",),
        input_sources=("filesystem",),
        produces=("capability_catalog",),
        consumes=("mutation_score",),
        evidence_type="capability_catalog",
        measurement_kind="mutation",
    ),
    _reg(
        capability_id="measure.coverage",
        name="Coverage Measurement (C47 canonical)",
        stage=CapabilityStage.MEASUREMENT,
        purpose=(
            "Produce an authoritative, durable, machine-readable "
            "measurement-truth record for coverage over a scope. The only "
            "canonical coverage path; raw `coverage run` is non-canonical."
        ),
        command="python runtime/verify.py measurement coverage <SCOPE> [--json]",
        implementation="runtime.foundation.verification.coverage_measurement:measure_coverage_cli",
        category=CommandCategory.COVERAGE_MEASUREMENT,
        trigger_conditions=(PROBLEM_COVERAGE_DROP, PROBLEM_STALE_EVIDENCE),
        input_types=("scope",),
        input_sources=("explicit_argument",),
        produces=("coverage_measurement",),
        consumes=("environment_fingerprint",),
        evidence_type="coverage_measurement",
        measurement_kind="coverage",
        configuration_authority=(_BACKEND_PYPROJECT, _ROOT_PYPROJECT),
        notes=(
            "A coverage drop or stale-coverage problem MUST route here "
            "first so a fresh authoritative truth record exists before any "
            "reuse or certification decision."
        ),
    ),
    _reg(
        capability_id="measure.truth-report",
        name="Measurement Truth Report (C47/C48)",
        stage=CapabilityStage.MEASUREMENT,
        purpose=(
            "Evaluate measurement truth across ALL capabilities and report "
            "which are authoritative-complete vs partial/derived — the gate "
            "that blocks certification from derived/incomplete evidence."
        ),
        command="python runtime/verify.py measurement-truth-report",
        implementation="runtime.foundation.verification.measurement_truth_integration:get_measurement_truth_integrator",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(
            PROBLEM_COVERAGE_DROP,
            PROBLEM_STALE_EVIDENCE,
            PROBLEM_MUTATION_SURVIVOR,
        ),
        input_types=("none",),
        input_sources=("generated_evidence",),
        produces=("certification_report",),
        consumes=("coverage_measurement", "mutation_score"),
        evidence_type="certification_report",
        measurement_kind="coverage",
    ),
]

REGISTRATIONS.extend(_REGISTRATIONS_MEASUREMENT)
del _REGISTRATIONS_MEASUREMENT

# ── DIAGNOSIS ───────────────────────────────────────────────────────────────

_REGISTRATIONS_DIAGNOSIS = [
    _reg(
        capability_id="diagnose.failure-attribution",
        name="Pipeline Failure Attribution (VEA-2 M6)",
        stage=CapabilityStage.DIAGNOSIS,
        purpose=(
            "Attribute real pipeline failures to the changed-file blast "
            "radius from M5 evidence (unit_id already joined), never by "
            "manual log parsing."
        ),
        command="python runtime/verify.py diagnose-failures",
        implementation="runtime/verify.py:cmd_diagnose_failures",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_WORKFLOW_FAILURE, PROBLEM_UNKNOWN_FAILURE),
        input_types=("none",),
        input_sources=("generated_evidence", "git_working_tree"),
        produces=("diagnostic_report",),
        consumes=("capability_resolution", "execution_report"),
        evidence_type="diagnostic_report",
        related_capabilities=("diagnose.forensic",),
    ),
    _reg(
        capability_id="diagnose.intelligence",
        name="Engineering Intelligence Layer",
        stage=CapabilityStage.DIAGNOSIS,
        purpose=(
            "Run the complete engineering intelligence layer: change "
            "analysis, blast radius, risk, and verification planning "
            "across all layers (backend, frontend, contracts, property)."
        ),
        command="python runtime/verify.py intelligence [--logs] [--no-ci]",
        implementation="runtime/verify.py:cmd_intelligence",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_CHANGED_FILE,),
        input_types=("changed_files",),
        input_sources=("git_working_tree",),
        produces=("diagnostic_report", "blast_radius_contract"),
        consumes=("environment_fingerprint",),
        evidence_type="diagnostic_report",
    ),
    # M9-C52.3 — C51 bypass-audit route (was in code, absent from catalog).
    _reg(
        capability_id="diagnose.bypass-audit",
        name="Control-Plane Bypass Audit (C51)",
        stage=CapabilityStage.DIAGNOSIS,
        purpose=(
            "Deterministically classify candidate invocation paths "
            "(problem + action) as CANONICAL_PATH / SUBOPTIMAL_PATH / "
            "UNSAFE_BYPASS / NO_CANONICAL_CAPABILITY, so the certification "
            "path can never silently use a bypass."
        ),
        command="python runtime/verify.py bypass-audit [--json] [--out PATH]",
        implementation=(
            "runtime.foundation.verification.capability_discovery:" "cmd_bypass_audit"
        ),
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_UNKNOWN_FAILURE,),
        input_types=("none",),
        input_sources=("generated_evidence",),
        produces=("bypass_risk_analysis",),
        consumes=("capability_catalog",),
        evidence_type="bypass_risk_analysis",
        related_capabilities=("discover.capability-for",),
        notes=(
            "C52.3: closed the in-code-absent-from-catalog gap. Feeds "
            "M52.6 bypass-enforcement."
        ),
    ),
]

REGISTRATIONS.extend(_REGISTRATIONS_DIAGNOSIS)
del _REGISTRATIONS_DIAGNOSIS

# ── STRENGTHENING ───────────────────────────────────────────────────────────

_REGISTRATIONS_STRENGTHENING = [
    _reg(
        capability_id="strengthen.survivor-intel",
        name="Durable Survivor Intelligence (C45)",
        stage=CapabilityStage.STRENGTHENING,
        purpose=(
            "Load and query the durable mutation-survivor intelligence "
            "record: per-survivor classification (A-E), capability "
            "attribution, covering tests, and prior investigation status."
        ),
        command="python runtime/verify.py mutation-intel [SURVIVOR_ID] [--json]",
        implementation="runtime.foundation.verification.survivor_intel:run_intel_cli",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_MUTATION_SURVIVOR,),
        input_types=("survivor_id",),
        input_sources=("durable_intel_store",),
        produces=("survivor_intel",),
        consumes=("mutation_score",),
        evidence_type="survivor_intel",
        measurement_kind="mutation",
        notes=(
            "A surviving mutant must be classified from this durable record "
            "before writing any test; it encodes whether the survivor is a "
            "true gap or an equivalent/uncertain mutant."
        ),
    ),
    _reg(
        capability_id="strengthen.capability-pipeline",
        name="Capability-Aware Strengthening Pipeline (C48)",
        stage=CapabilityStage.STRENGTHENING,
        purpose=(
            "Discover capability survivors, classify each, propose "
            "behavioral assertions, gate on human authorization, validate "
            "proposals against mutants, and record durable decisions."
        ),
        command=(
            "python runtime/verify.py "
            "strengthen-capability <CAPABILITY_ID> [--max-survivors N] [--json] | "
            "strengthen-survivor <SURVIVOR_ID> [--json] [--out PATH]"
        ),
        implementation="runtime.foundation.verification.strengthening_pipeline:cmd_strengthen_capability",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_MUTATION_SURVIVOR,),
        input_types=("capability_id",),
        input_sources=("durable_intel_store",),
        produces=("strengthening_proposal", "survivor_intel"),
        consumes=("survivor_intel", "mutation_score"),
        evidence_type="strengthening_proposal",
        authorization=AuthorizationLevel.HUMAN,
        preconditions=("strengthen.survivor-intel",),
        related_capabilities=("strengthen.forensic", "measure.mutation"),
        notes=(
            "The canonical survivor->strengthening route. Produces "
            "authorization-gated proposals with target test + proposed "
            "assertion, then targeted revalidation via measure.mutation."
        ),
    ),
    _reg(
        capability_id="strengthen.forensic",
        name="Forensic Diagnostic Lab (C42.30)",
        stage=CapabilityStage.STRENGTHENING,
        purpose=(
            "Forensic diagnosis and strengthening analysis of mutation "
            "survivors: discover, classify, propose, and validate per "
            "engine through the forensic CLI."
        ),
        command=(
            "python runtime/verify.py forensic-diagnose <ENGINE> | "
            "forensic-report | strengthen-discover <ENGINE> | "
            "strengthen-propose <ENGINE> | strengthen-validate <ENGINE> | "
            "strengthen-survivor-forensic <SURVIVOR_ID> [--json] | "
            "strengthen-analyze <ENGINE> | strengthen-report"
        ),
        implementation="runtime.foundation.verification.forensic_cli:run_forensic_diagnose",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_MUTATION_SURVIVOR,),
        input_types=("engine", "survivor_id"),
        input_sources=("durable_intel_store", "explicit_argument"),
        produces=("forensic_report", "strengthening_proposal"),
        consumes=("survivor_intel",),
        evidence_type="forensic_report",
        authorization=AuthorizationLevel.HUMAN,
        preconditions=("strengthen.survivor-intel",),
        related_capabilities=("strengthen.capability-pipeline",),
        notes=(
            "Low-level forensic lab (C42.30). strengthen-survivor-forensic "
            "uses mutmut built-ins (show / tests-for-mutant) and REQUIRES a "
            "live mutation run; it is an explicit developer/diagnostic escape, "
            "not the canonical route (M9-C52.2). Canonical per-survivor route "
            "is `strengthen-survivor` (strengthen.capability-pipeline)."
        ),
    ),
]

REGISTRATIONS.extend(_REGISTRATIONS_STRENGTHENING)
del _REGISTRATIONS_STRENGTHENING

# ── QUALITY (M51.7 — repository-root config authority) ─────────────────────

_REGISTRATIONS_QUALITY = [
    _reg(
        capability_id="quality.ruff",
        name="Ruff Lint (repository-wide)",
        stage=CapabilityStage.EXECUTION,
        purpose=(
            "Lint the repository with the canonical Ruff configuration. "
            "The repository-root pyproject.toml [tool.ruff] is the single "
            "authority; it is NOT scoped to backend/src."
        ),
        command="python -m ruff check . --output-format=github",
        implementation=".github/scripts/run_fast_checks.sh::ruff",
        category=CommandCategory.STATIC_ANALYSIS,
        trigger_conditions=(PROBLEM_QUALITY_FAILURE,),
        input_types=("repository",),
        input_sources=("filesystem",),
        produces=("lint_report",),
        consumes=(),
        evidence_type="lint_report",
        configuration_authority=(_ROOT_PYPROJECT,),
        notes=(
            "Canonical quality path for Ruff failures. Runs at repository "
            "root over the whole tree (runtime + backend + scripts), "
            "governed by the root pyproject.toml. Do not assume "
            "backend/src is the repository-wide source scope."
        ),
    ),
    _reg(
        capability_id="quality.black",
        name="Black Format (repository-wide)",
        stage=CapabilityStage.EXECUTION,
        purpose=(
            "Check formatting with the canonical Black configuration. "
            "The repository-root pyproject.toml [tool.black] governs the "
            "whole tree, not backend/src."
        ),
        command="python -m black --check --diff .",
        implementation=".github/scripts/run_fast_checks.sh::black",
        category=CommandCategory.STATIC_ANALYSIS,
        trigger_conditions=(PROBLEM_QUALITY_FAILURE,),
        input_types=("repository",),
        input_sources=("filesystem",),
        produces=("format_report",),
        consumes=(),
        evidence_type="format_report",
        configuration_authority=(_ROOT_PYPROJECT,),
    ),
    _reg(
        capability_id="quality.mypy",
        name="Mypy Typecheck (scoped boundaries)",
        stage=CapabilityStage.EXECUTION,
        purpose=(
            "Typecheck with the canonical Mypy configuration. Two "
            "authoritative boundaries: repo-scope from root pyproject.toml "
            "[tool.mypy] (excludes backend/), and backend strict boundary "
            "from backend/pyproject.toml [tool.mypy] strict=true."
        ),
        command=(
            "python -m mypy .  # repo boundary;  python -m mypy src/  "
            "# backend strict boundary (rootdir=backend)"
        ),
        implementation=".github/scripts/run_fast_checks.sh::mypy",
        category=CommandCategory.STATIC_ANALYSIS,
        trigger_conditions=(PROBLEM_QUALITY_FAILURE,),
        input_types=("repository",),
        input_sources=("filesystem",),
        produces=("typecheck_report",),
        consumes=(),
        evidence_type="typecheck_report",
        configuration_authority=(_ROOT_PYPROJECT, _BACKEND_PYPROJECT),
        notes=(
            "The backend is its own STRICT typing boundary (rootdir="
            "backend, strict=true) gated by scripts/verify-fast.sh; the "
            "root mypy config deliberately excludes backend/ to avoid "
            "duplicate module identities. Do not conflate the two."
        ),
    ),
    _reg(
        capability_id="quality.pytest",
        name="Pytest (backend + runtime suites)",
        stage=CapabilityStage.EXECUTION,
        purpose=(
            "Run the canonical pytest suites. Backend unit/contract/"
            "property/invariant suites use backend/pyproject.toml "
            "[tool.pytest.ini_options]; runtime verification tests use the "
            "root [tool.pytest.ini_options]."
        ),
        command=(
            "python -m pytest tests/unit/ -x -q  # backend (rootdir=backend);  "
            "python -m pytest runtime/tests/  # runtime"
        ),
        implementation=".github/scripts/run_backend_verification.sh::pytest",
        category=CommandCategory.UNIT_TEST,
        trigger_conditions=(PROBLEM_TEST_FAILURE,),
        input_types=("test_path", "repository"),
        input_sources=("filesystem",),
        produces=("test_pass",),
        consumes=(),
        evidence_type="test_pass",
        configuration_authority=(_ROOT_PYPROJECT, _BACKEND_PYPROJECT),
    ),
]

REGISTRATIONS.extend(_REGISTRATIONS_QUALITY)
del _REGISTRATIONS_QUALITY

# ── CERTIFICATION ───────────────────────────────────────────────────────────

_REGISTRATIONS_CERTIFICATION = [
    _reg(
        capability_id="certify.contract-governance",
        name="Contract Governance Certification (C30)",
        stage=CapabilityStage.CERTIFICATION,
        purpose=(
            "Forensic certification that proves no reasonable future "
            "mutation can silently bypass the API contract gate. Covers "
            "exhaustive mutation surface inventory, semantic blind spots, "
            "authority policy, and CI enforcement."
        ),
        command="python runtime/verify.py contract-governance",
        implementation="runtime.foundation.verification.api_contracts.c30_certification:main",
        category=CommandCategory.CERTIFICATION,
        trigger_conditions=(PROBLEM_STALE_EVIDENCE,),
        input_types=("none",),
        input_sources=("generated_evidence",),
        produces=("certification_report",),
        consumes=("coverage_measurement", "mutation_score"),
        evidence_type="certification_report",
    ),
    _reg(
        capability_id="certify.api-contracts",
        name="API Contract Integrity Gate (C27)",
        stage=CapabilityStage.CERTIFICATION,
        purpose=(
            "Run the canonical api-contracts capability: STRUCTURAL "
            "freshness, GENERATED-type reproducibility, CONSUMER integrity, "
            "and WIRE validation. Emits machine-readable evidence and exits "
            "non-zero on drift."
        ),
        command="python runtime/verify.py api-contracts",
        implementation="runtime.foundation.verification.api_contracts.gate:ApiContractGate.run",
        category=CommandCategory.CONTRACT_TEST,
        trigger_conditions=(PROBLEM_CHANGED_FILE, PROBLEM_PROPOSED_CHANGE),
        input_types=("changed_files",),
        input_sources=("git_working_tree", "filesystem"),
        produces=("certification_report",),
        consumes=("environment_fingerprint",),
        evidence_type="certification_report",
        configuration_authority=(_VERIFICATION_YAML,),
    ),
    _reg(
        capability_id="certify.integrity",
        name="Architecture Integrity Verification",
        stage=CapabilityStage.CERTIFICATION,
        purpose=(
            "Evaluate repository architectural integrity rules against the "
            "current source tree. Detects architecture drift, ownership "
            "violations, and cross-layer boundary violations."
        ),
        command="python runtime/verify.py integrity",
        implementation="runtime.foundation.integrity.engine:evaluate_integrity",
        category=CommandCategory.ARCHITECTURAL,
        trigger_conditions=(PROBLEM_QUALITY_FAILURE, PROBLEM_UNKNOWN_FAILURE),
        input_types=("repository",),
        input_sources=("filesystem",),
        produces=("certification_report",),
        consumes=(),
        evidence_type="certification_report",
    ),
    _reg(
        capability_id="certify.audit",
        name="Engineering Platform Certification Audit",
        stage=CapabilityStage.CERTIFICATION,
        purpose=(
            "Run the complete engineering platform certification audit: "
            "repository analysis, cross-layer checks, dependency graph, "
            "planner, executor, evidence, observability, knowledge, "
            "workspace, integrity, GitHub Actions, runtime CLI, and ROI."
        ),
        command="python runtime/verify.py audit",
        implementation="runtime/verify.py:cmd_audit",
        category=CommandCategory.CERTIFICATION,
        trigger_conditions=(PROBLEM_UNKNOWN_FAILURE, PROBLEM_STALE_EVIDENCE),
        input_types=("repository",),
        input_sources=("filesystem",),
        produces=("certification_report",),
        consumes=(),
        evidence_type="certification_report",
    ),
    # M9-C52.3 — C42.28 evidence-pipeline certify route (was in code, absent from catalog).
    _reg(
        capability_id="certify.evidence-pipeline",
        name="Evidence Pipeline Certification (C42.28)",
        stage=CapabilityStage.CERTIFICATION,
        purpose=(
            "Execute the full evidence-pipeline (execute + reconcile) with "
            "targeted mutation scope and emit the final certification "
            "verdict. This is the canonical evidence-driven certification "
            "path."
        ),
        command="python runtime/verify.py evidence-certify",
        implementation="runtime.foundation.verification.executor_pipeline:main",
        category=CommandCategory.CERTIFICATION,
        trigger_conditions=(PROBLEM_CHANGED_FILE,),
        input_types=("changed_files",),
        input_sources=("git_working_tree",),
        produces=("certification_report",),
        consumes=("execution_evidence",),
        evidence_type="certification_report",
        related_capabilities=(
            "exec.evidence-execute",
            "evidence.reconcile-pipeline",
        ),
        notes="C52.3: closed the in-code-absent-from-catalog gap.",
    ),
]

REGISTRATIONS.extend(_REGISTRATIONS_CERTIFICATION)
del _REGISTRATIONS_CERTIFICATION

# ── EVIDENCE_INSPECTION ─────────────────────────────────────────────────────

_REGISTRATIONS_EVIDENCE = [
    _reg(
        capability_id="evidence.inspect-truth",
        name="Measurement Truth Inspection (C47)",
        stage=CapabilityStage.EVIDENCE_INSPECTION,
        purpose=(
            "Inspect a specific measurement-truth record: validate its "
            "classification, fingerprint, scope, and certifiability."
        ),
        command="python runtime/verify.py measurement-truth <RECORD_PATH> [--json]",
        implementation="runtime.foundation.verification.measurement_truth_cli:run_measurement_truth_cli",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_STALE_EVIDENCE,),
        input_types=("measurement_record_path",),
        input_sources=("generated_evidence",),
        produces=(),
        consumes=("coverage_measurement", "mutation_score"),
        evidence_type="certification_report",
    ),
    _reg(
        capability_id="evidence.execution-status",
        name="Execution Report Status",
        stage=CapabilityStage.EVIDENCE_INSPECTION,
        purpose=(
            "Look up an existing execution report by plan ID or show the "
            "latest report. Returns per-task status, duration, decisions."
        ),
        command=(
            "python runtime/verify.py "
            "execution-status [--plan PLAN] [--latest] [--json] | "
            "execution-report [--plan PLAN] [--latest] [--json]"
        ),
        implementation="runtime/verify.py:execution-status",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(),
        input_types=("plan_id",),
        input_sources=("generated_evidence",),
        produces=(),
        consumes=("execution_report",),
        evidence_type="execution_report",
    ),
    _reg(
        capability_id="evidence.workspace-status",
        name="Workspace Status & Metrics",
        stage=CapabilityStage.EVIDENCE_INSPECTION,
        purpose=(
            "Report current workspace state: test counts, recent history, "
            "dependency health, verification status, and metrics snapshots."
        ),
        command=(
            "python runtime/verify.py status | metrics | history | deps | "
            "verify-status"
        ),
        implementation="runtime.foundation.workspace.*",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(),
        input_types=("none",),
        input_sources=("filesystem",),
        produces=("environment_fingerprint",),
        consumes=(),
        evidence_type="environment_fingerprint",
    ),
    # M9-C52.3 — C51/C42.28 evidence-inspection routes (were in code, absent from catalog).
    _reg(
        capability_id="evidence.config-authority",
        name="Configuration Authority Verification (C51)",
        stage=CapabilityStage.EVIDENCE_INSPECTION,
        purpose=(
            "Validate the canonical configuration authority (pytest/ruff/black/"
            "mypy/mutmut/hypothesis/frontend/CI) against the repository state. "
            "Detects drift and ensures no tool silently uses non-canonical config."
        ),
        command="python runtime/verify.py config-authority [--validate] [--json] [--out PATH]",
        implementation=(
            "runtime.foundation.verification.configuration_authority:"
            "cmd_config_authority"
        ),
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_QUALITY_FAILURE,),
        input_types=("none",),
        input_sources=("filesystem",),
        produces=("configuration_authority_report",),
        consumes=(),
        evidence_type="configuration_authority_report",
        notes="C52.3: closed the in-code-absent-from-catalog gap.",
    ),
    _reg(
        capability_id="evidence.reconcile-pipeline",
        name="Evidence Pipeline Reconciliation (C42.28)",
        stage=CapabilityStage.EVIDENCE_INSPECTION,
        purpose=(
            "Re-execute the evidence pipeline plan (no mutation) and run the "
            "reconciliation phase, consuming existing on-disk evidence plus the "
            "planner output to verify plan-vs-evidence consistency."
        ),
        command="python runtime/verify.py evidence-reconcile",
        implementation="runtime.foundation.verification.executor_pipeline:main",
        category=CommandCategory.RECONCILIATION,
        trigger_conditions=(PROBLEM_CHANGED_FILE,),
        input_types=("changed_files",),
        input_sources=("git_working_tree",),
        produces=("reconciliation_report",),
        consumes=("execution_plan", "execution_evidence"),
        evidence_type="reconciliation_report",
        related_capabilities=(
            "evidence.pipeline-plan",
            "exec.evidence-execute",
            "certify.evidence-pipeline",
        ),
        notes="C52.3: closed the in-code-absent-from-catalog gap.",
    ),
    _reg(
        capability_id="evidence.reconcile",
        name="VEA-5 Plan Reconciliation Gate (C42.27)",
        stage=CapabilityStage.EVIDENCE_INSPECTION,
        purpose=(
            "Validate a CI plan against its own persisted execution evidence. "
            "A valid fully-passing execution yields same-plan (exit 0). Must "
            "NOT classify as environment-divergence merely because a local side "
            "was omitted. This is the CI reconciliation gate."
        ),
        command="python runtime/verify.py reconcile --plan PATH [--evidence PATH] [--local] [--json]",
        implementation="runtime/verify.py:cmd_reconcile",
        category=CommandCategory.RECONCILIATION,
        trigger_conditions=(PROBLEM_WORKFLOW_FAILURE, PROBLEM_STALE_EVIDENCE),
        input_types=("plan_manifest",),
        input_sources=("generated_evidence", "explicit_argument"),
        produces=("reconciliation_report",),
        consumes=("execution_plan", "execution_evidence"),
        evidence_type="reconciliation_report",
        related_capabilities=("evidence.pipeline-plan", "evidence.reconcile-pipeline"),
        notes="C52.3: closed the in-code-absent-from-catalog gap.",
    ),
    _reg(
        capability_id="evidence.knowledge-base",
        name="Verification Knowledge Base (C3/C42)",
        stage=CapabilityStage.EVIDENCE_INSPECTION,
        purpose=(
            "Query the canonical verification knowledge base: endpoints, "
            "capabilities, workspace, rules, and components. Indexes and "
            "formats the knowledge catalog for operator/agent consumption."
        ),
        command=(
            "python runtime/verify.py knowledge [endpoint|capability|workspace|rule|component] [--json] [--out PATH]"
        ),
        implementation="runtime.foundation.knowledge.indexer:build_index",
        category=CommandCategory.DIAGNOSTIC,
        trigger_conditions=(PROBLEM_UNKNOWN_FAILURE,),
        input_types=("query_type",),
        input_sources=("explicit_argument",),
        produces=("knowledge_report",),
        consumes=(),
        evidence_type="knowledge_report",
        related_capabilities=("certify.contract-governance", "certify.audit"),
        notes=(
            "C52.3: closed the in-code-absent-from-catalog gap. Sub-routes: "
            "knowledge endpoint|capability|workspace|rule|component."
        ),
    ),
]

REGISTRATIONS.extend(_REGISTRATIONS_EVIDENCE)
del _REGISTRATIONS_EVIDENCE

# Final: sort by stage order, then alphabetically within stage.
_STAGE_ORDER = {
    CapabilityStage.DISCOVERY: 0,
    CapabilityStage.PLANNING: 1,
    CapabilityStage.EXECUTION: 2,
    CapabilityStage.MEASUREMENT: 3,
    CapabilityStage.DIAGNOSIS: 4,
    CapabilityStage.STRENGTHENING: 5,
    CapabilityStage.EVIDENCE_INSPECTION: 6,
    CapabilityStage.CERTIFICATION: 7,
}

REGISTRATIONS.sort(key=lambda r: (_STAGE_ORDER[r.stage], r.capability_id))
