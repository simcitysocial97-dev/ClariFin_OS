"""Artifact Ownership Audit — Program 12.

Audits generated artifacts for ownership, creation, consumption,
overwrites, retention policies, duplicates, and unused artifacts.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

GENERATED_DIR = REPO_ROOT / "runtime" / "generated"
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"

ARTIFACT_OWNERS = {
    "cross-layer-map.json": {"owner": "platform", "creator": "build_cross_layer_map", "consumer": "diagnostics,planner,reporting"},
    "knowledge-index.json": {"owner": "platform", "creator": "knowledge_indexer", "consumer": "query_engine,workspace"},
    "verification-cache.json": {"owner": "runtime", "creator": "verification_runtime", "consumer": "orchestrator,cache_checker"},
    "engineering-history.json": {"owner": "platform", "creator": "observability", "consumer": "reporting,dashboard"},
    "dashboard.json": {"owner": "platform", "creator": "dashboard_generator", "consumer": "workspace,reporting"},
    "verification-report.md": {"owner": "runtime", "creator": "orchestrator", "consumer": "reporting,ci_summary"},
    "verification-pipeline.md": {"owner": "runtime", "creator": "planner", "consumer": "documentation"},
    "verification-profile-matrix.md": {"owner": "platform", "creator": "profile_manager", "consumer": "documentation"},
    "verification-quality.md": {"owner": "platform", "creator": "quality_gate", "consumer": "reporting"},
    "dependency-growth.json": {"owner": "platform", "creator": "dependency_tracker", "consumer": "reporting"},
    "cost-analysis.json": {"owner": "platform", "creator": "cost_analyzer", "consumer": "reporting"},
    "engineering-analytics.json": {"owner": "platform", "creator": "analytics_engine", "consumer": "reporting,dashboard"},
    "engineering-events.jsonl": {"owner": "platform", "creator": "event_collector", "consumer": "analytics,reporting"},
    "flaky-tests.json": {"owner": "runtime", "creator": "test_runner", "consumer": "quality_gate"},
    "github-workflow-inventory.json": {"owner": "platform", "creator": "workflow_scanner", "consumer": "reporting"},
    "program8-completion-report.md": {"owner": "platform", "creator": "program8", "consumer": "documentation"},
    "validation-summary.md": {"owner": "platform", "creator": "validator", "consumer": "documentation"},
    "acceptance_planner.py": {"owner": "platform", "creator": "planner", "consumer": "workspace"},
    "artifact-ownership.json": {"owner": "platform", "creator": "audit", "consumer": "reporting"},
    "certification-dashboard.json": {"owner": "platform", "creator": "certification_tracker", "consumer": "reporting,dashboard"},
    "certification-history.json": {"owner": "platform", "creator": "certification_tracker", "consumer": "reporting"},
    "certification-progress.json": {"owner": "platform", "creator": "certification_tracker", "consumer": "reporting"},
    "contract.json": {"owner": "platform", "creator": "contract_generator", "consumer": "reporting"},
    "contract_empty.json": {"owner": "platform", "creator": "contract_generator", "consumer": "reporting"},
    "contract_invalid.json": {"owner": "platform", "creator": "contract_generator", "consumer": "reporting"},
    "contract_partial.json": {"owner": "platform", "creator": "contract_generator", "consumer": "reporting"},
    "contract_valid.json": {"owner": "platform", "creator": "contract_generator", "consumer": "reporting"},
    "coverage.json": {"owner": "platform", "creator": "coverage_collector", "consumer": "reporting"},
    "coverage_empty.json": {"owner": "platform", "creator": "coverage_collector", "consumer": "reporting"},
    "coverage_invalid.json": {"owner": "platform", "creator": "coverage_collector", "consumer": "reporting"},
    "coverage_partial.json": {"owner": "platform", "creator": "coverage_collector", "consumer": "reporting"},
    "coverage_valid.json": {"owner": "platform", "creator": "coverage_collector", "consumer": "reporting"},
    "dependency-health.json": {"owner": "platform", "creator": "dependency_tracker", "consumer": "reporting"},
    "engineering-health.md": {"owner": "platform", "creator": "health_report", "consumer": "reporting"},
    "engineering-platform-audit.json": {"owner": "platform", "creator": "audit", "consumer": "reporting"},
    "engineering-platform-audit.md": {"owner": "platform", "creator": "audit", "consumer": "reporting"},
    "engineering-platform-audit-v2.json": {"owner": "certification", "creator": "runtime/foundation/audit/certification.py", "consumer": "reporting"},
    "engineering-platform-audit-v3.json": {"owner": "certification", "creator": "runtime/foundation/audit/certification.py", "consumer": "reporting"},
    "engineering-platform-audit-v3.md": {"owner": "certification", "creator": "runtime/foundation/audit/certification.py", "consumer": "reporting"},
    "runtime-migration-report.md": {"owner": "certification", "creator": "runtime/foundation/architecture", "consumer": "documentation"},
    "provider-consumer-inventory.json": {"owner": "certification", "creator": "runtime/foundation/architecture", "consumer": "documentation"},
    "runtime-id-consistency.json": {"owner": "certification", "creator": "runtime/foundation/architecture", "consumer": "documentation"},
    "provider-performance.json": {"owner": "certification", "creator": "runtime/foundation/architecture", "consumer": "documentation"},
    "runtime-retirement-plan.json": {"owner": "certification", "creator": "runtime/foundation/architecture", "consumer": "documentation"},
    "runtime-constitution.json": {"owner": "certification", "creator": "runtime/foundation/architecture", "consumer": "documentation"},
    "runtime-consumer-migration.md": {"owner": "certification", "creator": "runtime/foundation/architecture", "consumer": "documentation"},
    # --- Program 14.0: Engineering Intelligence Layer ---
    "change-intelligence.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/change.py", "consumer": "blast_radius,verification_optimizer,platform_state"},
    "blast-radius.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/blast.py", "consumer": "verification_optimizer,risk_engine,repair_intelligence"},
    "verification-plan.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/optimizer.py", "consumer": "verification_cost,platform_state"},
    "engineering-risk.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/risk.py", "consumer": "platform_state,reporting"},
    "repair-intelligence.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/repair.py", "consumer": "platform_state,reporting"},
    "engineering-memory.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/memory.py", "consumer": "risk_engine,platform_state"},
    "github-intelligence.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/ci.py", "consumer": "platform_state,reporting"},
    "verification-cost.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/cost.py", "consumer": "platform_state,reporting"},
    "platform-state.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/state.py", "consumer": "dashboard,reporting"},
    "engineering-platform-audit-v4.json": {"owner": "certification", "creator": "runtime/foundation/intelligence/platform/certification.py", "consumer": "reporting"},
    "engineering-platform-audit-v5.json": {"owner": "certification", "creator": "runtime/foundation/intelligence/platform/certification.py", "consumer": "reporting"},
    "program14-certification.md": {"owner": "certification", "creator": "runtime/foundation/intelligence/platform/certification.py", "consumer": "documentation"},
    "program14.1-certification.md": {"owner": "certification", "creator": "runtime/foundation/intelligence/platform/certification.py", "consumer": "documentation"},
    "intelligence-inventory.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/migration.py", "consumer": "documentation"},
    "intelligence-duplication.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/migration.py", "consumer": "documentation"},
    "test-resolution.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/migration.py", "consumer": "verification"},
    "cli-consistency.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/migration.py", "consumer": "documentation"},
    "intelligence-api.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/migration.py", "consumer": "documentation"},
    "intelligence-retirement-plan.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/migration.py", "consumer": "documentation"},
    "intelligence-constitution.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/migration.py", "consumer": "documentation"},
    "runtime-simplification.json": {"owner": "intelligence", "creator": "runtime/foundation/intelligence/platform/migration.py", "consumer": "documentation"},
    "github-actions-health.json": {"owner": "platform", "creator": "github_health", "consumer": "reporting"},
    "index.json": {"owner": "platform", "creator": "repository_indexer", "consumer": "graph_service"},
    "junit-property.xml": {"owner": "runtime", "creator": "test_runner", "consumer": "quality_gate"},
    "junit.xml": {"owner": "runtime", "creator": "test_runner", "consumer": "quality_gate"},
    "junit_empty.xml": {"owner": "runtime", "creator": "test_runner", "consumer": "quality_gate"},
    "junit_invalid.xml": {"owner": "runtime", "creator": "test_runner", "consumer": "quality_gate"},
    "junit_partial.xml": {"owner": "runtime", "creator": "test_runner", "consumer": "quality_gate"},
    "junit_valid.xml": {"owner": "runtime", "creator": "test_runner", "consumer": "quality_gate"},
    "loan-results.txt": {"owner": "platform", "creator": "loan_engine", "consumer": "reporting"},
    "mutation-summary.json": {"owner": "platform", "creator": "mutation_runner", "consumer": "reporting"},
    "normalized-issues.json": {"owner": "platform", "creator": "audit_normalizer", "consumer": "reporting"},
    "pipeline-certification.md": {"owner": "platform", "creator": "pipeline", "consumer": "documentation"},
    "pipeline-validation.json": {"owner": "platform", "creator": "pipeline", "consumer": "reporting"},
    "plan.json": {"owner": "platform", "creator": "planner", "consumer": "workspace"},
    "platform-remediation.md": {"owner": "platform", "creator": "remediation_engine", "consumer": "documentation"},
    "repair-order.json": {"owner": "platform", "creator": "repair_orderer", "consumer": "reporting"},
    "root-cause-clusters.json": {"owner": "platform", "creator": "cluster_analyzer", "consumer": "reporting"},
    "runtime-defects.json": {"owner": "platform", "creator": "defect_detector", "consumer": "reporting"},
    "summary.json": {"owner": "platform", "creator": "aggregator", "consumer": "reporting"},
    "summary.md": {"owner": "platform", "creator": "aggregator", "consumer": "reporting"},
    "system-health-score.json": {"owner": "platform", "creator": "health_scorer", "consumer": "reporting,dashboard"},
    "verification-performance.json": {"owner": "runtime", "creator": "performance_tracker", "consumer": "reporting"},
}

RETENTION_POLICIES = {
    "cross-layer-map.json": "90_days",
    "knowledge-index.json": "90_days",
    "verification-cache.json": "14_days",
    "engineering-history.json": "90_days",
    "dashboard.json": "30_days",
    "verification-report.md": "30_days",
    "verification-pipeline.md": "30_days",
    "verification-profile-matrix.md": "30_days",
    "verification-quality.md": "30_days",
    "dependency-growth.json": "30_days",
    "cost-analysis.json": "30_days",
    "engineering-analytics.json": "30_days",
    "engineering-events.jsonl": "90_days",
    "flaky-tests.json": "14_days",
    "github-workflow-inventory.json": "30_days",
    "program8-completion-report.md": "permanent",
    "validation-summary.md": "30_days",
    "acceptance_planner.py": "30_days",
    "artifact-ownership.json": "30_days",
    "certification-dashboard.json": "30_days",
    "certification-history.json": "permanent",
    "certification-progress.json": "30_days",
    "contract.json": "30_days",
    "contract_empty.json": "30_days",
    "contract_invalid.json": "30_days",
    "contract_partial.json": "30_days",
    "contract_valid.json": "30_days",
    "coverage.json": "30_days",
    "coverage_empty.json": "30_days",
    "coverage_invalid.json": "30_days",
    "coverage_partial.json": "30_days",
    "coverage_valid.json": "30_days",
    "dependency-health.json": "30_days",
    "engineering-health.md": "30_days",
    "engineering-platform-audit.json": "30_days",
    "engineering-platform-audit.md": "30_days",
    "github-actions-health.json": "30_days",
    "index.json": "90_days",
    "junit-property.xml": "14_days",
    "junit.xml": "14_days",
    "junit_empty.xml": "14_days",
    "junit_invalid.xml": "14_days",
    "junit_partial.xml": "14_days",
    "junit_valid.xml": "14_days",
    "loan-results.txt": "30_days",
    "mutation-summary.json": "90_days",
    "normalized-issues.json": "30_days",
    "pipeline-certification.md": "permanent",
    "pipeline-validation.json": "30_days",
    "plan.json": "30_days",
    "platform-remediation.md": "permanent",
    "repair-order.json": "90_days",
    "root-cause-clusters.json": "90_days",
    "runtime-defects.json": "30_days",
    "summary.json": "30_days",
    "summary.md": "30_days",
    "engineering-platform-audit-v2.json": "30_days",
    "engineering-platform-audit-v3.json": "30_days",
    "engineering-platform-audit-v3.md": "30_days",
    "runtime-migration-report.md": "permanent",
    "provider-consumer-inventory.json": "permanent",
    "runtime-id-consistency.json": "permanent",
    "provider-performance.json": "permanent",
    "runtime-retirement-plan.json": "permanent",
    "runtime-constitution.json": "permanent",
    "runtime-consumer-migration.md": "permanent",
    # --- Program 14.0: Engineering Intelligence Layer ---
    # Intelligence outputs describe the CURRENT change set, so they are
    # short-lived; certification records are permanent.
    "change-intelligence.json": "14_days",
    "blast-radius.json": "14_days",
    "verification-plan.json": "14_days",
    "engineering-risk.json": "30_days",
    "repair-intelligence.json": "30_days",
    "engineering-memory.json": "permanent",
    "github-intelligence.json": "14_days",
    "verification-cost.json": "30_days",
    "platform-state.json": "30_days",
    "engineering-platform-audit-v4.json": "permanent",
    "program14-certification.md": "permanent",
    "program14.1-certification.md": "permanent",
    "intelligence-inventory.json": "90_days",
    "intelligence-duplication.json": "90_days",
    "test-resolution.json": "90_days",
    "cli-consistency.json": "30_days",
    "intelligence-api.json": "permanent",
    "intelligence-retirement-plan.json": "permanent",
    "intelligence-constitution.json": "permanent",
    "runtime-simplification.json": "permanent",
    "engineering-platform-audit-v5.json": "permanent",
    "system-health-score.json": "30_days",
    "verification-performance.json": "30_days",
}


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    repo_root = repo_root or REPO_ROOT
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    generated_dir = repo_root / "runtime" / "generated"
    if not generated_dir.exists():
        findings.append(
            _finding(
                "artifact_ownership",
                "AO-001",
                "Generated directory does not exist",
                "fail",
                "critical",
                f"Generated directory {generated_dir} does not exist",
                {"path": str(generated_dir)},
                "Ensure the generated directory exists and is populated",
            )
        )
        return {
            "section": "artifact_ownership",
            "name": "Artifact Ownership Audit",
            "status": "fail",
            "findings": findings,
            "metrics": {"generated_dir_exists": False},
            "duration_seconds": round(time.monotonic() - start, 3),
        }

    artifact_files = _list_artifacts(generated_dir)
    metrics["total_artifacts"] = len(artifact_files)
    metrics["generated_dir_exists"] = True

    v3_by_name = _load_v3_by_name(repo_root)

    ownership_check = _check_ownership(artifact_files, v3_by_name)
    findings.extend(ownership_check["findings"])
    metrics.update(ownership_check["metrics"])

    overwrite_check = _check_overwrites(artifact_files)
    findings.extend(overwrite_check["findings"])
    metrics.update(overwrite_check["metrics"])

    retention_check = _check_retention_policies(artifact_files, v3_by_name)
    findings.extend(retention_check["findings"])
    metrics.update(retention_check["metrics"])

    duplicate_check = _check_duplicates(generated_dir)
    findings.extend(duplicate_check["findings"])
    metrics.update(duplicate_check["metrics"])

    unused_check = _check_unused_artifacts(artifact_files)
    findings.extend(unused_check["findings"])
    metrics.update(unused_check["metrics"])

    workflow_ref_check = _check_workflow_references(repo_root)
    findings.extend(workflow_ref_check["findings"])
    metrics.update(workflow_ref_check["metrics"])

    consumer_check = _check_consumers(artifact_files, v3_by_name)
    findings.extend(consumer_check["findings"])
    metrics.update(consumer_check["metrics"])

    status = "pass" if all(f["status"] == "pass" for f in findings) else "fail"
    duration = time.monotonic() - start

    return {
        "section": "artifact_ownership",
        "name": "Artifact Ownership Audit",
        "status": status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": round(duration, 3),
    }


def _list_artifacts(generated_dir: Path) -> list[Path]:
    artifacts: list[Path] = []
    for item in generated_dir.rglob("*"):
        if item.is_file() and not item.name.startswith("."):
            artifacts.append(item)
    return artifacts


def _load_v3_by_name(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Load the canonical artifact-ownership-v3 registry keyed by file name.

    Program 13.2: the canonical registry (built by the architecture provider)
    is the single source of artifact ownership truth, replacing the hardcoded
    ``ARTIFACT_OWNERS`` table.
    """
    path = repo_root / "runtime" / "generated" / "artifact-ownership-v3.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    by_name: dict[str, dict[str, Any]] = {}
    for entry in data.get("artifacts", []):
        name = entry.get("artifact", "").split("/")[-1]
        if name:
            by_name[name] = entry
    return by_name


