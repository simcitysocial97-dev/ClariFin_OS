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

#: External actions pinned to an immutable commit SHA. M10 replaced every
#: tag pin with a full 40-character SHA, keeping the tag as a trailing comment
#: for humans. A SHA pin makes the D1 failure class structurally impossible — a
#: tag can name a release that never existed; a commit cannot — but these tests
#: still verify the pins offline and deterministically, so the resolved SHAs
#: are declared here exactly as the tags are.
#:
#: Resolve with:
#:     gh api repos/<owner>/<repo>/commits/<tag> --jq .sha
VERIFIED_SHAS: dict[str, set[str]] = {
    "actions/cache": {"55cc8345863c7cc4c66a329aec7e433d2d1c52a9"},
    "actions/checkout": {"3d3c42e5aac5ba805825da76410c181273ba90b1"},
    "actions/download-artifact": {"37930b1c2abaa49bbe596cd826c3c89aef350131"},
    "actions/github-script": {"f28e40c7f34bde8b3046d885e986cb6290c5673b"},
    "actions/setup-node": {"820762786026740c76f36085b0efc47a31fe5020"},
    "actions/setup-python": {"5fda3b95a4ea91299a34e894583c3862153e4b97"},
    "actions/upload-artifact": {"043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"},
    "github/codeql-action/autobuild": {"1190a975f95ce23525efb6a3fc21ea29567c1b52"},
    "github/codeql-action/analyze": {"1190a975f95ce23525efb6a3fc21ea29567c1b52"},
    "github/codeql-action/init": {"1190a975f95ce23525efb6a3fc21ea29567c1b52"},
}

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# A `uses:` directive, allowing for the trailing `# <tag>` comment that records
# the human-readable version next to a SHA pin.
USES_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)\s*(?:#.*)?$", re.MULTILINE)


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

    def test_every_pin_is_a_verified_tag_or_sha(self):
        """A pin outside the verified sets has not been checked for existence.

        This is the assertion that would have caught the D1 incident in a unit
        test rather than after a full campaign. Since M10 the repository pins to
        an immutable commit SHA with the tag retained as a comment, so a pin is
        acceptable if it is a declared verified SHA *or* a declared verified tag.
        """
        unknown: list[str] = []
        for repo, ref, path in _external_pins():
            if SHA_RE.match(ref):
                if ref not in VERIFIED_SHAS.get(repo, set()):
                    unknown.append(f"{repo}@{ref} ({path.relative_to(REPO_ROOT)})")
            elif ref not in VERIFIED_PINS.get(repo, set()):
                unknown.append(f"{repo}@{ref} ({path.relative_to(REPO_ROOT)})")

        assert not unknown, (
            "action pins not present in VERIFIED_SHAS/VERIFIED_PINS — resolve "
            "and verify the ref exists (`gh api repos/<owner>/<repo>/commits/"
            "<tag> --jq .sha`) before using it:\n  "
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
        """download-artifact must resolve to a real published version.

        Accepts either form of pin: a published tag, or a verified commit SHA
        (which cannot name a nonexistent release at all). Either way the pin
        must be one this repository has verified.
        """
        download_pins = {
            ref for repo, ref, _ in _external_pins() if repo == "actions/download-artifact"
        }

        assert (
            download_pins
        ), "no download-artifact pin found — the aggregate gate cannot work"
        for ref in download_pins:
            if SHA_RE.match(ref):
                assert (
                    ref in VERIFIED_SHAS["actions/download-artifact"]
                ), f"actions/download-artifact@{ref} is not a verified commit SHA"
            else:
                assert ref in {
                    "v7.0.0",
                    "v8.0.0",
                    "v8.0.1",
                }, f"actions/download-artifact@{ref} is not a published tag"


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
        """The `uses:` directive must name a resolvable version.

        Checked on the directive, not on raw text: the file deliberately
        documents the trap tag in a comment, and a raw substring check would
        forbid the very explanation that stops the next person repeating it.

        Since M10 the directive is pinned to a verified commit SHA, so the
        assertion is that the directive carries that SHA and that the version
        it resolves from is recorded alongside it.
        """
        directives = [m.group(1) for m in USES_PATTERN.finditer(download_action)]

        assert not any(
            d.endswith("@v7.0.1") for d in directives
        ), "the nonexistent download-artifact v7.0.1 tag must never be pinned"
        download_sha = VERIFIED_SHAS["actions/download-artifact"]
        assert any(
            d.startswith("actions/download-artifact@") and d.split("@", 1)[1] in download_sha
            for d in directives
        ), f"download-runtime must pin a verified download-artifact SHA: {directives}"
        # The resolved version must stay readable next to the SHA, so the next
        # person bumping this pin knows which release to verify first.
        pin_lines = [
            ln
            for ln in download_action.splitlines()
            if "uses: actions/download-artifact@" in ln
        ]
        assert pin_lines, "no download-artifact pin line found"
        assert all(
            "# v7.0.0" in ln for ln in pin_lines
        ), f"the resolved version must be recorded on the pin line: {pin_lines}"
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
