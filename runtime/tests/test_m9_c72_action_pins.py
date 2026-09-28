# runtime/tests/test_m9_c72_action_pins.py
#
# M9-C72 — Guard the GitHub Actions version pins.
#
# WHY THIS FILE EXISTS
# --------------------
# On 2026-09-28 the 26-shard mutation campaign ran to completion in CI — every
# shard job succeeded — and the run still failed, at this line:
#
#     ##[error]Unable to resolve action `actions/download-artifact@v7.0.1`,
#               unable to find version `v7.0.1`
#
# `actions/download-artifact` publishes v7.0.0 and then v8.0.0; it never shipped
# a v7.0.1 patch. The sibling actions `checkout` and `upload-artifact` DO have a
# v7.0.1 tag, so a repository-wide bump to "v7.0.1" left exactly one action
# unresolvable — and unresolvable actions fail only when a job actually reaches
# the step, so the mistake survived until a full campaign was dispatched.
#
# The cost was asymmetric: two uploads succeeded, so the version looked right;
# only the download failed, and only at the end.
#
# These tests make the pin set explicit and offline-deterministic. They cannot
# reach the network, so they verify two things a network call could not:
#
#   1. every pin is in the DECLARED set below, whose existence was verified
#      against the published tag list on 2026-09-28; and
#   2. the known-trap tag `v7.0.1` is never used for download-artifact.
#
# A version bump that has not been verified against the published tags fails
# here in seconds, instead of failing in CI after a full campaign.
#
# When upgrading an action, verify the tag exists FIRST
# (`gh api repos/actions/<name>/tags`), then update both this table and the
# workflow in the same commit.

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOWS = REPO_ROOT / ".github"

#: Every external action pin in the repository, verified against the published
#: tag list on 2026-09-28 (actions/<name> `git ls-remote --tags`).
#:
#: NOTE the deliberate asymmetry that caused D1: checkout and upload-artifact
#: have a v7.0.1, download-artifact does NOT. Uniform-looking version numbers
#: are not uniform across actions.
VERIFIED_PINS: dict[str, set[str]] = {
    "actions/cache": {"v6.1.0"},
    "actions/checkout": {"v7.0.1"},
    "actions/download-artifact": {"v7.0.0"},
    "actions/github-script": {"v7"},
    "actions/setup-node": {"v7.0.0"},
    "actions/setup-python": {"v7.0.0"},
    "actions/upload-artifact": {"v7", "v7.0.1"},
    "github/codeql-action/autobuild": {"v3"},
    "github/codeql-action/analyze": {"v3"},
    "github/codeql-action/init": {"v3"},
}

#: Tags that MUST NOT be used for download-artifact. `v7.0.1` looks identical
#: to the checkout/upload pins and reads as obviously correct, which is exactly
#: why it was chosen and why it broke.
FORBIDDEN_DOWNLOAD_TAGS = {"v7.0.1"}

USES_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)\s*$", re.MULTILINE)


def _workflow_files() -> list[Path]:
    return sorted(
        p
        for p in WORKFLOWS.rglob("*.yml")
        if ".github/actions" in p.as_posix() or p.parent.name == "workflows"
    )


def _external_pins() -> list[tuple[str, str, Path]]:
    """Every external ``owner/repo@tag`` pin, with the file it came from."""
    pins: list[tuple[str, str, Path]] = []
    for path in _workflow_files():
        for match in USES_PATTERN.finditer(path.read_text(encoding="utf-8")):
            ref = match.group(1)
            if ref.startswith("./") or ref.startswith("docker://"):
                continue  # local composite action or image
            if "@" not in ref:
                continue
            repo, _, tag = ref.partition("@")
            pins.append((repo, tag, path))
    return pins


@pytest.fixture(scope="module")
def mutation_workflow() -> str:
    """The mutation workflow text, for the gate-contract assertions."""
    return (WORKFLOWS / "workflows" / "mutation.yml").read_text(encoding="utf-8")


# ── the pins themselves ──────────────────────────────────────────────────────


