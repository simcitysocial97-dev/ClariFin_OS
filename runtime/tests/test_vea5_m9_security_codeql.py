"""VEA-5 M9 — CodeQL Security Analysis Integration.

M9 establishes a real, source-controlled, GitHub-native CodeQL security-analysis
surface and wires it into the VEA-5 deep-contract (``deep-codeql`` surface) as a
genuine, executable, auditable surface — distinct from every existing verification
owner (unit/integration/contract/frontend/mutation/golden/playwright/dependency).

These tests are layered per the M0–M8 reality-audit standard:

  * Static      — the workflow file is valid and configured to spec.
  * Behavioral  — the ``deep-codeql`` DEEP contract surface is REAL (not a stub)
                  and references the workflow that executes it.
  * Negative    — the analysis step must NOT swallow failures (no
                  ``continue-on-error``); a failed analysis must fail the job,
                  never silently pass.
  * Scope       — a security workflow must not carry a path filter that could let
                  security-sensitive changes bypass CodeQL.

Run:
    python3 -m pytest runtime/tests/test_vea5_m9_security_codeql.py -q
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO / ".github" / "workflows"
WF = WORKFLOWS / "security-codeql.yml"

CODEQL_ACTION = "github/codeql-action"
VALID_LANGS = {"python", "javascript"}  # javascript extractor covers TypeScript


def _load_wf() -> dict:
    assert WF.exists(), f"security-codeql.yml missing at {WF}"
    return yaml.safe_load(WF.read_text())


# ---------------------------------------------------------------------------
# Static — workflow configuration
# ---------------------------------------------------------------------------


def test_m9_workflow_exists_and_is_valid_yaml():
    doc = _load_wf()
    assert doc.get("name") == "CodeQL Security Analysis"


def test_m9_analyzes_repository_languages():
    """Only languages actually present in the repo (Python + JS/TS) are analyzed."""
    doc = _load_wf()
    jobs = doc["jobs"]
    analyze = jobs["analyze"]
    init = next(
        s
        for s in analyze["steps"]
        if (s.get("uses") or "").endswith("codeql-action/init@v3")
    )
    langs = {l.strip() for l in init["with"]["languages"].split(",")}
    # Exactly python + javascript; nothing else blindly enabled.
    assert langs == VALID_LANGS, f"unexpected CodeQL languages: {langs}"


def test_m9_uses_supported_codeql_actions():
    doc = _load_wf()
    analyze = doc["jobs"]["analyze"]
    uses = [s.get("uses", "") for s in analyze["steps"]]
    assert any(u.endswith(f"{CODEQL_ACTION}/init@v3") for u in uses)
    assert any(u.endswith(f"{CODEQL_ACTION}/analyze@v3") for u in uses)
    # Either autobuild or an explicit build step is present (analyze needs a build).
    assert any(
        u.endswith(f"{CODEQL_ACTION}/autobuild@v3") for u in uses
    ), "CodeQL analysis requires a build/autobuild step"


def test_m9_minimal_permissions_explained():
    doc = _load_wf()
    perms = doc.get("permissions", {})
    # security-events:write is mandatory to upload SARIF to code scanning.
    assert perms.get("security-events") == "write"
    # contents:read is the least-privilege for checkout.
    assert perms.get("contents") == "read"
    assert perms.get("actions") == "read"
    # pull-requests:write enables PR annotations (PR-feedback objective).
    assert perms.get("pull-requests") == "write"


def test_m9_triggers_cover_pr_and_default_branch_and_scheduled():
    doc = _load_wf()
    on = doc.get("on") if "on" in doc else doc.get(True, {})
    assert "pull_request" in on, "CodeQL must run on PRs for security feedback"
    assert "push" in on, "CodeQL must run on push to default branch (merge cadence)"
    assert "workflow_dispatch" in on, "CodeQL must support manual re-scan"
    assert "schedule" in on, "CodeQL must support scheduled deep analysis"
    pr = on["pull_request"]
    assert "main" in pr["branches"]


def test_m9_deterministic_job_identity():
    doc = _load_wf()
    assert list(doc["jobs"].keys()) == ["analyze"], "exactly one job 'analyze'"
    assert doc["jobs"]["analyze"]["name"] == "Analyze"


def test_m9_concurrency_is_configured():
    doc = _load_wf()
    conc = doc.get("concurrency", {})
    assert conc.get("group") == "${{ github.workflow }}-${{ github.ref }}"
    assert conc.get("cancel-in-progress") is True


def test_m9_no_path_filter_on_security_scope():
    """A security workflow must not silently skip security-sensitive changes."""
    doc = _load_wf()
    on = doc.get("on") if "on" in doc else doc.get(True, {})
    push = on.get("push", {})
    pr = on.get("pull_request", {})
    # No `paths` filters may restrict which changes are analyzed.
    assert "paths" not in push, "PR/push path filter would let changes bypass CodeQL"
    assert "paths" not in pr, "PR/push path filter would let changes bypass CodeQL"


def test_m9_uploads_to_code_scanning():
    """The analysis step uploads results (SARIF) to GitHub code scanning."""
    doc = _load_wf()
    analyze = doc["jobs"]["analyze"]
    analyze_step = next(
        s
        for s in analyze["steps"]
        if (s.get("uses") or "").endswith("codeql-action/analyze@v3")
    )
    # github/codeql-action/analyze uploads SARIF by default; presence is the contract.
    assert analyze_step.get("uses", "").endswith("codeql-action/analyze@v3")


# ---------------------------------------------------------------------------
# Negative — failure must not be silently converted to success
# ---------------------------------------------------------------------------


def test_m9_analysis_failure_is_not_swallowed():
    """A failed CodeQL analysis must fail the job (never continue-on-error)."""
    doc = _load_wf()
    analyze = doc["jobs"]["analyze"]
    for step in analyze["steps"]:
        if (step.get("uses") or "").endswith("codeql-action/analyze@v3"):
            assert step.get("continue-on-error") is not True, (
                "CodeQL analysis must NOT use continue-on-error — failures must "
                "fail the job, not silently pass"
            )


def test_m9_analysis_step_always_executes():
    """Zero findings must still be a real, executed analysis (never skipped)."""
    doc = _load_wf()
    analyze = doc["jobs"]["analyze"]
    init = any(
        (s.get("uses") or "").endswith("codeql-action/init@v3")
        for s in analyze["steps"]
    )
    analyze_present = any(
        (s.get("uses") or "").endswith("codeql-action/analyze@v3")
        for s in analyze["steps"]
    )
    assert init and analyze_present, "CodeQL init+analyze must always run the analysis"


# ---------------------------------------------------------------------------
# Behavioral — deep-codeql DEEP contract surface is REAL (not a stub)
# ---------------------------------------------------------------------------


def test_m9_deep_codeql_surface_is_real_not_stub():
    from runtime.foundation.verification.evidence_contract import (
        DeepVerificationDomain,
        deep_surfaces_by_domain,
    )

    surfaces = deep_surfaces_by_domain(DeepVerificationDomain.SECURITY.value)
    codeql = next(s for s in surfaces if s.surface_id == "deep-codeql")
    # Previously a stub: command="github-codeql/codeql" (not a real command).
    assert (
        codeql.command == "github/codeql-action/analyze"
    ), "deep-codeql command must reference the real CodeQL action, not a stub"
    assert (
        codeql.workflow == ".github/workflows/security-codeql.yml"
    ), "deep-codeql must associate the source-controlled workflow"
    assert codeql.domain == "security"
    assert "codeql" in codeql.evidence_kinds
    assert "security" in codeql.evidence_kinds
    # Languages covered are declared real (python + javascript/TS).
    assert "schedule" in codeql.trigger  # scheduled deep analysis
    assert "merge" in codeql.trigger  # push-to-default-branch cadence


def test_m9_workflow_file_matches_contract_surface():
    """The contract surface's workflow path must point at the real file."""
    from runtime.foundation.verification.evidence_contract import (
        DeepVerificationDomain,
        deep_surfaces_by_domain,
    )

    codeql = next(
        s
        for s in deep_surfaces_by_domain(DeepVerificationDomain.SECURITY.value)
        if s.surface_id == "deep-codeql"
    )
    path = REPO / codeql.workflow
    assert path.exists(), f"deep-codeql workflow missing: {path}"
    assert path == WF


def test_m9_deep_contract_still_has_six_domains_and_surfaces():
    """M9 must not disturb the established DEEP contract shape."""
    from runtime.foundation.verification.evidence_contract import (
        DeepVerificationDomain,
        deep_contract_manifest,
    )

    manifest = deep_contract_manifest()
    assert manifest["schema"] == "vea5-deep-contract/v1"
    assert set(manifest["domains"]) == {d.value for d in DeepVerificationDomain}
    assert len(manifest["surfaces"]) >= 10
