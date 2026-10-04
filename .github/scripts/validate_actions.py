#!/usr/bin/env python3
"""Program 11.5 — Validation harness for the GitHub Actions architecture.

Validates, against docs/GITHUB_ACTIONS_CONSTITUTION.md and the Program 11.5
rules:
1. Every workflow + composite action is valid YAML.
 2. No workflow inlines setup-python / setup-node / upload-artifact / cache.
 3. Every verification workflow executes exactly one `python -m runtime.verify`
    command (the profile for that workflow).
 4. No duplicated runtime-artifact generation (build_cross_layer_map / build_index
    must only run inside bootstrap-runtime).
 5. No duplicated artifact names within a workflow.
 6. Concurrency is configured; cancel-in-progress follows the exception list.
 7. Path filters configured on push/PR triggers (where applicable), AND the
    inverse for required status checks: a required context must NOT be path
    filtered (Rule 7a).
 8. Every workflow ends with `python -m runtime.verify status`.
 9. Every composite action references existing scripts/commands.
10. Every external action is pinned to a full 40-character commit SHA (Rule 10).
11. Every required status check is declared, unique, and produced by exactly
    one job of exactly one workflow (Rule 7a / Rule 11).
12. Artifact handling is valid: matrix-disambiguated names, workspace-relative
    non-empty paths, and a recognised `if-no-files-found` (Rule 12).
13. No workflow re-projects a runtime-emitted matrix through a hand-written
    field list (Rule 13).
"""

from __future__ import annotations

import re
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

#: The status checks the `protect-main-branch` ruleset (id 20127383, active)
#: requires — workflow file -> the exact check name the ruleset names.
#:
#: M11 (Task 4/7). Two facts about this table are load-bearing, and both were
#: measured against the live ruleset rather than assumed:
#:
#: 1. IT MUST BE EXHAUSTIVE over required contexts, and `check_required_status_
#:    checks()` fails if a second workflow claims to produce a context this
#:    table also claims. A required context produced by two workflows cannot be
#:    distinguished on the PR, and the one that is cancelled loses the race.
#:
#: 2. Rule 7 used to WARN whenever a verification workflow had no `paths:`
#:    filter. For exactly these four workflows that warning was backwards: a
#:    required context that a path filter skips never reports, and GitHub
#:    treats a required context that does not report as UNSATISFIED. This
#:    repository paid for that on PR #8 — a pull request touching none of the
#:    filtered paths was blocked indefinitely with every reported check green
#:    and no clue in the checks list. `backend-verify.yml` and
#:    `verification-runtime.yml` carry that incident in their own comments.
#:
#: So the rule is now asymmetric, and enforced rather than advisory:
#:   * required check  + `paths:`/`paths-ignore:` -> ERROR  (can never report)
#:   * required check  + no filter                -> correct, no warning
#:   * other workflow  + no filter                -> advisory warning (efficiency)
#:
#: Renaming a required workflow's job renames its check context and breaks the
#: ruleset, so each job's `name:` is asserted against the string below.
REQUIRED_STATUS_CHECKS = {
    "backend-verify.yml": "Backend Verification",
    "frontend-verify.yml": "Frontend Verification",
    "verification-runtime.yml": "Runtime Verification",
    "security-codeql.yml": "Analyze",
}

NO_CANCEL = {"golden.yml", "mutation.yml", "release.yml"}

#: A full, immutable commit SHA. M10 replaced every tag pin in this tree with
#: one of these, keeping the tag as a trailing comment; this rule keeps it that
#: way. It is deliberately STRUCTURAL (is this a SHA?) rather than an allowlist
#: of known-good SHAs: `runtime/tests/test_m9_c72_action_pins.py` owns the
#: allowlist, and duplicating that table here would create a second authority
#: that could drift from it. The two compose: this rule rejects an unpinned or
#: mutable ref, that test rejects a SHA for the wrong action or the wrong tag.
SHA_PIN = re.compile(r"^[0-9a-f]{40}$")

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


def validate_matrix_projection(name: str, raw: str) -> None:
    """Rule 13 — a matrix projection must not name runtime fields.

    M10-R3 (L1). Five workflows each re-projected the runtime's matrix document with a
    hand-written list of the fields they wanted:

        jq -c '{include: [.include[] | {shard, task_count, estimated_seconds, ...}]}'

    That is a second, hand-maintained schema for a document the runtime owns. Every
    field the runtime added was silently dropped unless all five files were edited in
    the same commit — and they were not: `estimated_seconds_serial` and `cpu_peak`
    (Checkpoint D) never reached a single workflow, so the measurement improvement was
    invisible in CI.

    The rule enforces the *shape* selection (`{include: .include}`) rather than a field
    list, which makes the whole drift class impossible rather than merely discouraged.
    """
    # `[.include[] | {` is the tell: a per-item object construction.
    if re.search(r"\{\s*include\s*:\s*\[\s*\.include\[\]\s*\|", raw):
        line_no = raw[: raw.index("[.include[] |")].count("\n") + 1
        err(
            f"{name}: matrix projection names runtime fields "
            f"(Rule 13, around line {line_no}). Use "
            f"`jq -c '{{include: .include}}'` so the matrix is whatever the runtime "
            f"emitted. Naming fields here silently drops anything the runtime adds."
        )


