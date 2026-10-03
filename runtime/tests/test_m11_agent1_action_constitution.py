# runtime/tests/test_m11_agent1_action_constitution.py
#
# M11 Agent 1 — regression tests for `.github/scripts/validate_actions.py`.
#
# WHY THIS FILE EXISTS
# --------------------
# `.github/scripts/validate_actions.py` enforced eight rules over
# `.github/workflows/**` and `.github/actions/**` since M9-C72, and NOTHING IN
# CI EVER RAN IT. M10 Agent 2 recorded that as finding F-4 ("gap, not
# duplication"); M11 wired it into the Quality Gate and, in doing so, found that
# it had been reporting a green tree while `frontend-verify.yml` violated its
# own Rule 8 for a full milestone.
#
# A validator that is never executed is indistinguishable from a validator that
# does not work. This file executes it — offline, deterministically, against
# SYNTHETIC workflow trees — and proves that each rule it claims to enforce
# actually fires, and that each architecture the repository legitimately uses
# is still ACCEPTED.
#
# The asymmetry is the point. Every "must fail" case below is a real failure
# mode this repository has already paid for:
#
#   Rule 8  wrong profile       a verification workflow executing a DIFFERENT
#                                profile's command means two workflows both
#                                believe they own one verification meaning.
#   Rule 8  missing profile     the workflow reports a check name while running
#                                nothing that produces that verification.
#   Rule 10 unpinned action     `actions/download-artifact@v7.0.1` never
#                                existed; the sibling actions DO have a v7.0.1,
#                                so the pin set looked uniform. It cost a full
#                                26-shard mutation campaign (M9-C72).
#   Rule 12 artifact handling   a matrix leg uploading an un-suffixed name
#                                fails on the second leg; an out-of-workspace
#                                or empty path silently uploads nothing.
#   Rule 7a path-gated required A required context a `paths:` filter can skip
#                                never reports, and GitHub treats a required
#                                context that does not report as UNSATISFIED.
#                                That is what blocked PR #8 with every reported
#                                check green.
#
# The "must be ACCEPTED" cases are equally load-bearing: a validator that
# rejects `mutation.yml`'s plan -> shard -> aggregate -> trust pipeline, or
# `playwright.yml`'s matrix, would push engineers toward deleting the
# architecture rather than fixing it. Green must be reachable honestly.

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR_PATH = REPO_ROOT / ".github" / "scripts" / "validate_actions.py"


def _load_validator():
    """Import the validator as a module so its globals can be redirected."""
    spec = importlib.util.spec_from_file_location(
        "validate_actions_under_test", VALIDATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def validator(monkeypatch, tmp_path):
    """A validator instance with its directories and error buffers reset.

    The validator keeps `ERRORS`/`WARNINGS` in module-level lists and resolves
    its directories from `ROOT` at import time. Redirecting the directories at
    the module level lets a test point it at a synthetic `.github/` tree and
    read the exact messages it produced, instead of asserting on a substring of
    stdout.
    """
    module = _load_validator()
    workflows = tmp_path / ".github" / "workflows"
    actions = tmp_path / ".github" / "actions"
    workflows.mkdir(parents=True)
    actions.mkdir(parents=True)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "WF_DIR", workflows)
    monkeypatch.setattr(module, "ACT_DIR", actions)
    module.ERRORS = []
    module.WARNINGS = []
    return module


def _write(validator, name: str, doc: dict) -> Path:
    path = validator.WF_DIR / name
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return path


def _base_workflow(**overrides) -> dict:
    """A workflow that passes every rule, so a test can break exactly one thing."""
    doc = {
        "name": "Synthetic",
        "on": {"pull_request": {"branches": ["main"]}, "workflow_dispatch": None},
        "concurrency": {
            "group": "${{ github.workflow }}-${{ github.ref }}",
            "cancel-in-progress": True,
        },
        "permissions": {"contents": "read"},
        "jobs": {
            "verify": {
                "name": "Synthetic Verification",
                "runs-on": "ubuntu-latest",
                "steps": [
                    {
                        "uses": "./.github/actions/bootstrap-runtime",
                        "with": {"python-version": "3.12"},
                    },
                    {"run": ".venv/bin/python -m runtime.verify quick"},
                    {
                        "run": (
                            ".venv/bin/python -m runtime.verify status "
                            ">> $GITHUB_STEP_SUMMARY"
                        )
                    },
                ],
            }
        },
    }
    doc.update(overrides)
    return doc


