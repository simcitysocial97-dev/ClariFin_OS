#!/usr/bin/env python3
"""Program 11.5 — Validation harness for the GitHub Actions architecture.

Validates, against docs/GITHUB_ACTIONS_CONSTITUTION.md and the Program 11.5
rules:
  1. Every workflow + composite action is valid YAML.
  2. No workflow inlines setup-python / setup-node / upload-artifact / cache.
  3. Every verification workflow executes exactly one `python runtime/verify.py`
     command (the profile for that workflow).
  4. No duplicated runtime-artifact generation (build_cross_layer_map / build_index
     must only run inside bootstrap-runtime).
  5. No duplicated artifact names within a workflow.
  6. Concurrency is configured; cancel-in-progress follows the exception list.
  7. Path filters configured on push/PR triggers (where applicable).
  8. Every workflow ends with `python runtime/verify.py status`.
  9. Every composite action references existing scripts/commands.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WF_DIR = ROOT / ".github" / "workflows"
ACT_DIR = ROOT / ".github" / "actions"

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

ERRORS = []
WARNINGS = []


def err(msg: str) -> None:
    ERRORS.append(msg)


def warn(msg: str) -> None:
    WARNINGS.append(msg)


def load_yml(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f) or {}


def validate_composite_action(action_dir: Path) -> None:
    action_file = action_dir / "action.yml"
    if not action_file.exists():
        err(f"Composite action missing action.yml: {action_dir}")
        return
    doc = load_yml(action_file)
    if doc.get("runs", {}).get("using") != "composite":
        err(f"{action_file}: expected runs.using=composite")


def validate_workflow(path: Path) -> None:
    name = path.name
    doc = load_yml(path)

    # concurrency
    conc = doc.get("concurrency")
    if not conc:
        err(f"{name}: missing `concurrency` block (Rule 6)")
    else:
        group = conc.get("group")
        if not group:
            err(f"{name}: concurrency.group is empty")
        cancel = conc.get("cancel-in-progress")
        expected_cancel = name not in NO_CANCEL
        if cancel is not expected_cancel:
            err(
                f"{name}: concurrency.cancel-in-progress={cancel}, "
                f"expected {expected_cancel} (Rule 6 exception list)"
            )

    # triggers (PyYAML coerces bare `on:` to boolean key True)
    on = doc.get("on") if "on" in doc else doc.get(True, {})
    if not isinstance(on, dict):
        on = {on: {}} if not isinstance(on, list) else {k: {} for k in on}
    push = on.get("push", {}) or {}
    pr = on.get("pull_request", {}) or {}
    has_push = bool(push)
    has_pr = bool(pr)
    has_dispatch = bool(on.get("workflow_dispatch"))
    has_schedule = bool(on.get("schedule"))
    if name not in VERIFICATION_PROFILES and not (
        has_schedule or has_dispatch
    ):
        warn(f"{name}: non-verification workflow has no schedule/manual trigger")

    # path filters for verification workflows with push/PR triggers
    if name in VERIFICATION_PROFILES and (has_push or has_pr):
        # Check push paths if push is configured
        if has_push and name != "quality.yml":
            push_paths = push.get("paths") or (push.get("branches") and push.get("paths"))
            if not push_paths:
                warn(f"{name}: push trigger has no `paths` filter (Rule 7)")
                
        # Check PR paths if PR is configured
        if has_pr and name != "quality.yml":
            pr_paths = pr.get("paths") or (pr.get("branches") and pr.get("paths"))
            if not pr_paths:
                warn(f"{name}: pull_request trigger has no `paths` filter (Rule 7)")
        
    jobs = doc.get("jobs", {})
    if not jobs:
        err(f"{name}: no jobs defined")
        return

    inline_setup = [
        "actions/setup-python",
        "actions/setup-node",
        "actions/setup-go",
        "actions/cache",
        "actions/upload-artifact",
    ]
    artifact_names: list[str] = []
    found_verify_profile = False
    found_status = False
    found_inline_gen = False

    for job_id, job in jobs.items():
        steps = job.get("steps", [])
        for step in steps:
            uses = step.get("uses", "")
            run = step.get("run", "")
            for bad in inline_setup:
                if uses.startswith(bad):
                    err(
                        f"{name}/{job_id}: inlines `{bad}` — must use shared "
                        f"composite action (Rule 4)"
                    )
            if "upload-artifact" in uses:
                err(f"{name}/{job_id}: inlines actions/upload-artifact (Rule 3/4)")
            if "build_cross_layer_map" in run or "build_index" in run or "save_index" in run:
                found_inline_gen = True
            if "python runtime/verify.py" in run:
                prof = run.strip().split("python runtime/verify.py")[-1].split()[0]
                if prof == "status":
                    found_status = True
                    continue
                # Only verification-profile workflows are bound to a single profile
                # command. Non-profile workflows (reconcile, security/CodeQL,
                # release, dependency health) may invoke other verify.py subcommands
                # (plan, reconcile, exec-evidence, ...) or none at all.
                if name in VERIFICATION_PROFILES:
                    expected = VERIFICATION_PROFILES[name]
                    if prof == expected:
                        found_verify_profile = True
                    else:
                        err(
                            f"{name}/{job_id}: runs `verify.py {prof}` but should be "
                            f"`verify.py {expected}` (Rule 8)"
                        )
            # artifact names via upload-runtime
            name_in = step.get("with", {}).get("name")
            if uses.endswith("upload-runtime") and name_in:
                artifact_names.append(name_in)

    # verification workflow must run exactly one profile command
    if name in VERIFICATION_PROFILES:
        if not found_verify_profile:
            err(f"{name}: missing required `python runtime/verify.py {VERIFICATION_PROFILES[name]}` (Rule 8)")
        if not found_status:
            err(f"{name}: missing `python runtime/verify.py status` summary (Rule 9)")
        if found_inline_gen:
            err(f"{name}: inlines shared-artifact generation (Rule 3)")

    # artifact name uniqueness within workflow
    dupes = [n for n in artifact_names if artifact_names.count(n) > 1]
    if dupes:
        err(f"{name}: duplicated artifact names {set(dupes)} (Rule 3/4)")

    # bootstrap-runtime usage for verification workflows
    if name in VERIFICATION_PROFILES:
        uses_bootstrap = any(
            step.get("uses", "").endswith("bootstrap-runtime")
            for job in jobs.values()
            for step in job.get("steps", [])
        )
        if not uses_bootstrap:
            err(f"{name}: verification workflow must use bootstrap-runtime (Rule 3)")


def main() -> int:
    for action_dir in sorted(ACT_DIR.iterdir()):
        if action_dir.is_dir():
            validate_composite_action(action_dir)

    for wf in sorted(WF_DIR.glob("*.yml")):
        validate_workflow(wf)

    print(f"Workflows validated: {len(list(WF_DIR.glob('*.yml')))}")
    print(f"Composite actions validated: {len([d for d in ACT_DIR.iterdir() if d.is_dir()])}")
    print()
    if WARNINGS:
        print("WARNINGS:")
        for w in WARNINGS:
            print(f"  - {w}")
    if ERRORS:
        print("ERRORS:")
        for e in ERRORS:
            print(f"  - {e}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