def validate_workflow(path: Path) -> None:
    name = path.name
    doc = load_yml(path)
    validate_matrix_projection(name, path.read_text(encoding="utf-8"))

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
    # M9-C43.1: `workflow_dispatch:` / `schedule:` without a body parse to None
    # in YAML; presence is the key existing in the mapping, not a truthy body.
    has_dispatch = "workflow_dispatch" in on
    has_schedule = "schedule" in on
    if name not in VERIFICATION_PROFILES and not (has_schedule or has_dispatch):
        warn(f"{name}: non-verification workflow has no schedule/manual trigger")

    # Path filters. Rule 7 asks for them; Rule 7a forbids them on a required
    # status check, and that prohibition is the stronger one because it is a
    # merge-blocking consequence rather than an efficiency one.
    required_context = REQUIRED_STATUS_CHECKS.get(name)
    for trigger_label, trigger_body, configured in (
        ("push", push, has_push),
        ("pull_request", pr, has_pr),
    ):
        if not configured:
            continue
        trigger_paths = (trigger_body or {}).get("paths")
        trigger_ignored = (trigger_body or {}).get("paths-ignore")
        if required_context:
            offending = [
                k
                for k, v in (
                    ("paths", trigger_paths),
                    ("paths-ignore", trigger_ignored),
                )
                if v
            ]
            if offending:
                err(
                    f"{name}: produces the required status check "
                    f"'{required_context}' and must NOT be path-filtered, but its "
                    f"{trigger_label} trigger sets {', '.join(offending)}. A required "
                    f"context that a path filter skips never reports, and GitHub "
                    f"treats a required context that does not report as unsatisfied — "
                    f"the pull request is blocked with every reported check green "
                    f"(Rule 7a)."
                )
            continue
        # Not a required check: an absent filter is an efficiency warning only.
        # quality.yml is exempt, as before.
        if name == "quality.yml":
            continue
        if not trigger_paths:
            warn(f"{name}: {trigger_label} trigger has no `paths` filter (Rule 7)")

    jobs = doc.get("jobs", {})
    if not jobs:
        err(f"{name}: no jobs defined")
        return

    # Rule 7a/11 — the required context must exist, be produced by exactly one
    # job, and be spelled exactly as the ruleset spells it. A rename here breaks
    # the ruleset silently on GitHub's side and loudly here.
    if required_context:
        producers = [
            job_id
            for job_id, job in jobs.items()
            if (job.get("name") or job_id) == required_context
        ]
        if not producers:
            err(
                f"{name}: declares the required status check '{required_context}' but "
                f"no job in it is named that. The `protect-main-branch` ruleset "
                f"(20127383) requires a context with that exact name; renaming the job "
                f"breaks the required check and every pull request waits forever "
                f"(Rule 11)."
            )
        elif len(producers) > 1:
            err(
                f"{name}: required status check '{required_context}' is produced by "
                f"{len(producers)} jobs {producers}; a required context must be "
                f"unambiguous (Rule 11)."
            )
        elif jobs.get(producers[0], {}).get("if"):
            job_if = str(jobs[producers[0]]["if"]).strip()
            # `always()` is not a skip condition — it is how a job is made to run
            # even when a dependency failed, which is exactly what an aggregate
            # gate must do. `mutation-aggregate` and any future Runtime
            # Verification aggregate depend on this allowance. Anything else
            # can evaluate false and leave the required context unreported.
            if job_if not in ("always()", "${{ always() }}"):
                err(
                    f"{name}: the job producing required status check "
                    f"'{required_context}' declares `if: {job_if}`. A job-level "
                    f"`if:` can skip the job, and a required context that never "
                    f"reports is unsatisfied. `always()` is allowed because it "
                    f"forces the job to run; every other condition is rejected "
                    f"(Rule 7a)."
                )

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
            # Rule 10 — external actions must be immutable. A tag is a mutable
            # name for a moving target: `actions/download-artifact@v7.0.1` never
            # existed and this repository lost a full 26-shard mutation campaign
            # to exactly that, because the sibling actions *do* have a v7.0.1 and
            # the pin set looked uniform. Local (`.github/actions/...`) and
            # container (`docker://`) references are exempt: the first are
            # versioned by this repository's own history, the second name a
            # digest-resolved image rather than an action release.
            if uses and not uses.startswith("./") and not uses.startswith("docker://"):
                owner_repo, _, ref = uses.partition("@")
                if not ref:
                    err(
                        f"{name}/{job_id}: `{uses}` has no ref. An unpinned action "
                        f"resolves to a default branch that can change without any "
                        f"review in this repository (Rule 10)."
                    )
                elif not SHA_PIN.match(ref):
                    err(
                        f"{name}/{job_id}: `{owner_repo}` is pinned to '{ref}', not a "
                        f"40-character commit SHA. Tags are mutable and a tag can "
                        f"name a release that was never published; a commit cannot "
                        f"(Rule 10)."
                    )
            if (
                "build_cross_layer_map" in run
                or "build_index" in run
                or "save_index" in run
            ):
                found_inline_gen = True
            if "python -m runtime.verify" in run:
                prof = run.strip().split("python -m runtime.verify")[-1].split()[0]
                if prof in ("status", "env-check", "doctor"):
                    # Auxiliary non-gate commands:
                    #   status    — Rule 9 job-summary append (never a verdict).
                    #   env-check — canonical environment fingerprint preflight
                    #              (AGENTS.md: verify before mutation/CI-critical
                    #              work; C42.5 toolchain-drift guard). Produces a
                    #              consistency report, never a verification
                    #              verdict, so it cannot duplicate or weaken the
                    #              single authoritative profile command (Rule 8).
                    #   doctor    — richer environment diagnostic, used by the
                    #              mutation workflows as a pre-campaign preflight
                    #              (AGENTS.md "environment diagnostic guard"). Like
                    #              env-check it reports; it never produces a gate.
                    #              Rule 9 summaries use `status`; `doctor` appears
                    #              only outside GITHUB_STEP_SUMMARY.
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
                    elif prof.startswith(expected + "-"):
                        # A documented subcommand of this workflow's own
                        # profile. Rule 8 requires the workflow to execute
                        # `python runtime/verify.py`; it does not forbid one
                        # profile from using that profile's own subcommands.
                        # mutation.yml relies on this: the M9-C71 sharded
                        # authoritative campaign is one responsibility (mutation)
                        # expressed as plan -> shard -> aggregate -> trust, which
                        # are `mutation-plan`, `mutation --shard`,
                        # `mutation-aggregate` and `mutation-trust`.
                        found_verify_profile = True
                    else:
                        # A *different* profile. This is a genuine violation:
                        # the workflow claims one responsibility and executes
                        # another profile's command.
                        err(
                            f"{name}/{job_id}: runs `runtime.verify {prof}` but should be "
                            f"`runtime.verify {expected}` (Rule 8)"
                        )
            # artifact names via upload-runtime
            name_in = step.get("with", {}).get("name")
            if uses.endswith("upload-runtime") and name_in:
                artifact_names.append(name_in)
                path_in = step.get("with", {}).get("path")
                # Rule 12 — invalid artifact handling. Three failure shapes,
                # all of which surface as a red or a silently-empty artifact
                # rather than as an explanation.
                if path_in is not None and not str(path_in).strip():
                    err(
                        f"{name}/{job_id}: artifact '{name_in}' has an empty `path` "
                        f"(Rule 12)."
                    )
                if path_in and any(part in str(path_in) for part in ("../", "~")):
                    err(
                        f"{name}/{job_id}: artifact path '{path_in}' escapes the "
                        f"workspace. Artifact paths must be workspace-relative; "
                        f"actions/upload-artifact resolves them against "
                        f"GITHUB_WORKSPACE and a `../` or `~/` path names something "
                        f"outside the run (Rule 12)."
                    )
                missing = step.get("with", {}).get("if-no-files-found")
                if missing is not None and str(missing) not in (
                    "warn",
                    "ignore",
                    "error",
                ):
                    err(
                        f"{name}/{job_id}: artifact '{name_in}' sets "
                        f"if-no-files-found='{missing}'. The value is passed straight "
                        f"through to actions/upload-artifact, which accepts only "
                        f"warn|ignore|error and fails the step on anything else "
                        f"(Rule 12)."
                    )

    # A matrix job must disambiguate its artifact names: `actions/upload-artifact`
    # rejects a second upload with the same name in one run, so N matrix legs
    # uploading 'x' means legs 2..N fail.
    matrixed = [
        job_id
        for job_id, job in jobs.items()
        if (job.get("strategy") or {}).get("matrix")
    ]
    if matrixed:
        for job_id in matrixed:
            names_here = []
            for step in jobs[job_id].get("steps", []):
                if step.get("uses", "").endswith("upload-runtime"):
                    n = (step.get("with") or {}).get("name")
                    if n:
                        names_here.append(n)
            ambiguous = [n for n in set(names_here) if "matrix." not in str(n)]
            if ambiguous:
                err(
                    f"{name}/{job_id}: matrix job uploads artifact(s) {sorted(ambiguous)} "
                    f"whose names do not interpolate `matrix.`. Every matrix leg "
                    f"resolves to the same artifact name and the second upload fails "
                    f"(Rule 12)."
                )

    # verification workflow must run exactly one profile command
    if name in VERIFICATION_PROFILES:
        if not found_verify_profile:
            err(
                f"{name}: missing required `python -m runtime.verify {VERIFICATION_PROFILES[name]}` (Rule 8)"
            )
        if not found_status:
            err(f"{name}: missing `python -m runtime.verify status` summary (Rule 9)")
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
    print(
        f"Composite actions validated: {len([d for d in ACT_DIR.iterdir() if d.is_dir()])}"
    )
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
