"""Phase 1 — Legacy architecture-builder catalogue (Program 13.2).

Produces ``runtime/generated/runtime-discovery-sources.json``: every place in
the Engineering Runtime that performed (or could perform) architecture
discovery, what it assumed, and which canonical source replaces it.

The catalogue is *curated* (each entry was read and classified) and *verified*
(a scanner re-checks the files on disk for residual legacy signals and reports
any uncatalogued hit).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_DIR = REPO_ROOT / "runtime" / "generated"
OUTPUT = GENERATED_DIR / "runtime-discovery-sources.json"

CANONICAL_PROVIDER = "runtime.foundation.architecture.get_architecture()"
CANONICAL_PIPELINE = "runtime.foundation.architecture.discovery"

# Discovery concerns enumerated by the program brief.
CONCERNS = (
    "engine_discovery",
    "package_discovery",
    "ownership_discovery",
    "capability_mapping",
    "router_mapping",
    "component_mapping",
    "knowledge_reconstruction",
    "artifact_ownership",
    "dependency_graph_generation",
    "execution_graph_generation",
    "cross_layer_map_generation",
    "verification_planning",
    "affected_analysis",
    "repair_suggestions",
    "certification_graph",
    "integrity_graph",
    "pipeline_graph",
)

STATUS_PIPELINE = "CANONICAL_PIPELINE"
STATUS_MIGRATED = "MIGRATED_CONSUMER"
STATUS_REPLACED = "REPLACED"
STATUS_CONSUMER = "CONSUMER_ONLY"


@dataclass(frozen=True, slots=True)
class DiscoverySource:
    file: str
    purpose: str
    concerns: tuple[str, ...]
    legacy_assumptions: tuple[str, ...]
    replacement_source: str
    status: str
    notes: str = ""

    def to_dict(self, repo_root: Path) -> dict[str, Any]:
        return {
            "file": self.file,
            "exists": (repo_root / self.file).exists(),
            "purpose": self.purpose,
            "concerns": list(self.concerns),
            "legacy_assumptions": list(self.legacy_assumptions),
            "replacement_source": self.replacement_source,
            "status": self.status,
            "notes": self.notes,
        }


NONE = ()

CATALOGUE: tuple[DiscoverySource, ...] = (
    # ---------------------------------------------------------------- pipeline
    DiscoverySource(
        "runtime/analyze_architecture.py",
        "Phase 1 of the single discovery pipeline: classify every module into one canonical node type.",
        ("engine_discovery", "package_discovery"),
        NONE,
        "runtime/generated/architecture-inventory.json",
        STATUS_PIPELINE,
        "Pipeline stage. Registered in runtime.foundation.architecture.discovery.PHASES.",
    ),
    DiscoverySource(
        "runtime/analyze_engine_topology.py",
        "Phase 2: discover canonical engines (package roots + designated single files).",
        ("engine_discovery", "package_discovery", "router_mapping", "capability_mapping"),
        NONE,
        "runtime/generated/engine-topology.json",
        STATUS_PIPELINE,
        "Pipeline stage.",
    ),
    DiscoverySource(
        "runtime/analyze_ownership.py",
        "Phase 3: build the evidence-backed ownership graph.",
        ("ownership_discovery",),
        NONE,
        "runtime/generated/ownership-graph.json",
        STATUS_PIPELINE,
        "Pipeline stage.",
    ),
    DiscoverySource(
        "runtime/analyze_execution.py",
        "Phase 4: build the runtime execution graph.",
        ("execution_graph_generation",),
        NONE,
        "runtime/generated/execution-graph.json",
        STATUS_PIPELINE,
        "Pipeline stage.",
    ),
    DiscoverySource(
        "runtime/analyze_engine_normalization.py",
        "Phase 5: classify engine migration status.",
        ("engine_discovery",),
        NONE,
        "runtime/generated/engine-normalization.json",
        STATUS_PIPELINE,
        "Pipeline stage.",
    ),
    DiscoverySource(
        "runtime/analyze_knowledge.py",
        "Phase 6: reconstruct knowledge entities from the ownership graph.",
        ("knowledge_reconstruction",),
        NONE,
        "runtime/generated/knowledge-reconstruction.json",
        STATUS_PIPELINE,
        "Pipeline stage.",
    ),
    DiscoverySource(
        "runtime/analyze_artifacts.py",
        "Phase 7: assign full ownership metadata to every generated artifact.",
        ("artifact_ownership",),
        NONE,
        "runtime/generated/artifact-ownership-v2.json",
        STATUS_PIPELINE,
        "Pipeline stage.",
    ),
    DiscoverySource(
        "runtime/analyze_gap.py",
        "Phase 8: certification gap analysis (old model vs canonical model).",
        ("certification_graph",),
        NONE,
        "runtime/generated/certification-gap-analysis.json",
        STATUS_PIPELINE,
        "Pipeline stage.",
    ),
    # ------------------------------------------------------- cross-layer map
    DiscoverySource(
        "tools/generators/build_cross_layer_map.py",
        "Legacy cross-layer map generator (Program 7A).",
        (
            "cross_layer_map_generation",
            "engine_discovery",
            "capability_mapping",
            "router_mapping",
            "component_mapping",
        ),
        (
            "Python file == Engine: emitted `backend/src/engines/<pkg>.py` for package engines, "
            "creating 7 phantom engine keys for files that do not exist.",
            "Registered every engine submodule (`loan_engine/emi.py`, `behaviour_engine/core.py`, ...) "
            "as a separate engine chain, duplicating 33 endpoints.",
            "Capability hook names derived from the filename (`_hook_name`) instead of the declared symbol.",
            "Engine tests discovered by substring match on the engine short name.",
            "Regex/substring ownership between endpoints and capability API paths.",
        ),
        "runtime.foundation.architecture.cross_layer.build_cross_layer_map_v2()",
        STATUS_REPLACED,
        "Now a deprecation shim that delegates to the canonical generator.",
    ),
    DiscoverySource(
        "runtime/foundation/audit/cross_layer.py",
        "Cross-layer map certification audit.",
        ("cross_layer_map_generation", "capability_mapping", "router_mapping"),
        (
            "Treated every map key as an engine FILE and asserted it exists on disk.",
            "`_check_file_exists` special-cased `.py` -> package to hide phantom engines.",
            "Flagged 'duplicate endpoints' when the same endpoint appeared under sibling submodule chains.",
            "Flagged 'missing capability' / 'missing router' for internal engines that legitimately have neither.",
            "Test-coverage denominator inflated by phantom + submodule chains.",
        ),
        CANONICAL_PROVIDER + " via runtime/generated/cross-layer-map-v2.json",
        STATUS_MIGRATED,
        "Audits canonical chains only; endpoint uniqueness is now checked at the Router (the real owner).",
    ),
    # ------------------------------------------------------------- knowledge
    DiscoverySource(
        "runtime/foundation/knowledge/indexer.py",
        "Knowledge index builder.",
        ("knowledge_reconstruction", "capability_mapping", "component_mapping"),
        (
            "Rebuilt capabilities/endpoints/components from the defective cross-layer map "
            "(rebuilt=4 vs saved=10 capabilities).",
            "Entity ownership expressed as `source_file: <phantom engine .py>`.",
            "Runtime artifact list hardcoded to nine filenames.",
        ),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
        "Entities now derive from the ownership graph; artifacts from artifact-ownership-v3.json.",
    ),
    DiscoverySource(
        "runtime/foundation/audit/knowledge.py",
        "Knowledge base certification audit.",
        ("knowledge_reconstruction",),
        (
            "Re-ran the indexer and compared counts, so a defective map produced a self-inconsistency failure.",
        ),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
        "Also asserts every knowledge entity resolves to a canonical owner.",
    ),
    DiscoverySource(
        "runtime/foundation/knowledge/query.py",
        "Knowledge query engine.",
        ("knowledge_reconstruction",),
        NONE,
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
        "Reads the catalog produced by the migrated indexer.",
    ),
    DiscoverySource(
        "runtime/foundation/knowledge/references.py",
        "Knowledge reference resolution.",
        ("knowledge_reconstruction",),
        NONE,
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    # ------------------------------------------------------ artifact ownership
    DiscoverySource(
        "runtime/foundation/audit/artifact_ownership.py",
        "Artifact ownership certification audit.",
        ("artifact_ownership",),
        (
            "Ownership resolved by matching the artifact FILENAME against two hardcoded allowlists "
            "(ARTIFACT_OWNERS / RETENTION_POLICIES); anything new was 'unowned'.",
            "No producer evidence, no pipeline/lifecycle, no engine or capability linkage.",
        ),
        "runtime/generated/artifact-ownership-v3.json via " + CANONICAL_PROVIDER,
        STATUS_MIGRATED,
        "Ownership now comes from producer evidence + ownership/execution graphs.",
    ),
    # ------------------------------------------------------------- graphs
    DiscoverySource(
        "runtime/foundation/audit/dependency_graph.py",
        "Dependency graph certification audit.",
        ("dependency_graph_generation", "ownership_discovery"),
        (
            "Audited a single repository index graph that mixed ownership, execution and dependency edges.",
            "'ownership' was a node attribute string, not an ownership relation.",
        ),
        "runtime/generated/dependency-graph-v2.json via " + CANONICAL_PROVIDER,
        STATUS_MIGRATED,
        "Ownership, execution and dependency are now three distinct, separately audited graphs.",
    ),
    DiscoverySource(
        "runtime/foundation/repository/builder/builder.py",
        "Repository index/graph builder.",
        ("dependency_graph_generation", "engine_discovery", "ownership_discovery"),
        (
            "Classified nodes by directory segment ('/engines/' -> engine), so package engines and "
            "their submodules were indistinguishable.",
        ),
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
        "Retained as a file-level index; architectural node identity now comes from the provider.",
    ),
    DiscoverySource(
        "runtime/foundation/repository/scanner/backend_scanner.py",
        "Backend file scanner for the repository index.",
        ("engine_discovery", "router_mapping", "ownership_discovery"),
        (
            "`{'engines': 'engine'}` directory->type map (file == engine).",
            "Relationship inference by substring test on module names "
            "('services' in source and 'engines' in target).",
        ),
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
        "File inventory only; not an architecture authority.",
    ),
    DiscoverySource(
        "runtime/foundation/repository/scanner/metadata_scanner.py",
        "Capability registry metadata scanner.",
        ("capability_mapping",),
        ("Capability -> engine edges read from a hand-maintained registry file.",),
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    DiscoverySource(
        "runtime/foundation/repository/graph/graph_service.py",
        "Repository graph query service.",
        ("dependency_graph_generation",),
        ("Single graph conflated ownership/execution/dependency semantics.",),
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    # -------------------------------------------------- verification planning
    DiscoverySource(
        "runtime/foundation/verification/planner/planner.py",
        "Cross-layer impact planner (blast radius, verification plan).",
        ("verification_planning", "affected_analysis", "cross_layer_map_generation"),
        (
            "Planned against phantom engine keys from the legacy cross-layer map.",
            "`_service_name_from_path` guessed the service class by PascalCasing the filename.",
            "Capability file path guessed as `frontend/lib/capabilities/{cap.lower()}.ts`.",
            "Property tests triggered by `'loan' in engine_name`.",
        ),
        CANONICAL_PROVIDER + " + runtime/generated/cross-layer-map-v2.json",
        STATUS_MIGRATED,
        "Resolves changed files to canonical engines; legacy flat maps still accepted for tests.",
    ),
    DiscoverySource(
        "runtime/foundation/verification/planner/plan_models.py",
        "Verification plan construction from impact.",
        ("verification_planning",),
        (
            "Engine name taken from a path segment; unit test path guessed as "
            "`tests/unit/engines/{engine_name}/`.",
        ),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
        "Test paths now come from the engine's recorded tests when available.",
    ),
    DiscoverySource(
        "runtime/foundation/verification/planner/impact_rules.py",
        "Impact rules (which layer a changed file belongs to).",
        ("verification_planning",),
        ("`file_path.startswith('backend/src/engines/')` as the engine test.",),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
        "Rule now asks the provider whether the path resolves to a canonical engine.",
    ),
    DiscoverySource(
        "runtime/foundation/verification/orchestrator.py",
        "Verification orchestrator.",
        ("verification_planning",),
        NONE,
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    DiscoverySource(
        "runtime/foundation/audit/planner.py",
        "Verification planner certification audit.",
        ("verification_planning", "certification_graph"),
        ("Probed the planner with the phantom path `backend/src/engines/loan_engine.py`.",),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
        "Probes now use a canonical engine implementation module.",
    ),
    # ------------------------------------------------------ affected / repair
    DiscoverySource(
        "runtime/foundation/intelligence/affected.py",
        "Affected test planner.",
        ("affected_analysis",),
        (
            "Engine name = basename minus `.py`; unit tests guessed as "
            "`backend/tests/unit/engines/{name}/` (wrong for every package engine).",
        ),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
        "Uses the engine's evidence-backed test list.",
    ),
    DiscoverySource(
        "runtime/foundation/intelligence/diagnostics.py",
        "Developer diagnostics (blast radius + repair).",
        ("affected_analysis", "repair_suggestions"),
        ("Consumed affected_engines containing phantom engine paths.",),
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    DiscoverySource(
        "runtime/foundation/intelligence/repair.py",
        "Repair suggestion guidance.",
        ("repair_suggestions",),
        NONE,
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    DiscoverySource(
        "runtime/foundation/intelligence/risk.py",
        "Change risk analysis.",
        ("affected_analysis",),
        ("Risk weighted by count of 'changed engines' that included submodules and phantoms.",),
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    # ---------------------------------------------------------- integrity
    DiscoverySource(
        "runtime/foundation/integrity/scanner.py",
        "Architecture layer classifier for integrity rules.",
        ("integrity_graph", "engine_discovery"),
        (
            "`_ENGINE_DIRS` was a hardcoded set of engine FILENAMES "
            "(ledger_audit_engine.py, insight_generator.py, ...).",
        ),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
        "Layer classification asks the provider first, then falls back to directory rules.",
    ),
    DiscoverySource(
        "runtime/foundation/integrity/registry.py",
        "Integrity rule constitution.",
        ("integrity_graph",),
        ("Rule examples referenced engine paths as illustrative strings only.",),
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    DiscoverySource(
        "runtime/foundation/audit/integrity.py",
        "Integrity engine certification audit.",
        ("integrity_graph", "certification_graph"),
        ("Probe used the phantom module `backend/src/engines/loan_engine.py`.",),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
    ),
    # ------------------------------------------------------- certification
    DiscoverySource(
        "runtime/foundation/audit/runner.py",
        "Certification audit runner.",
        ("certification_graph",),
        NONE,
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
        "Runs registered audit sections; performs no discovery.",
    ),
    DiscoverySource(
        "runtime/foundation/audit/certification.py",
        "Certification progress/dashboard tracker.",
        ("certification_graph",),
        NONE,
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    DiscoverySource(
        "runtime/foundation/audit/evidence.py",
        "Evidence aggregator certification audit.",
        ("certification_graph",),
        ("Sample cross-layer map used the phantom key `backend/src/engines/account_engine.py`.",),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
    ),
    DiscoverySource(
        "runtime/foundation/audit/failure_injection.py",
        "Failure injection certification audit.",
        ("certification_graph",),
        ("Synthetic capability registry referenced `backend/src/engines/transfer_engine` (non-existent).",),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
        "Synthetic fixtures are now labelled as fixtures, not architecture.",
    ),
    DiscoverySource(
        "runtime/foundation/audit/pipeline.py",
        "Pipeline validation audit (pipeline graph).",
        ("pipeline_graph", "certification_graph"),
        ("Stage list hardcoded; knowledge/artifact stages validated against legacy artifacts.",),
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    DiscoverySource(
        "runtime/foundation/audit/normalize.py",
        "Audit finding normalisation.",
        ("certification_graph",),
        NONE,
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    DiscoverySource(
        "runtime/foundation/audit/cluster.py",
        "Root-cause clustering.",
        ("certification_graph",),
        NONE,
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    DiscoverySource(
        "runtime/foundation/audit/repair_order.py",
        "Repair ordering.",
        ("certification_graph", "repair_suggestions"),
        NONE,
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    DiscoverySource(
        "runtime/foundation/audit/remediation.py",
        "Platform remediation plan.",
        ("certification_graph", "repair_suggestions"),
        NONE,
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
    ),
    # ------------------------------------------------------- observability
    DiscoverySource(
        "runtime/system/observability/dependency_growth.py",
        "Cross-layer dependency growth metrics.",
        ("dependency_graph_generation",),
        (
            "Counted 'engines' as `engine_file.count('/')` over legacy map keys — "
            "a path-shape heuristic, not an engine count.",
        ),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
    ),
    DiscoverySource(
        "runtime/foundation/workspace/workspace.py",
        "Workspace cross-layer status panel.",
        ("engine_discovery",),
        ("Counted one engine per legacy map key, so phantoms and submodules inflated the total.",),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
    ),
    DiscoverySource(
        "runtime/system/evidence/collectors/coverage.py",
        "Engine coverage evidence collector.",
        ("engine_discovery",),
        ("Engine files identified by the substring '/engines/'.",),
        CANONICAL_PROVIDER,
        STATUS_MIGRATED,
    ),
    # --------------------------------------------------------------- tools
    DiscoverySource(
        "tools/development/mutation_discovery.py",
        "Mutation target discovery.",
        ("engine_discovery",),
        ("Walks `backend/src/engines` and treats each `.py` as a mutation engine target.",),
        CANONICAL_PROVIDER,
        STATUS_CONSUMER,
        "Operates on files for mutation purposes; makes no architectural claim.",
    ),
)


# ---------------------------------------------------------------------------
# residual-signal scanner
# ---------------------------------------------------------------------------

LEGACY_SIGNALS: tuple[tuple[str, str, str], ...] = (
    (
        "phantom_engine_path",
        r"backend/src/engines/[a-z_]+_engine\.py",
        "References a `<engine>.py` path; package engines have no such file.",
    ),
    (
        "engine_py_composition",
        r"engines/\{[^}]+\}\.py|engines/\" *\+|f\"backend/src/engines/\{",
        "Composes an engine path by appending `.py` to a name.",
    ),
    (
        "legacy_map_load",
        r"cross-layer-map\.json",
        "Loads the legacy cross-layer map directly instead of the provider.",
    ),
    (
        "engine_name_from_path",
        r"engine\.split\(\"/\"\)\[-1\]|split\(\"/\"\)\[-1\]\.replace\(\"\.py\"",
        "Derives an engine identity from a path basename.",
    ),
    (
        "engines_dir_heuristic",
        r"startswith\(\"backend/src/engines/\"\)|\"/engines/\" (?:in|not in)",
        "Uses a directory prefix as the engine test.",
    ),
)

SCAN_ROOTS = ("runtime", "tools")
SCAN_EXCLUDE = ("__pycache__", "runtime/generated", "node_modules", ".git")
# Files that legitimately mention legacy identifiers (catalogue + migration code).
SIGNAL_ALLOWLIST = {
    "runtime/foundation/architecture/sources.py",
    "runtime/foundation/architecture/consistency.py",
    "runtime/foundation/architecture/cross_layer.py",
    "runtime/foundation/architecture/artifacts.py",
    "runtime/foundation/architecture/knowledge_migration.py",
    "runtime/analyze_architecture.py",
    "runtime/analyze_engine_topology.py",
    "runtime/analyze_engine_normalization.py",
    "runtime/analyze_ownership.py",
    "runtime/analyze_execution.py",
    "runtime/analyze_knowledge.py",
    "runtime/analyze_artifacts.py",
    "runtime/analyze_gap.py",
}


def _iter_python_files(repo_root: Path):
    for root_name in SCAN_ROOTS:
        root = repo_root / root_name
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            rel = path.relative_to(repo_root).as_posix()
            if any(x in rel for x in SCAN_EXCLUDE):
                continue
            yield rel, path


def scan_residual_signals(repo_root: Path | None = None) -> list[dict[str, Any]]:
    """Scan runtime + tools for residual legacy architecture assumptions."""
    root = repo_root or REPO_ROOT
    catalogued = {c.file for c in CATALOGUE}
    hits: list[dict[str, Any]] = []
    for rel, path in _iter_python_files(root):
        if rel in SIGNAL_ALLOWLIST:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:  # pragma: no cover - defensive
            continue
        is_test = "/tests/" in rel or rel.split("/")[-1].startswith("test_")
        for signal, pattern, description in LEGACY_SIGNALS:
            matches = re.findall(pattern, text)
            if not matches:
                continue
            hits.append(
                {
                    "file": rel,
                    "signal": signal,
                    "description": description,
                    "occurrences": len(matches),
                    "catalogued": rel in catalogued,
                    "kind": "test_fixture" if is_test else "runtime_code",
                }
            )
    return hits


def build(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or REPO_ROOT
    from runtime.foundation.architecture.discovery import pipeline_manifest

    residual = scan_residual_signals(root)
    uncatalogued = [
        h for h in residual if not h["catalogued"] and h["kind"] == "runtime_code"
    ]
    by_concern: dict[str, list[str]] = {c: [] for c in CONCERNS}
    for entry in CATALOGUE:
        for concern in entry.concerns:
            by_concern.setdefault(concern, []).append(entry.file)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "Program 13.2 — Phase 1: Locate Every Legacy Architecture Builder",
        "rule": (
            "Exactly one architecture discovery pipeline may exist. Every other "
            "runtime subsystem must consume "
            f"{CANONICAL_PROVIDER}."
        ),
        "canonical_pipeline": pipeline_manifest(),
        "canonical_provider": CANONICAL_PROVIDER,
        "concerns": list(CONCERNS),
        "source_count": len(CATALOGUE),
        "status_counts": {
            status: sum(1 for c in CATALOGUE if c.status == status)
            for status in (
                STATUS_PIPELINE,
                STATUS_REPLACED,
                STATUS_MIGRATED,
                STATUS_CONSUMER,
            )
        },
        "sources": [c.to_dict(root) for c in CATALOGUE],
        "sources_by_concern": {k: sorted(set(v)) for k, v in sorted(by_concern.items())},
        "residual_legacy_signals": residual,
        "uncatalogued_runtime_signals": uncatalogued,
        "notes": [
            "Files marked CANONICAL_PIPELINE are the phases of the single discovery pipeline.",
            "Files marked REPLACED no longer perform discovery; they delegate to the canonical generator.",
            "Files marked MIGRATED_CONSUMER previously performed discovery and now read the provider.",
            "Files marked CONSUMER_ONLY never claimed architectural authority; they are listed for completeness.",
            "residual_legacy_signals includes test fixtures, which intentionally hard-code legacy paths "
            "to prove backward compatibility; only uncatalogued_runtime_signals is a defect.",
        ],
    }


def save(repo_root: Path | None = None) -> Path:
    data = build(repo_root)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return OUTPUT