class TestActionPinsAreVerified:
    def test_external_pins_exist_in_the_repository(self):
        """A vacuous pass would be worse than no test: assert we found some."""
        pins = _external_pins()

        assert len(pins) >= 5, f"only found {len(pins)} external action pins"

    def test_every_pin_is_a_verified_tag(self):
        """A pin outside the verified set has not been checked for existence.

        This is the assertion that would have caught the D1 incident in a unit
        test rather than after a full campaign.
        """
        unknown: list[str] = []
        for repo, tag, path in _external_pins():
            if tag not in VERIFIED_PINS.get(repo, set()):
                unknown.append(f"{repo}@{tag} ({path.relative_to(REPO_ROOT)})")

        assert not unknown, (
            "action pins not present in VERIFIED_PINS — verify the tag exists "
            "(`gh api repos/<owner>/<repo>/tags`) before using it:\n  "
            + "\n  ".join(unknown)
        )

    def test_download_artifact_never_uses_a_nonexistent_tag(self):
        """The specific regression: v7.0.1 does not exist for this action."""
        offenders = [
            f"{tag} in {path.relative_to(REPO_ROOT)}"
            for repo, tag, path in _external_pins()
            if repo == "actions/download-artifact" and tag in FORBIDDEN_DOWNLOAD_TAGS
        ]

        assert not offenders, (
            "actions/download-artifact has no v7.0.1 tag (it goes v7.0.0 -> "
            "v8.0.0); found: " + ", ".join(offenders)
        )

    def test_download_artifact_uses_a_tag_that_exists(self):
        """download-artifact must be on a real tag, and v7.0.0 is the one."""
        download_pins = {
            tag
            for repo, tag, _ in _external_pins()
            if repo == "actions/download-artifact"
        }

        assert (
            download_pins
        ), "no download-artifact pin found — the aggregate gate cannot work"
        for tag in download_pins:
            assert tag in {
                "v7.0.0",
                "v8.0.0",
                "v8.0.1",
            }, f"actions/download-artifact@{tag} is not a published tag"


# ── the composite action contract ────────────────────────────────────────────


class TestDownloadActionContract:
    @pytest.fixture(scope="class")
    def download_action(self) -> str:
        path = WORKFLOWS / "actions" / "download-runtime" / "action.yml"
        return path.read_text(encoding="utf-8")

    def test_the_shared_download_action_exists(self):
        path = WORKFLOWS / "actions" / "download-runtime" / "action.yml"

        assert path.is_file(), "the canonical download action is missing"

    def test_it_pins_a_resolvable_version(self, download_action):
        """The `uses:` directive must name a published tag.

        Checked on the directive, not on raw text: the file deliberately
        documents the trap tag in a comment, and a raw substring check would
        forbid the very explanation that stops the next person repeating it.
        """
        directives = [m.group(1) for m in USES_PATTERN.finditer(download_action)]

        assert "actions/download-artifact@v7.0.0" in directives
        assert "actions/download-artifact@v7.0.1" not in directives
        assert "v7.0.1" in download_action, "the trap tag must be documented"

    def test_name_and_pattern_are_passed_exclusively(self, download_action):
        """`name` and `pattern` are mutually exclusive.

        Forwarding a bare `name: ${{ inputs.name }}` sends an empty string
        whenever a caller sets only `pattern`, which selects the wrong lookup
        mode. Each must be nulled when the caller did not supply it.
        """
        assert "name: ${{ inputs.name != '' && inputs.name || null }}" in (
            download_action
        ), "name is forwarded verbatim; an unset input arrives as an empty string"
        assert "pattern: ${{ inputs.pattern != '' && inputs.pattern || null }}" in (
            download_action
        ), "pattern is forwarded verbatim"

    def test_it_documents_why_the_version_is_pinned(self, download_action):
        """A pin with no recorded reason is a pin that will be 'fixed' again."""
        text = download_action.lower()

        assert "v7.0.0" in text
        assert "v7.0.1" in text, "the trap tag must be named so the history survives"


# ── expression syntax: the bug that yields empty instead of failing ───────────