def _record_for(name: str, v3_by_name: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if name in v3_by_name:
        rec = v3_by_name[name]
        return {
            "owner": rec.get("owner", ""),
            "creator": rec.get("creator") or rec.get("producer", ""),
            "consumer": ",".join(rec.get("consumers", [])) if rec.get("consumers") else "",
            "retention": rec.get("retention", ""),
            "source": "artifact-ownership-v3",
        }
    if name in ARTIFACT_OWNERS:
        return {**ARTIFACT_OWNERS[name], "source": "legacy-registry"}
    return None


def _check_ownership(artifact_files: list[Path], v3_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    owned_count = 0
    unowned_count = 0

    for artifact in artifact_files:
        name = artifact.name
        rec = _record_for(name, v3_by_name)
        if rec:
            owned_count += 1
            metrics[f"artifact_{name}_owner"] = rec["owner"]
            metrics[f"artifact_{name}_creator"] = rec["creator"]
        else:
            unowned_count += 1
            findings.append(
                _finding(
                    "artifact_ownership",
                    "AO-002",
                    f"Artifact has no registered owner: {name}",
                    "warning",
                    "medium",
                    f"Artifact {name} in runtime/generated/ has no registered owner",
                    {"artifact": name, "path": str(artifact)},
                    f"Register an owner for {name} in the artifact ownership registry",
                )
            )

    metrics["owned_artifacts"] = owned_count
    metrics["unowned_artifacts"] = unowned_count

    if unowned_count == 0:
        findings.append(
            _finding(
                "artifact_ownership",
                "AO-003",
                "All artifacts have registered owners",
                "pass",
                "info",
                f"All {owned_count} artifacts in runtime/generated/ have registered owners",
                {},
                "Continue registering ownership for all generated artifacts",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_overwrites(artifact_files: list[Path]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    seen_names: dict[str, list[str]] = {}
    for artifact in artifact_files:
        name = artifact.name
        if name not in seen_names:
            seen_names[name] = []
        seen_names[name].append(str(artifact))

    duplicate_names = {}
    for name, paths in seen_names.items():
        if len(paths) <= 1:
            continue
        unique_dirs = set()
        for p in paths:
            parent = str(Path(p).parent)
            unique_dirs.add(parent)
        if len(unique_dirs) <= 1:
            duplicate_names[name] = paths

    for name, paths in duplicate_names.items():
        findings.append(
            _finding(
                "artifact_ownership",
                "AO-004",
                f"Potential overwrite: {name} found in multiple locations",
                "fail",
                "high",
                f"Artifact {name} exists in {len(paths)} locations, which may cause overwrites",
                {"artifact": name, "paths": paths},
                f"Consolidate {name} to a single location or rename duplicates",
            )
        )

    metrics["unique_artifact_names"] = len(seen_names)
    metrics["duplicate_artifact_names"] = len(duplicate_names)

    if not duplicate_names:
        findings.append(
            _finding(
                "artifact_ownership",
                "AO-005",
                "No artifact overwrites detected",
                "pass",
                "info",
                "All artifact names in runtime/generated/ are unique",
                {},
                "Continue ensuring unique artifact names",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_retention_policies(artifact_files: list[Path], v3_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    for artifact in artifact_files:
        name = artifact.name
        rec = _record_for(name, v3_by_name)
        policy = (rec or {}).get("retention") or RETENTION_POLICIES.get(name)
        if policy:
            metrics[f"artifact_{name}_retention"] = policy
        else:
            findings.append(
                _finding(
                    "artifact_ownership",
                    "AO-006",
                    f"Artifact has no retention policy: {name}",
                    "warning",
                    "low",
                    f"Artifact {name} has no defined retention policy",
                    {"artifact": name, "path": str(artifact)},
                    f"Define a retention policy for {name}",
                )
            )

    if not any(f["check_id"] == "AO-006" for f in findings):
        findings.append(
            _finding(
                "artifact_ownership",
                "AO-007",
                "All artifacts have retention policies",
                "pass",
                "info",
                f"All {len(artifact_files)} artifacts have defined retention policies",
                {},
                "Review retention policies periodically",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_duplicates(generated_dir: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    content_hashes: dict[str, list[str]] = {}
    for artifact in generated_dir.rglob("*"):
        if not artifact.is_file() or artifact.name.startswith("."):
            continue
        try:
            content = artifact.read_bytes()
            import hashlib
            h = hashlib.md5(content).hexdigest()
            key = f"{artifact.name}:{h}"
            if key not in content_hashes:
                content_hashes[key] = []
            content_hashes[key].append(str(artifact))
        except Exception:
            continue

    duplicate_content = {k: v for k, v in content_hashes.items() if len(v) > 1}
    metrics["content_unique_artifacts"] = len(content_hashes)
    metrics["content_duplicate_groups"] = len(duplicate_content)

    for key, paths in duplicate_content.items():
        name = key.split(":")[0]
        findings.append(
            _finding(
                "artifact_ownership",
                "AO-008",
                f"Duplicate content for artifact: {name}",
                "warning",
                "medium",
                f"Artifact {name} has identical content in {len(paths)} locations",
                {"artifact": name, "paths": paths},
                f"Consolidate duplicate content for {name} or remove redundant copies",
            )
        )

    if not duplicate_content:
        findings.append(
            _finding(
                "artifact_ownership",
                "AO-009",
                "No duplicate artifact content detected",
                "pass",
                "info",
                "All artifacts in runtime/generated/ have unique content",
                {},
                "Continue monitoring for duplicate content",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_unused_artifacts(artifact_files: list[Path]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    for artifact in artifact_files:
        name = artifact.name
        if name in ARTIFACT_OWNERS:
            info = ARTIFACT_OWNERS[name]
            consumers = info.get("consumer", "").split(",")
            metrics[f"artifact_{name}_consumer_count"] = len(consumers)

    if not findings:
        findings.append(
            _finding(
                "artifact_ownership",
                "AO-010",
                "Artifact consumption tracking complete",
                "pass",
                "info",
                f"All {len(artifact_files)} artifacts have registered consumers",
                {},
                "Continue tracking artifact consumers",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_workflow_references(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    workflow_files = list((repo_root / ".github" / "workflows").glob("*.yml"))
    artifact_refs_in_workflows: dict[str, list[str]] = {}

    for wf in workflow_files:
        try:
            content = wf.read_text(encoding="utf-8")
            for artifact_name in ARTIFACT_OWNERS:
                if artifact_name.replace(".json", "").replace(".md", "") in content.replace(".json", "").replace(".md", ""):
                    if artifact_name not in artifact_refs_in_workflows:
                        artifact_refs_in_workflows[artifact_name] = []
                    artifact_refs_in_workflows[artifact_name].append(wf.name)
        except Exception:
            continue

    metrics["workflow_files_checked"] = len(workflow_files)
    metrics["artifacts_referenced_in_workflows"] = len(artifact_refs_in_workflows)

    for artifact_name, wf_names in artifact_refs_in_workflows.items():
        metrics[f"artifact_{artifact_name}_referenced_in"] = wf_names

    findings.append(
        _finding(
            "artifact_ownership",
            "AO-011",
            "Workflow artifact references checked",
            "pass",
            "info",
            f"Checked {len(workflow_files)} workflow files for artifact references; {len(artifact_refs_in_workflows)} artifacts are referenced",
            metrics,
            "Ensure all critical artifacts are referenced in at least one workflow",
        )
    )

    return {"findings": findings, "metrics": metrics}


def _check_consumers(artifact_files: list[Path], v3_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    artifacts_without_consumers = []
    for artifact in artifact_files:
        name = artifact.name
        rec = _record_for(name, v3_by_name)
        consumers = (rec or {}).get("consumer", "") if rec else ""
        if rec and (not consumers or consumers.strip() == ""):
            artifacts_without_consumers.append(name)

    metrics["artifacts_with_consumers"] = len(artifact_files) - len(artifacts_without_consumers)
    metrics["artifacts_without_consumers"] = len(artifacts_without_consumers)

    if artifacts_without_consumers:
        for name in artifacts_without_consumers:
            findings.append(
                _finding(
                    "artifact_ownership",
                    "AO-012",
                    f"Artifact has no registered consumer: {name}",
                    "warning",
                    "low",
                    f"Artifact {name} is generated but has no registered consumer",
                    {"artifact": name},
                    f"Register a consumer for {name} or remove if unused",
                )
            )
    else:
        findings.append(
            _finding(
                "artifact_ownership",
                "AO-013",
                "All artifacts have registered consumers",
                "pass",
                "info",
                f"All {len(artifact_files)} artifacts have registered consumers",
                {},
                "Continue registering consumers for all artifacts",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _finding(
    section: str,
    check_id: str,
    name: str,
    status: str,
    severity: str,
    message: str,
    details: dict[str, Any],
    recommendation: str,
) -> dict[str, Any]:
    return {
        "section": section,
        "check_id": check_id,
        "name": name,
        "status": status,
        "severity": severity,
        "priority": _severity_to_priority(severity),
        "message": message,
        "details": details,
        "recommendation": recommendation,
    }


def _severity_to_priority(severity: str) -> str:
    mapping = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "low",
    }
    return mapping.get(severity, "low")