"""GitHub Actions Audit — Program 12.

Audits every workflow file, composite action, trigger, artifact, cache,
path filter, concurrency group, upload/download, profile, runtime command,
retention policy, summary, bootstrap, and validator.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
WF_DIR = REPO_ROOT / ".github" / "workflows"
ACT_DIR = REPO_ROOT / ".github" / "actions"
VALIDATE_SCRIPT = REPO_ROOT / ".github" / "scripts" / "validate_actions.py"

VERIFICATION_PROFILES = {
    "quality.yml": "quick",
    "backend-verify.yml": "backend",
    "frontend-verify.yml": "frontend",
    "verification-runtime.yml": "runtime",
    "golden.yml": "golden",
    "mutation.yml": "mutation",
    "playwright.yml": "playwright",
}

NO_CANCEL = {"golden.yml", "mutation.yml", "release.yml"}

INLINE_SETUP_ACTIONS = [
    "actions/setup-python",
    "actions/setup-node",
    "actions/setup-go",
    "actions/cache",
    "actions/upload-artifact",
]


def _load_yaml(path: Path) -> dict[str, Any]:
    import yaml

    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _audit_workflow(path: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    name = path.name
    wf = _load_yaml(path)

    on = wf.get("on") if "on" in wf else wf.get(True, {})
    if not isinstance(on, dict):
        on = {on: {}} if not isinstance(on, list) else {k: {} for k in on}

    push = on.get("push", {}) or {}
    pr = on.get("pull_request", {}) or {}
    has_push = bool(push)
    has_pr = bool(pr)
    has_dispatch = bool(on.get("workflow_dispatch"))
    has_schedule = bool(on.get("schedule"))

    if name not in VERIFICATION_PROFILES and not (has_schedule or has_dispatch):
        findings.append(
            {
                "section": "github_actions",
                "check_id": f"gh-trigger-{name}",
                "name": f"{name}: non-verification workflow has no schedule/manual trigger",
                "status": "warning",
                "severity": "medium",
                "priority": "medium",
                "message": "Workflow has no schedule or workflow_dispatch trigger",
                "details": {
                    "has_push": has_push,
                    "has_pr": has_pr,
                    "has_schedule": has_schedule,
                    "has_dispatch": has_dispatch,
                },
                "recommendation": "Add a schedule or workflow_dispatch trigger for operational workflows",
            }
        )

    if name in VERIFICATION_PROFILES and has_push:
        paths = push.get("paths") or (push.get("branches") and push.get("paths"))
        if name != "quality.yml" and not paths:
            findings.append(
                {
                    "section": "github_actions",
                    "check_id": f"gh-pathfilter-{name}",
                    "name": f"{name}: push trigger has no paths filter",
                    "status": "fail",
                    "severity": "high",
                    "priority": "high",
                    "message": "Verification workflow push trigger missing `paths` filter",
                    "details": {"trigger": "push", "workflow": name},
                    "recommendation": "Add `paths` filter to the push trigger",
                }
            )

    conc = wf.get("concurrency")
    if not conc:
        findings.append(
            {
                "section": "github_actions",
                "check_id": f"gh-concurrency-{name}",
                "name": f"{name}: missing concurrency block",
                "status": "fail",
                "severity": "high",
                "priority": "high",
                "message": "Workflow is missing the `concurrency` block",
                "details": {"workflow": name},
                "recommendation": "Add a concurrency block with group and cancel-in-progress",
            }
        )
    else:
        group = conc.get("group")
        if not group:
            findings.append(
                {
                    "section": "github_actions",
                    "check_id": f"gh-concurrency-group-{name}",
                    "name": f"{name}: concurrency.group is empty",
                    "status": "fail",
                    "severity": "high",
                    "priority": "high",
                    "message": "concurrency.group is empty or missing",
                    "details": {"workflow": name},
                    "recommendation": "Set concurrency.group to `${{ github.workflow }}-${{ github.ref }}`",
                }
            )
        else:
            findings.append(
                {
                    "section": "github_actions",
                    "check_id": f"gh-concurrency-group-{name}",
                    "name": f"{name}: concurrency.group configured",
                    "status": "pass",
                    "severity": "info",
                    "priority": "low",
                    "message": f"concurrency.group = '{group}'",
                    "details": {"group": group},
                    "recommendation": "",
                }
            )

        cancel = conc.get("cancel-in-progress")
        expected_cancel = name not in NO_CANCEL
        if cancel is not expected_cancel:
            findings.append(
                {
                    "section": "github_actions",
                    "check_id": f"gh-concurrency-cancel-{name}",
                    "name": f"{name}: concurrency.cancel-in-progress mismatch",
                    "status": "fail",
                    "severity": "high",
                    "priority": "high",
                    "message": f"cancel-in-progress={cancel}, expected {expected_cancel} (Rule 6 exception list)",
                    "details": {
                        "workflow": name,
                        "actual": cancel,
                        "expected": expected_cancel,
                    },
                    "recommendation": f"Set cancel-in-progress to {expected_cancel} for {name}",
                }
            )
        else:
            findings.append(
                {
                    "section": "github_actions",
                    "check_id": f"gh-concurrency-cancel-{name}",
                    "name": f"{name}: concurrency.cancel-in-progress correct",
                    "status": "pass",
                    "severity": "info",
                    "priority": "low",
                    "message": f"cancel-in-progress={cancel} matches exception list",
                    "details": {"workflow": name, "cancel_in_progress": cancel},
                    "recommendation": "",
                }
            )

    jobs = wf.get("jobs", {})
    if not jobs:
        findings.append(
            {
                "section": "github_actions",
                "check_id": f"gh-jobs-{name}",
                "name": f"{name}: no jobs defined",
                "status": "fail",
                "severity": "critical",
                "priority": "critical",
                "message": "Workflow has no jobs defined",
                "details": {"workflow": name},
                "recommendation": "Add at least one job to the workflow",
            }
        )
        return findings

    artifact_names: list[str] = []
    found_verify_profile = False
    found_status = False
    found_inline_gen = False
    found_bootstrap = False

    for job_id, job in jobs.items():
        steps = job.get("steps", [])
        for step in steps:
            uses = step.get("uses", "")
            run = step.get("run", "")

            for bad in INLINE_SETUP_ACTIONS:
                if uses.startswith(bad):
                    findings.append(
                        {
                            "section": "github_actions",
                            "check_id": f"gh-inline-setup-{name}-{job_id}",
                            "name": f"{name}/{job_id}: inlines `{bad}`",
                            "status": "fail",
                            "severity": "high",
                            "priority": "high",
                            "message": f"Inlines `{bad}` — must use shared composite action (Rule 4)",
                            "details": {"workflow": name, "job": job_id, "action": bad},
                            "recommendation": "Replace with the corresponding shared composite action in .github/actions/",
                        }
                    )

            if "upload-artifact" in uses:
                findings.append(
                    {
                        "section": "github_actions",
                        "check_id": f"gh-inline-upload-{name}-{job_id}",
                        "name": f"{name}/{job_id}: inlines actions/upload-artifact",
                        "status": "fail",
                        "severity": "high",
                        "priority": "high",
                        "message": "Inlines actions/upload-artifact — must use upload-runtime composite action (Rule 3/4)",
                        "details": {"workflow": name, "job": job_id},
                        "recommendation": "Use ./.github/actions/upload-runtime instead",
                    }
                )

            if (
                "build_cross_layer_map" in run
                or "build_index" in run
                or "save_index" in run
            ):
                found_inline_gen = True

            if "python runtime/verify.py" in run:
                parts = run.strip().split("python runtime/verify.py")
                if len(parts) > 1:
                    prof = parts[-1].split()[0] if parts[-1].strip() else ""
                    if prof == "status":
                        found_status = True
                    elif name in VERIFICATION_PROFILES:
                        expected = VERIFICATION_PROFILES[name]
                        if prof == expected:
                            found_verify_profile = True
                        else:
                            findings.append(
                                {
                                    "section": "github_actions",
                                    "check_id": f"gh-profile-{name}-{job_id}",
                                    "name": f"{name}/{job_id}: wrong verification profile",
                                    "status": "fail",
                                    "severity": "high",
                                    "priority": "high",
                                    "message": f"Runs `verify.py {prof}` but should be `verify.py {expected}` (Rule 8)",
                                    "details": {
                                        "workflow": name,
                                        "job": job_id,
                                        "actual": prof,
                                        "expected": expected,
                                    },
                                    "recommendation": f"Change to `python runtime/verify.py {expected}`",
                                }
                            )

            if uses.endswith("upload-runtime"):
                name_in = step.get("with", {}).get("name")
                if name_in:
                    artifact_names.append(name_in)

            if uses.endswith("bootstrap-runtime"):
                found_bootstrap = True

            if uses.endswith("upload-runtime"):
                retention = step.get("with", {}).get("retention-days")
                if retention is not None:
                    findings.append(
                        {
                            "section": "github_actions",
                            "check_id": f"gh-retention-{name}-{job_id}-{name_in}",
                            "name": f"{name}/{job_id}: artifact {name_in} retention-days={retention}",
                            "status": "pass",
                            "severity": "info",
                            "priority": "low",
                            "message": f"Artifact '{name_in}' has retention-days={retention}",
                            "details": {
                                "workflow": name,
                                "job": job_id,
                                "artifact": name_in,
                                "retention_days": retention,
                            },
                            "recommendation": "",
                        }
                    )

            cache_uses = step.get("uses", "")
            if "actions/cache" in cache_uses:
                cache_key = step.get("with", {}).get("key", "")
                findings.append(
                    {
                        "section": "github_actions",
                        "check_id": f"gh-cache-{name}-{job_id}",
                        "name": f"{name}/{job_id}: cache configured",
                        "status": "pass",
                        "severity": "info",
                        "priority": "low",
                        "message": "Cache action found with key pattern",
                        "details": {
                            "workflow": name,
                            "job": job_id,
                            "cache_key": cache_key[:80] if cache_key else "",
                        },
                        "recommendation": "",
                    }
                )

    if name in VERIFICATION_PROFILES:
        if not found_verify_profile:
            expected = VERIFICATION_PROFILES[name]
            findings.append(
                {
                    "section": "github_actions",
                    "check_id": f"gh-profile-missing-{name}",
                    "name": f"{name}: missing required verification profile command",
                    "status": "fail",
                    "severity": "high",
                    "priority": "high",
                    "message": f"Missing `python runtime/verify.py {expected}` (Rule 8)",
                    "details": {"workflow": name, "expected_profile": expected},
                    "recommendation": f"Add a step running `python runtime/verify.py {expected}`",
                }
            )

        if not found_status:
            findings.append(
                {
                    "section": "github_actions",
                    "check_id": f"gh-status-missing-{name}",
                    "name": f"{name}: missing verify.py status summary",
                    "status": "fail",
                    "severity": "high",
                    "priority": "high",
                    "message": "Missing `python runtime/verify.py status` summary (Rule 9)",
                    "details": {"workflow": name},
                    "recommendation": "Add a step running `python runtime/verify.py status` to append to GITHUB_STEP_SUMMARY",
                }
            )

        if found_inline_gen:
            findings.append(
                {
                    "section": "github_actions",
                    "check_id": f"gh-inline-gen-{name}",
                    "name": f"{name}: inlines shared-artifact generation",
                    "status": "fail",
                    "severity": "high",
                    "priority": "high",
                    "message": "Inlines shared-artifact generation (build_cross_layer_map / build_index) (Rule 3)",
                    "details": {"workflow": name},
                    "recommendation": "Remove inline generation; let bootstrap-runtime handle it",
                }
            )

        if not found_bootstrap:
            findings.append(
                {
                    "section": "github_actions",
                    "check_id": f"gh-bootstrap-{name}",
                    "name": f"{name}: verification workflow must use bootstrap-runtime",
                    "status": "fail",
                    "severity": "high",
                    "priority": "high",
                    "message": "Verification workflow must use bootstrap-runtime composite action (Rule 3)",
                    "details": {"workflow": name},
                    "recommendation": "Add a step using ./.github/actions/bootstrap-runtime",
                }
            )

    dupes = [n for n in artifact_names if artifact_names.count(n) > 1]
    if dupes:
        findings.append(
            {
                "section": "github_actions",
                "check_id": f"gh-artifact-dupe-{name}",
                "name": f"{name}: duplicated artifact names",
                "status": "fail",
                "severity": "high",
                "priority": "high",
                "message": f"Duplicated artifact names: {set(dupes)} (Rule 3/4)",
                "details": {"workflow": name, "duplicates": list(set(dupes))},
                "recommendation": "Ensure each artifact name is unique within the workflow",
            }
        )

    summary_found = False
    for job_id, job in jobs.items():
        for step in job.get("steps", []):
            run = step.get("run", "")
            if "GITHUB_STEP_SUMMARY" in run:
                summary_found = True
                findings.append(
                    {
                        "section": "github_actions",
                        "check_id": f"gh-summary-{name}-{job_id}",
                        "name": f"{name}/{job_id}: job summary configured",
                        "status": "pass",
                        "severity": "info",
                        "priority": "low",
                        "message": "Job summary step found (GITHUB_STEP_SUMMARY)",
                        "details": {"workflow": name, "job": job_id},
                        "recommendation": "",
                    }
                )
                break

    if not summary_found and name in VERIFICATION_PROFILES:
        findings.append(
            {
                "section": "github_actions",
                "check_id": f"gh-summary-missing-{name}",
                "name": f"{name}: missing job summary step",
                "status": "fail",
                "severity": "medium",
                "priority": "medium",
                "message": "No step appends to GITHUB_STEP_SUMMARY (Rule 9)",
                "details": {"workflow": name},
                "recommendation": "Add a summary step that appends to $GITHUB_STEP_SUMMARY",
            }
        )

    return findings


def _audit_composite_action(path: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    action_name = path.name
    action_file = path / "action.yml"

    if not action_file.exists():
        findings.append(
            {
                "section": "github_actions",
                "check_id": f"gh-action-{action_name}-missing",
                "name": f"Composite action {action_name}: missing action.yml",
                "status": "fail",
                "severity": "critical",
                "priority": "critical",
                "message": "Composite action directory missing action.yml",
                "details": {"action_dir": str(action_file)},
                "recommendation": "Add action.yml to the composite action directory",
            }
        )
        return findings

    doc = _load_yaml(action_file)
    runs = doc.get("runs", {})
    if runs.get("using") != "composite":
        findings.append(
            {
                "section": "github_actions",
                "check_id": f"gh-action-{action_name}-type",
                "name": f"Composite action {action_name}: runs.using != composite",
                "status": "fail",
                "severity": "high",
                "priority": "high",
                "message": f"Expected runs.using=composite, got '{runs.get('using')}'",
                "details": {
                    "action_dir": str(action_file),
                    "runs_using": runs.get("using"),
                },
                "recommendation": "Set runs.using to 'composite' in action.yml",
            }
        )
    else:
        findings.append(
            {
                "section": "github_actions",
                "check_id": f"gh-action-{action_name}-type",
                "name": f"Composite action {action_name}: valid composite type",
                "status": "pass",
                "severity": "info",
                "priority": "low",
                "message": "action.yml has runs.using=composite",
                "details": {},
                "recommendation": "",
            }
        )

    inputs = doc.get("inputs", {})
    findings.append(
        {
            "section": "github_actions",
            "check_id": f"gh-action-{action_name}-inputs",
            "name": f"Composite action {action_name}: inputs defined",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"Action has {len(inputs)} input(s)",
            "details": {"input_count": len(inputs), "inputs": list(inputs.keys())},
            "recommendation": "",
        }
    )

    steps = runs.get("steps", [])
    has_setup_python = any(
        s.get("uses", "").endswith("setup-python-runtime") for s in steps
    )
    has_setup_node = any(
        s.get("uses", "").endswith("setup-node-runtime") for s in steps
    )
    has_upload = any(s.get("uses", "").endswith("upload-runtime") for s in steps)
    has_cache = any("actions/cache" in s.get("uses", "") for s in steps)

    findings.append(
        {
            "section": "github_actions",
            "check_id": f"gh-action-{action_name}-steps",
            "name": f"Composite action {action_name}: step composition",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"Steps: setup-python={has_setup_python}, setup-node={has_setup_node}, upload-runtime={has_upload}, cache={has_cache}",
            "details": {
                "step_count": len(steps),
                "has_setup_python": has_setup_python,
                "has_setup_node": has_setup_node,
                "has_upload_runtime": has_upload,
                "has_cache": has_cache,
            },
            "recommendation": "",
        }
    )

    return findings


def _reuse_validate_actions() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    if not VALIDATE_SCRIPT.exists():
        findings.append(
            {
                "section": "github_actions",
                "check_id": "gh-validate-script-missing",
                "name": "validate_actions.py script exists",
                "status": "fail",
                "severity": "critical",
                "priority": "critical",
                "message": f"validate_actions.py not found at {VALIDATE_SCRIPT}",
                "details": {},
                "recommendation": "Ensure .github/scripts/validate_actions.py exists",
            }
        )
        return findings

    proc = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO_ROOT),
    )

    findings.append(
        {
            "section": "github_actions",
            "check_id": "gh-validate-script-exit",
            "name": "validate_actions.py execution",
            "status": "pass" if proc.returncode == 0 else "fail",
            "severity": "info",
            "priority": "low",
            "message": f"validate_actions.py exited with code {proc.returncode}",
            "details": {
                "returncode": proc.returncode,
                "stdout": proc.stdout[:500],
                "stderr": proc.stderr[:500],
            },
            "recommendation": (
                ""
                if proc.returncode == 0
                else "Fix validation errors reported by validate_actions.py"
            ),
        }
    )

    return findings


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    root = repo_root or REPO_ROOT
    wf_dir = root / ".github" / "workflows"
    act_dir = root / ".github" / "actions"

    workflow_files = sorted(wf_dir.glob("*.yml")) if wf_dir.exists() else []
    action_dirs = sorted(act_dir.iterdir()) if act_dir.exists() else []

    workflow_count = 0
    action_count = 0

    for wf_path in workflow_files:
        workflow_count += 1
        wf_findings = _audit_workflow(wf_path)
        findings.extend(wf_findings)

    for action_dir in action_dirs:
        if not action_dir.is_dir():
            continue
        action_count += 1
        act_findings = _audit_composite_action(action_dir)
        findings.extend(act_findings)

    validate_findings = _reuse_validate_actions()
    findings.extend(validate_findings)

    all_pass = all(f["status"] == "pass" for f in findings)
    overall_status = "pass" if all_pass else "fail"

    metrics = {
        "workflows_audited": workflow_count,
        "composite_actions_audited": action_count,
        "total_findings": len(findings),
        "failures": sum(1 for f in findings if f["status"] == "fail"),
        "warnings": sum(1 for f in findings if f["status"] == "warning"),
        "passes": sum(1 for f in findings if f["status"] == "pass"),
    }

    duration = time.monotonic() - start
    return {
        "section": "github_actions",
        "name": "GitHub Actions Audit",
        "status": overall_status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": duration,
    }