class TestDispatchInputExpressions:
    """Hyphenated `workflow_dispatch` inputs cannot use dotted access.

    `${{ inputs.engine-name }}` parses as `inputs.engine - run - id` and
    evaluates to EMPTY — it does not error. That is the dangerous part: a
    silent empty is indistinguishable from a defaulted input.

    It stayed hidden here because the affected input, `engine-name`, has a
    default of `all` and empty is handled the same way, so the campaign
    produced a correct full plan and nothing looked wrong. When
    `evidence-run-id` was added with no default, the replay path resolved an
    empty run id and failed with "No run with shard evidence was found" while
    the log showed the correct id in the environment.

    A guard turns a silent wrong value into a failing test.
    """

    @pytest.mark.parametrize("workflow", sorted(WORKFLOWS.glob("workflows/*.yml")))
    def test_no_hyphenated_input_uses_dotted_access(self, workflow):
        # Comment lines are excluded: this file's own documentation quotes the
        # broken form to explain it, and a guard that flagged its own
        # explanation would have to be deleted rather than trusted.
        expressions = [
            line
            for line in workflow.read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        ]
        offenders = {
            match.group(0)
            for line in expressions
            for match in re.finditer(r"inputs\.([A-Za-z0-9_-]*-)", line)
        }

        assert not offenders, (
            f"{workflow.name}: dotted access on a hyphenated input name "
            f"({', '.join(sorted(offenders))}); use inputs['name-with-hyphen']"
        )

    def test_the_mutation_workflow_reads_its_replay_input(self):
        """The input that actually broke the replay path must be read correctly."""
        text = (WORKFLOWS / "workflows" / "mutation.yml").read_text(encoding="utf-8")

        assert "inputs['evidence-run-id']" in text


# ── the exit-code contract that made a below-threshold run lie ───────────────


class TestAggregateExitCodeContract:
    def test_the_gate_captures_its_own_exit_code(self, mutation_workflow):
        """`bash -e` kills the step on a non-zero exit, so a bare `RC=$?` is
        dead code and the exit code never reaches the enforcing step.

        A below-threshold campaign (exit 2) would then be reported as
        "NOT EVALUABLE", telling the reader to look for missing evidence when
        the evidence was complete and the score was simply low.
        """
        assert (
            "set +e" in mutation_workflow
        ), "the reconcile step must disable errexit before capturing RC"
        assert "set -e" in mutation_workflow, "errexit must be restored afterwards"
        assert "RC=$?" in mutation_workflow

    def test_the_reconcile_step_declares_bash_explicitly(self, mutation_workflow):
        """`set +e` only takes effect under a shell that honours it, and the
        `run:` default shell must be stated so the behaviour is not implicit."""
        assert "shell: bash" in mutation_workflow

    def test_distinct_exit_codes_are_enforced_distinctly(self, mutation_workflow):
        """0 satisfied, 2 below threshold, 1 not evaluable — three meanings, so
        three branches. Collapsing 1 and 2 would hide the reason for a failure."""
        enforce = mutation_workflow.split("Enforce campaign gate", 1)[-1]

        assert 'if [ "$RC" = "0" ]' in enforce
        assert 'elif [ "$RC" = "2" ]' in enforce, (
            "a below-threshold campaign must be reported as below threshold, "
            "not as missing evidence"
        )
        assert "below threshold" in enforce.lower()
        assert "NOT EVALUABLE" in enforce


# ── the diagnostic that makes a transport fault visible ──────────────────────


class TestTransportDiagnostics:
    def test_the_gate_reports_what_it_downloaded(self, mutation_workflow):
        """The D1 incident printed nothing at the failing step.

        Without this, a transport fault and a measurement fault are
        indistinguishable from the log, and recovery costs a full campaign.
        """
        assert "Report downloaded shard evidence" in mutation_workflow
        assert "mutation-summary-*.json" in mutation_workflow
        assert "TRANSPORT fault" in mutation_workflow, (
            "the summary must distinguish a transport fault from a measurement "
            "fault, or the next incident costs the same debugging session"
        )