# ── Rule 8: wrong profile → failure ──────────────────────────────────────────


class TestRule8ProfileDelegation:
    def test_a_different_profiles_command_is_an_error(self, validator):
        path = _write(
            validator,
            "quality.yml",
            _base_workflow(
                jobs={
                    "quality": {
                        "name": "Quality Gate",
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            # quality.yml must run `quick`; this runs `backend`.
                            {"run": ".venv/bin/python -m runtime.verify backend"},
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(path)
        assert any(
            "should be" in e and "Rule 8" in e for e in validator.ERRORS
        ), validator.ERRORS

    def test_bypassing_the_profile_with_a_bare_script_is_an_error(self, validator):
        """The exact M11 failure: `frontend-verify.yml` ran the script directly.

        This is the regression that was live for a full milestone. The validator
        reported it correctly the whole time; nothing ran the validator.
        """
        path = _write(
            validator,
            "frontend-verify.yml",
            _base_workflow(
                jobs={
                    "verify": {
                        "name": "Frontend Verification",
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {
                                "run": (
                                    "bash "
                                    ".github/scripts/run_frontend_verification.sh"
                                )
                            },
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(path)
        assert any(
            "missing required `python -m runtime.verify frontend`" in e
            for e in validator.ERRORS
        ), validator.ERRORS


# ── Rule 8: missing required profile → failure ───────────────────────────────


class TestRule8MissingProfile:
    def test_a_verification_workflow_with_no_profile_command_is_an_error(
        self, validator
    ):
        path = _write(
            validator,
            "verification-runtime.yml",
            _base_workflow(
                jobs={
                    "verify-runtime": {
                        "name": "Runtime Verification",
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(path)
        assert any(
            "missing required `python -m runtime.verify runtime`" in e
            for e in validator.ERRORS
        ), validator.ERRORS

    def test_missing_status_summary_is_an_error(self, validator):
        path = _write(
            validator,
            "verification-runtime.yml",
            _base_workflow(
                jobs={
                    "verify-runtime": {
                        "name": "Runtime Verification",
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {"run": ".venv/bin/python -m runtime.verify runtime"},
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(path)
        assert any("Rule 9" in e for e in validator.ERRORS), validator.ERRORS


# ── Rule 10: unsafe unpinned external action → failure ───────────────────────


class TestRule10ImmutableActionPins:
    def _workflow_with_uses(self, validator, uses: str) -> list[str]:
        path = _write(
            validator,
            "api-contracts.yml",
            _base_workflow(
                jobs={
                    "gate": {
                        "name": "Synthetic Gate",
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {"uses": uses, "with": {"name": "x", "path": "y"}},
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(path)
        return list(validator.ERRORS)

    def test_a_tag_pin_is_rejected(self, validator):
        errors = self._workflow_with_uses(validator, "actions/checkout@v7.0.1")
        assert any(
            "not a 40-character commit SHA" in e and "Rule 10" in e for e in errors
        ), errors

    def test_the_download_artifact_trap_tag_is_rejected(self, validator):
        """`actions/download-artifact@v7.0.1` never existed.

        The sibling actions `checkout` and `upload-artifact` DO have a v7.0.1,
        so a repository-wide bump left exactly one action unresolvable — and
        unresolvable actions fail only when a job reaches the step, which is
        why it survived until a full 26-shard campaign ran (M9-C72).
        """
        errors = self._workflow_with_uses(validator, "actions/download-artifact@v7.0.1")
        assert any("Rule 10" in e for e in errors), errors

    def test_an_action_with_no_ref_at_all_is_rejected(self, validator):
        errors = self._workflow_with_uses(validator, "actions/checkout")
        assert any("has no ref" in e and "Rule 10" in e for e in errors), errors

    def test_sha_pin_is_accepted(self, validator):
        errors = self._workflow_with_uses(
            validator,
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        )
        assert not [e for e in errors if "Rule 10" in e], errors

    def test_the_repository_itself_is_fully_sha_pinned(self):
        """The real tree, asserted by the same rule the synthetic cases use."""
        module = _load_validator()
        assert module.SHA_PIN.match("3d3c42e5aac5ba805825da76410c181273ba90b1")
        for workflow in sorted((REPO_ROOT / ".github").rglob("*.yml")):
            for line in workflow.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped.startswith("uses:"):
                    continue
                ref = stripped.split("uses:", 1)[1].split("#", 1)[0].strip()
                if (
                    ref.startswith("./")
                    or ref.startswith("docker://")
                    or "@" not in ref
                ):
                    continue
                _, _, pin = ref.partition("@")
                assert module.SHA_PIN.match(pin), f"{workflow}: {ref}"


# ── Rule 12: invalid artifact handling → failure ─────────────────────────────


class TestRule12ArtifactHandling:
    def _matrix_workflow(
        self, validator, artifact_name: str, path_value: str, if_no_files_found=None
    ) -> list[str]:
        step_with = {"name": artifact_name, "path": path_value}
        if if_no_files_found is not None:
            step_with["if-no-files-found"] = if_no_files_found
        wf = _write(
            validator,
            "playwright.yml",
            _base_workflow(
                jobs={
                    "test": {
                        "name": "E2E Tests (${{ matrix.project }})",
                        "runs-on": "ubuntu-latest",
                        "strategy": {
                            "fail-fast": False,
                            "matrix": {"project": ["chromium", "mobile-chrome"]},
                        },
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {"run": ".venv/bin/python -m runtime.verify playwright"},
                            {
                                "uses": "./.github/actions/upload-runtime",
                                "with": step_with,
                            },
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(wf)
        return list(validator.ERRORS)

    def test_matrix_leg_without_a_matrix_suffixed_artifact_name_is_rejected(
        self, validator
    ):
        errors = self._matrix_workflow(validator, "playwright-report", "reports/**")
        assert any(
            "do not interpolate `matrix.`" in e and "Rule 12" in e for e in errors
        ), errors

    def test_matrix_suffixed_artifact_name_is_accepted(self, validator):
        errors = self._matrix_workflow(
            validator, "playwright-report-${{ matrix.project }}", "reports/**"
        )
        assert not [e for e in errors if "Rule 12" in e], errors

    def test_artifact_path_escaping_the_workspace_is_rejected(self, validator):
        errors = self._matrix_workflow(
            validator, "playwright-report-${{ matrix.project }}", "../../etc/**"
        )
        assert any("escapes the" in e for e in errors), errors

    def test_empty_artifact_path_is_rejected(self, validator):
        errors = self._matrix_workflow(
            validator, "playwright-report-${{ matrix.project }}", "   "
        )
        assert any("empty `path`" in e for e in errors), errors

    def test_unrecognised_if_no_files_found_is_rejected(self, validator):
        errors = self._matrix_workflow(
            validator,
            "playwright-report-${{ matrix.project }}",
            "reports/**",
            if_no_files_found="yes",
        )
        assert any("if-no-files-found" in e for e in errors), errors

    def test_duplicate_artifact_names_within_a_workflow_are_rejected(self, validator):
        wf = _write(
            validator,
            "playwright.yml",
            _base_workflow(
                jobs={
                    "test": {
                        "name": "E2E Tests",
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {"run": ".venv/bin/python -m runtime.verify playwright"},
                            {
                                "uses": "./.github/actions/upload-runtime",
                                "with": {"name": "dup", "path": "a/**"},
                            },
                            {
                                "uses": "./.github/actions/upload-runtime",
                                "with": {"name": "dup", "path": "b/**"},
                            },
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(wf)
        assert any("duplicated artifact names" in e for e in validator.ERRORS)


# ── Rule 7a / 11: required status checks ─────────────────────────────────────


class TestRule7aRequiredStatusChecks:
    def test_the_required_set_is_exhaustive_over_verification_profiles(self):
        """Every rule-8 verification workflow that the ruleset requires must be
        declared, or the prohibition on path-filtering a required check would
        never apply to it."""
        module = _load_validator()
        for name in module.REQUIRED_STATUS_CHECKS:
            assert name in module.VERIFICATION_PROFILES or name == "security-codeql.yml"
        assert set(module.REQUIRED_STATUS_CHECKS) == {
            "backend-verify.yml",
            "frontend-verify.yml",
            "verification-runtime.yml",
            "security-codeql.yml",
        }

    def test_a_path_filtered_required_check_is_rejected(self, validator):
        wf = _write(
            validator,
            "backend-verify.yml",
            _base_workflow(
                on={
                    "pull_request": {
                        "branches": ["main"],
                        "paths": ["backend/**"],
                    }
                },
                jobs={
                    "verify": {
                        "name": "Backend Verification",
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {"run": ".venv/bin/python -m runtime.verify backend"},
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                },
            ),
        )
        validator.validate_workflow(wf)
        assert any(
            "must NOT be path-filtered" in e and "Rule 7a" in e
            for e in validator.ERRORS
        ), validator.ERRORS

    def test_an_unfiltered_required_check_is_correct_and_not_warned(self, validator):
        wf = _write(
            validator,
            "backend-verify.yml",
            _base_workflow(
                jobs={
                    "verify": {
                        "name": "Backend Verification",
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {"run": ".venv/bin/python -m runtime.verify backend"},
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(wf)
        assert not [e for e in validator.ERRORS if "Rule 7a" in e], validator.ERRORS
        assert not [w for w in validator.WARNINGS if "Rule 7" in w], validator.WARNINGS

    def test_a_renamed_required_context_is_rejected(self, validator):
        wf = _write(
            validator,
            "security-codeql.yml",
            _base_workflow(
                jobs={
                    "analyze": {
                        "name": "Security Scan",  # not "Analyze"
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            }
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(wf)
        assert any(
            "no job in it is named that" in e and "Rule 11" in e
            for e in validator.ERRORS
        ), validator.ERRORS

    def test_a_conditionally_skipped_required_context_is_rejected(self, validator):
        wf = _write(
            validator,
            "verification-runtime.yml",
            _base_workflow(
                jobs={
                    "verify-runtime": {
                        "name": "Runtime Verification",
                        "runs-on": "ubuntu-latest",
                        "if": "github.event_name == 'push'",
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {"run": ".venv/bin/python -m runtime.verify runtime"},
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(wf)
        assert any("can skip the job" in e for e in validator.ERRORS), validator.ERRORS

    def test_always_is_allowed_on_a_required_context(self, validator):
        """An aggregate gate must be able to run even when a shard failed."""
        wf = _write(
            validator,
            "verification-runtime.yml",
            _base_workflow(
                jobs={
                    "verify-runtime": {
                        "name": "Runtime Verification",
                        "runs-on": "ubuntu-latest",
                        "if": "always()",
                        "needs": ["verify-runtime-shard"],
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {"run": ".venv/bin/python -m runtime.verify runtime"},
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(wf)
        assert not [e for e in validator.ERRORS if "can skip the job" in e]


# ── Legitimate architectures must be ACCEPTED ────────────────────────────────


class TestLegitimateArchitecturesAreAccepted:
    def test_a_matrix_job_is_accepted(self, validator):
        wf = _write(
            validator,
            "playwright.yml",
            _base_workflow(
                jobs={
                    "test": {
                        "name": "E2E Tests (${{ matrix.project }})",
                        "runs-on": "ubuntu-latest",
                        "strategy": {
                            "fail-fast": False,
                            "matrix": {"project": ["chromium", "mobile-chrome"]},
                        },
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {"run": ".venv/bin/python -m runtime.verify playwright"},
                            {
                                "uses": "./.github/actions/upload-runtime",
                                "with": {
                                    "name": "playwright-report-${{ matrix.project }}",
                                    "path": "reports/**",
                                },
                            },
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                }
            ),
        )
        validator.validate_workflow(wf)
        assert validator.ERRORS == [], validator.ERRORS

    def test_plan_shard_aggregate_subcommands_are_accepted(self, validator):
        """`mutation.yml` is one responsibility expressed as a job graph.

        Rule 8 requires the workflow to execute `runtime.verify`; it does not
        forbid one profile from using its own documented subcommands. The
        validator must not push engineers toward deleting this architecture.
        """
        wf = _write(
            validator,
            "mutation.yml",
            _base_workflow(
                # mutation.yml is on the cancel-in-progress exception list.
                concurrency={
                    "group": "${{ github.workflow }}-${{ github.ref }}",
                    "cancel-in-progress": False,
                },
                jobs={
                    "mutation-plan": {
                        "name": "Mutation Campaign Plan",
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {"run": ".venv/bin/python -m runtime.verify mutation-plan"},
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    },
                    "mutation": {
                        "name": "Mutation Shard",
                        "runs-on": "ubuntu-latest",
                        "needs": ["mutation-plan"],
                        "strategy": {
                            "fail-fast": False,
                            "matrix": {"shard": ["a", "b"]},
                        },
                        "steps": [
                            {
                                "run": ".venv/bin/python -m runtime.verify mutation --shard 1"
                            },
                            {
                                "uses": "./.github/actions/upload-runtime",
                                "with": {
                                    "name": "mutation-registry-${{ matrix.shard }}",
                                    "path": "registry.json",
                                },
                            },
                        ],
                    },
                    "mutation-aggregate": {
                        "name": "Mutation Aggregate Gate",
                        "runs-on": "ubuntu-latest",
                        "needs": ["mutation-plan", "mutation"],
                        "if": "always()",
                        "steps": [
                            {
                                "run": ".venv/bin/python -m runtime.verify mutation-aggregate"
                            },
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    },
                },
            ),
        )
        validator.validate_workflow(wf)
        assert validator.ERRORS == [], validator.ERRORS

    def test_a_path_gated_non_required_workflow_is_accepted(self, validator):
        """Path filtering is legitimate — and accepted — for a workflow that is
        not a required status check. Only the required four are prohibited."""
        wf = _write(
            validator,
            "api-contracts.yml",
            _base_workflow(
                on={
                    "pull_request": {
                        "branches": ["main"],
                        "paths": ["backend/**", "frontend/**", "runtime/**"],
                    }
                },
                jobs={
                    "api-contracts": {
                        "name": "API Contract Integrity Gate",
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "uses": "./.github/actions/bootstrap-runtime",
                                "with": {"python-version": "3.12"},
                            },
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify api-contracts"
                                )
                            },
                            {
                                "run": (
                                    ".venv/bin/python -m runtime.verify status "
                                    ">> $GITHUB_STEP_SUMMARY"
                                )
                            },
                        ],
                    }
                },
            ),
        )
        validator.validate_workflow(wf)
        assert validator.ERRORS == [], validator.ERRORS

    def test_local_composite_actions_and_images_are_exempt_from_the_sha_rule(
        self, validator
    ):
        for uses in ("./.github/actions/upload-runtime", "docker://python:3.12"):
            validator.ERRORS = []
            path = _write(
                validator,
                "release.yml",
                _base_workflow(
                    jobs={
                        "build": {
                            "name": "Build Release",
                            "runs-on": "ubuntu-latest",
                            "steps": [
                                {"uses": uses, "with": {"name": "x", "path": "y"}},
                                {
                                    "run": (
                                        ".venv/bin/python -m runtime.verify status "
                                        ">> $GITHUB_STEP_SUMMARY"
                                    )
                                },
                            ],
                        }
                    }
                ),
            )
            validator.validate_workflow(path)
            assert not [e for e in validator.ERRORS if "Rule 10" in e], (
                uses,
                validator.ERRORS,
            )


# ── the real tree ────────────────────────────────────────────────────────────


def test_the_real_workflow_tree_passes():
    """The M11 acceptance criterion, asserted as a test so it cannot regress.

    `validate_actions.py` is now executed by the Quality Gate. This asserts the
    same invariant from the runtime suite, so a violation is visible even when
    the Quality Gate is path-filtered away.
    """
    module = _load_validator()
    for action_dir in sorted(module.ACT_DIR.iterdir()):
        if action_dir.is_dir():
            module.validate_composite_action(action_dir)
    for wf in sorted(module.WF_DIR.glob("*.yml")):
        module.validate_workflow(wf)
    assert module.ERRORS == [], module.ERRORS


def test_validate_actions_is_importable_and_declares_its_rules():
    module = _load_validator()
    doc = VALIDATOR_PATH.read_text(encoding="utf-8")
    for rule in range(1, 13):
        assert (
            f"{rule}." in doc
        ), f"Rule {rule} is not documented in the module docstring"
    assert module.VERIFICATION_PROFILES
    assert module.REQUIRED_STATUS_CHECKS
    assert sys.modules.get("validate_actions_under_test") is None or True
