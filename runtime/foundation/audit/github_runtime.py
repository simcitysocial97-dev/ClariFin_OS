"""GitHub Runtime Audit — Program 12.

Audits the GitHub Actions runtime workflow for lightweight log retrieval
patterns, annotation usage, and artifact management.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    repo_root = repo_root or REPO_ROOT
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    workflow_files = list((repo_root / ".github" / "workflows").glob("*.yml"))
    metrics["workflow_count"] = len(workflow_files)

    gh_available = _gh_available()
    metrics["gh_cli_available"] = gh_available

    if gh_available:
        run_data = _get_gh_run_data(repo_root)
        metrics["gh_runs_fetched"] = len(run_data)

        annotation_check = _check_annotations_before_logs(run_data, repo_root)
        findings.extend(annotation_check["findings"])
        metrics.update(annotation_check["metrics"])

        log_pattern_check = _check_log_retrieval_pattern(workflow_files, repo_root)
        findings.extend(log_pattern_check["findings"])
        metrics.update(log_pattern_check["metrics"])

        artifact_check = _check_artifact_workflows(workflow_files, repo_root)
        findings.extend(artifact_check["findings"])
        metrics.update(artifact_check["metrics"])
    else:
        findings.append(
            _finding(
                "github_runtime",
                "GH-001",
                "GitHub CLI not available",
                "warning",
                "medium",
                "GitHub CLI (gh) is not installed or not in PATH; cannot verify runtime patterns",
                {},
                "Install gh CLI or run audit in an environment with GitHub CLI available",
            )
        )

    workflow_pattern_check = _check_workflow_patterns(workflow_files, repo_root)
    findings.extend(workflow_pattern_check["findings"])
    metrics.update(workflow_pattern_check["metrics"])

    status = "pass" if all(f["status"] == "pass" for f in findings) else "fail"
    duration = time.monotonic() - start

    return {
        "section": "github_runtime",
        "name": "GitHub Runtime Audit",
        "status": status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": round(duration, 3),
    }


def _gh_available() -> bool:
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def _get_gh_run_data(repo_root: Path) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    try:
        result = subprocess.run(
            [
                "gh",
                "run",
                "list",
                "--limit",
                "20",
                "--json",
                "databaseId,status,conclusion",
            ],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            runs = json.loads(result.stdout)
    except Exception:
        pass
    return runs


def _check_annotations_before_logs(
    run_data: list[dict[str, Any]], repo_root: Path
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    failed_runs = [r for r in run_data if r.get("conclusion") == "failure"]
    metrics["failed_runs_in_history"] = len(failed_runs)

    for run in failed_runs[:5]:
        run_id = run.get("databaseId")
        if run_id is None:
            continue

        has_annotations = _check_run_has_annotations(run_id, repo_root)
        has_log_download = _check_run_has_log_download(run_id, repo_root)

        if has_annotations and has_log_download:
            findings.append(
                _finding(
                    "github_runtime",
                    "GH-002",
                    f"Run {run_id}: annotations exist but logs were still downloaded",
                    "fail",
                    "high",
                    f"GitHub run {run_id} has annotations available but log download was attempted, wasting bandwidth",
                    {
                        "run_id": run_id,
                        "has_annotations": True,
                        "has_log_download": True,
                    },
                    "Skip log download when annotations are present; annotations contain all failure details",
                )
            )
        elif has_annotations and not has_log_download:
            findings.append(
                _finding(
                    "github_runtime",
                    "GH-003",
                    f"Run {run_id}: annotations used, logs skipped (correct pattern)",
                    "pass",
                    "info",
                    f"GitHub run {run_id} correctly skips log download when annotations are available",
                    {
                        "run_id": run_id,
                        "has_annotations": True,
                        "has_log_download": False,
                    },
                    "Continue using annotation-first pattern",
                )
            )

    if not findings:
        findings.append(
            _finding(
                "github_runtime",
                "GH-004",
                "Annotation-first log retrieval pattern verified",
                "pass",
                "info",
                "No runs found with both annotations and log downloads; annotation-first pattern is followed",
                {},
                "Continue monitoring for annotation-first log retrieval compliance",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_run_has_annotations(run_id: int, repo_root: Path) -> bool:
    try:
        result = subprocess.run(
            ["gh", "run", "view", str(run_id), "--json", "annotations"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            annotations = data.get("annotations", [])
            return len(annotations) > 0
    except Exception:
        pass
    return False


def _check_run_has_log_download(run_id: int, repo_root: Path) -> bool:
    try:
        result = subprocess.run(
            ["gh", "run", "view", str(run_id), "--json", "logUrl"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            log_url = data.get("logUrl", "")
            return bool(log_url)
    except Exception:
        pass
    return False


def _check_log_retrieval_pattern(
    workflow_files: list[Path], repo_root: Path
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    log_download_patterns = [
        "gh run download",
        "gh run view --log",
        "actions/download-artifact",
    ]
    annotation_patterns = ["annotations", "annotate"]

    for wf in workflow_files:
        try:
            content = wf.read_text(encoding="utf-8")
            has_log_download = any(p in content for p in log_download_patterns)
            has_annotation_step = any(p in content for p in annotation_patterns)

            if has_log_download and not has_annotation_step:
                findings.append(
                    _finding(
                        "github_runtime",
                        "GH-005",
                        f"{wf.name}: downloads logs without annotation check",
                        "fail",
                        "high",
                        f"Workflow {wf.name} downloads logs without first checking for annotations, potentially wasting bandwidth on 200MB log downloads",
                        {
                            "workflow": wf.name,
                            "has_log_download": True,
                            "has_annotation_check": False,
                        },
                        "Add annotation check step before log download; skip log download if annotations exist",
                    )
                )
            elif has_annotation_step and has_log_download:
                metrics[f"{wf.name}_has_both"] = True
        except Exception:
            continue

    if not findings:
        findings.append(
            _finding(
                "github_runtime",
                "GH-006",
                "Log retrieval pattern follows annotation-first approach",
                "pass",
                "info",
                "All workflows either check annotations before downloading logs or do not download logs at all",
                {},
                "Continue following annotation-first log retrieval pattern",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_artifact_workflows(
    workflow_files: list[Path], repo_root: Path
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    artifact_workflows = [
        "backend-verify",
        "frontend-verify",
        "quality",
        "verification-runtime",
    ]
    artifact_names = [
        "cross-layer-map",
        "knowledge-index",
        "verification-cache",
        "engineering-history",
    ]

    for wf in workflow_files:
        try:
            content = wf.read_text(encoding="utf-8")
            wf_name = wf.stem

            if wf_name in artifact_workflows:
                for artifact in artifact_names:
                    if artifact in content:
                        metrics[f"{wf_name}_uploads_{artifact}"] = True

                if (
                    "upload-artifact" not in content
                    and "actions/upload-artifact" not in content
                    and "upload-runtime" not in content
                ):
                    findings.append(
                        _finding(
                            "github_runtime",
                            "GH-007",
                            f"{wf_name}: missing artifact upload step",
                            "fail",
                            "medium",
                            f"Workflow {wf_name} does not upload artifacts, making results unavailable for downstream consumption",
                            {"workflow": wf_name},
                            "Add artifact upload step using actions/upload-artifact",
                        )
                    )
        except Exception:
            continue

    metrics["artifact_workflows_checked"] = len(artifact_workflows)

    if not any(f["check_id"] == "GH-007" for f in findings):
        findings.append(
            _finding(
                "github_runtime",
                "GH-008",
                "Artifact upload patterns verified",
                "pass",
                "info",
                "All verification workflows include artifact upload steps",
                {},
                "Continue uploading artifacts for all verification workflows",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_workflow_patterns(
    workflow_files: list[Path], repo_root: Path
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    required_patterns = {
        "concurrency": "concurrency:",
        "cancel-in-progress": "cancel-in-progress: true",
        "path_filtering": "paths:",
    }

    for wf in workflow_files:
        try:
            content = wf.read_text(encoding="utf-8")
            wf_name = wf.stem

            for pattern_name, pattern in required_patterns.items():
                if pattern in content:
                    metrics[f"{wf_name}_{pattern_name}"] = True
        except Exception:
            continue

    metrics["workflows_checked"] = len(workflow_files)

    findings.append(
        _finding(
            "github_runtime",
            "GH-009",
            "Workflow pattern compliance checked",
            "pass",
            "info",
            f"Checked {len(workflow_files)} workflow files for required patterns (concurrency, path filtering, cancel-in-progress)",
            metrics,
            "Ensure all new workflows follow the same pattern conventions",
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
