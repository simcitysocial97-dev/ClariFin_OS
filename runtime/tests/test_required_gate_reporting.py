"""M9 stabilization — gate integrity: a required check must always be able to report.

`protect-main-branch` requires four contexts. GitHub treats a required context
that does not report as **unsatisfied**, so a required check carrying a `paths:`
filter blocks every pull request that happens to touch none of those paths — with
every check that *did* report showing green. That failure mode is indistinguishable
from "CI is red" when you only read the checks list, and it has already cost one
pull request on this repository (PR #8, fixed for `Runtime Verification` and left
in place for `Backend Verification`).

The invariant is asserted here against the workflow files and against the
ruleset's own required list, so a filter cannot be reintroduced to a required
gate without a test failing.

Run:
    python -m pytest runtime/tests/test_required_gate_reporting.py -q
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent.parent
WORKFLOWS = REPO / ".github" / "workflows"
RULESET_ID = "20127383"

#: The contexts `protect-main-branch` requires. Kept as an explicit list so the
#: test states the contract rather than mirroring whatever the ruleset happens to
#: contain today; a workflow whose name is not here cannot silently become a
#: required gate.
REQUIRED_CONTEXTS = {
    "Backend Verification": "backend-verify.yml",
    "Frontend Verification": "frontend-verify.yml",
    "Runtime Verification": "verification-runtime.yml",
    "Analyze": "security-codeql.yml",
}

#: Not required, on purpose, keyed by the workflow's own `name:`. Each reason is
#: asserted below so it cannot quietly become stale.
NOT_REQUIRED = {
    "Quality Gate": (
        "repository/static/application quality — `runtime verify quick` plus "
        "frontend eslint/tsc/vitest. Path-scoped so it neither runs twice per PR "
        "nor reports on an event with nothing static to say; its green result is "
        "still published, it is simply not a merge gate."
    ),
    "Verification Reconcile": (
        "change-boundary runtime verification and reconciliation — "
        "`runtime verify check` over the resolved capability boundary. Path-scoped "
        "to runtime/ and backend/; its verdict is an evidence artifact, not a "
        "merge gate. Required checks that report for the same tree are Backend "
        "Verification (total backend) and Verification Runtime (runtime "
        "self-validation), which are different commands over different scopes."
    ),
    "API Contract Integrity": (
        "diffs the committed OpenAPI baseline; path-scoped to the API surface. A "
        "contract break is a Backend/Frontend failure symptom, and its own "
        "`workflow_run` re-check on a failed Playwright run covers the case where "
        "the E2E suite is the first thing to notice."
    ),
    "Playwright Tests": (
        "chromium + mobile-chrome E2E matrix; path-scoped to frontend/ and e2e/. "
        "Deliberately not a merge gate: it needs both a built frontend and a live "
        "backend, and requiring it would make every backend-only change wait on a "
        "browser matrix. It is re-checked by Verification Runtime's route and shell "
        "readiness assertions."
    ),
    "Mutation Testing": (
        "scheduled and dispatched campaign over 26 shards, ~25 min. A merge gate "
        "at that cost would block every PR on an hourly signal."
    ),
    "Mutation Testing (PR Incremental)": (
        "boundary-scoped campaign for pull requests. Complementary evidence, not a "
        "gate: the aggregate verdict is published for review."
    ),
    "Golden Dataset Regression": (
        "scheduled financial-regression sweep, no per-PR event."
    ),
    "M9 Forensic Diagnostic Lab": ("manual forensic surface, dispatched on demand."),
    "Dependency Updates": (
        "schedated dependency refresh; its own job reports per-update."
    ),
    "Release": ("release-time only; nothing about a pull request can satisfy it."),
    "CodeQL Security Analysis": (
        "the single authoritative CodeQL owner. Its `Analyze` job IS required; the "
        "workflow is listed here only so the reasons file is complete, and it "
        "carries no path filter for the same reason the other required gates do not."
    ),
}


def _load(rel: str) -> dict:
    return yaml.safe_load((WORKFLOWS / rel).read_text())


def _triggers(doc: dict) -> dict:
    return doc.get(True) or doc.get("on") or {}


@pytest.mark.parametrize("context,rel", sorted(REQUIRED_CONTEXTS.items()))
def test_a_required_gate_has_no_path_filter(context: str, rel: str):
    """A required gate that can skip is a gate that blocks everything else."""
    triggers = _triggers(_load(rel))
    assert triggers, f"{rel} declares no triggers"
    for event, cfg in triggers.items():
        if not isinstance(cfg, dict):
            continue
        assert "paths" not in cfg, (
            f"{context!r} is a required status check and must always report, but "
            f"its {event} trigger is filtered to {cfg['paths']}. A pull request "
            "that touches none of those paths would be permanently blocked with "
            "every reported check green."
        )


def test_backend_verification_is_a_total_check_not_a_boundary_check():
    """Removing the filter is only honest if the check is total.

    `Backend Verification` runs `runtime verify backend` over the whole backend.
    Boundary-scoped runtime verification is owned by Verification Reconcile
    (`runtime verify check`) — a different command over a different scope — so
    running it on a PR that changed no backend code is added coverage, not a
    second copy of the same work.
    """
    backend = yaml.safe_dump(_load("backend-verify.yml"))
    reconcile = yaml.safe_dump(_load("verification-reconcile.yml"))
    assert "-m runtime.verify backend" in backend
    assert "-m runtime.verify check" in reconcile
    assert (
        "-m runtime.verify check" not in backend
    ), "Backend Verification must not do the reconcile workflow's job"
    assert "-m runtime.verify backend" not in reconcile


def test_the_quality_gate_does_not_duplicate_the_reconcile_workflow():
    """§2: static quality and boundary verification are distinct responsibilities."""
    quality = yaml.safe_dump(_load("quality.yml"))
    reconcile = yaml.safe_dump(_load("verification-reconcile.yml"))
    assert "-m runtime.verify quick" in quality
    assert "-m runtime.verify check" not in quality, (
        "the Quality Gate must stay static/application quality; boundary "
        "verification belongs to Verification Reconcile"
    )
    assert (
        "-m runtime.verify quick" not in reconcile
    ), "the Reconcile workflow must not re-run the static profile"


def test_the_ruleset_required_list_is_the_one_this_test_claims():
    """The contract above is checked against the ruleset, not assumed.

    Skips when the token cannot read the ruleset — a private repository without
    the audit scope must not turn a governance test into a false failure. The
    workflow-file invariants above still hold in that case.
    """
    try:
        raw = subprocess.run(
            [
                "gh",
                "api",
                f"repos/:owner/:repo/rulesets/{RULESET_ID}",
                "--jq",
                '[.rules[] | select(.type == "required_status_checks")'
                " | .parameters.required_status_checks[].context]",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        ).stdout
    except (FileNotFoundError, subprocess.SubprocessError):
        pytest.skip("gh CLI unavailable")

    try:
        required = set(json.loads(raw))
    except json.JSONDecodeError:
        pytest.skip("ruleset not readable from this environment")

    assert required == set(REQUIRED_CONTEXTS), (
        f"the ruleset requires {sorted(required)} but this test documents "
        f"{sorted(REQUIRED_CONTEXTS)}. Update both together, and say why."
    )


def test_every_non_required_workflow_states_a_reason():
    """§10 asks for the exact reason each workflow is intentionally not required.

    A workflow that is not required and has no recorded reason here is the same
    as a forgotten one. The unit is the workflow, not the job: a workflow is
    required or it is not.
    """
    required_owners = set(REQUIRED_CONTEXTS.values())
    undocumented = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        name = (yaml.safe_load(path.read_text()) or {}).get("name") or path.stem
        if path.name in required_owners or name in NOT_REQUIRED:
            continue
        undocumented.append(f"{path.name} ({name})")

    assert not undocumented, (
        "workflows with no recorded reason for being non-required: "
        f"{undocumented}. Add each to NOT_REQUIRED with the reason, or to "
        "REQUIRED_CONTEXTS if it is meant to gate a merge."
    )
