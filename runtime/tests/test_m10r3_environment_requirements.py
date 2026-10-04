"""M10-R3 / Checkpoint B1 — environment requirements are declared, resolved and enforced.

The defect these tests exist to prevent is precise and was measured: a field named
``required_environment`` was declared, populated 25 times, serialised — and read by
nothing outside its own ``to_dict()``. The only real checker, ``verify_prerequisites``,
read a *different* field on a *different* class, verified repository paths only, and
explicitly skipped five of its own values so it never once checked a tool, a version,
or an environment variable.

The consequence in CI was that a missing environment variable surfaced as an opaque
non-zero exit minutes later, with the real cause in a log nobody was watching. These
tests assert the opposite: a missing requirement is a *named* failure, decided before
any process is spawned.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification.execution_orchestrator import (
    PLACEHOLDER_TOKENS,
    ExecutionContext,
    ExecutionPlan,
    ExecutionTaskSpec,
    RequirementSyntaxError,
    _parse_requirement,
    verify_environment_requirement,
    verify_task_environment,
)
from runtime.foundation.verification.env import child_process_env

REPO_ROOT = Path(__file__).resolve().parents[2]


def _ctx(**kw) -> ExecutionContext:
    kw.setdefault("workspace", str(REPO_ROOT))
    return ExecutionContext(**kw)


# ---------------------------------------------------------------------------
# Form parsing — the three forms must be syntactically distinguishable
# ---------------------------------------------------------------------------


class TestRequirementFormParsing:
    @pytest.mark.parametrize(
        ("raw", "form", "subject", "expected"),
        [
            # PATH — inferred from a slash or a leading dot
            (".venv", "path", ".venv", ""),
            ("backend/pyproject.toml", "path", "backend/pyproject.toml", ""),
            (".git", "path", ".git", ""),
            # TOOL — lowercase bare name
            ("pytest", "tool", "pytest", ""),
            ("coverage", "tool", "coverage", ""),
            ("git", "tool", "git", ""),
            # TOOL with a pinned version. Note '==' must win over '='.
            ("mutmut==3.7.0", "tool_version", "mutmut", "3.7.0"),
            # VARIABLE — SHOUTING_SNAKE, optionally with a required value
            ("FINANCE_DB_PATH", "variable", "FINANCE_DB_PATH", ""),
            (
                "PLAYWRIGHT_PROJECT=chromium",
                "variable",
                "PLAYWRIGHT_PROJECT",
                "chromium",
            ),
            # Explicit prefixes always win over inference
            ("tool:mutmut==3.7.0", "tool_version", "mutmut", "3.7.0"),
            ("path:.github/scripts/run_property_tests.sh", "path", ".github/scripts/run_property_tests.sh", ""),
            ("env:FINANCE_DB_PATH", "variable", "FINANCE_DB_PATH", ""),
            ("env:FOO=@workspace/backend", "variable", "FOO", "@workspace/backend"),
            # An explicit prefix may also *force* a form inference would deny
            ("env:pytest", "variable", "pytest", ""),
        ],
    )
    def test_form_is_parsed_unambiguously(self, raw, form, subject, expected):
        assert _parse_requirement(raw) == (form, subject, expected)

    @pytest.mark.parametrize(
        "raw",
        ["", "   ", "env:", "tool:", "==3.7.0", "=value", "BAD-NAME=1"],
    )
    def test_malformed_requirement_is_rejected_not_guessed(self, raw):
        """A requirement that cannot be parsed must raise, never fall through.

        Silently coercing a malformed requirement into a passing check is the exact
        shape of the defect being removed: a declaration that looks enforced and is
        not.
        """
        with pytest.raises(RequirementSyntaxError):
            _parse_requirement(raw)

    def test_requirement_syntax_error_is_reported_as_a_failure_not_raised(self):
        """The batch API converts a bad declaration into a named failure.

        One malformed entry must not abort validation of the rest of the plan —
        but it must also not be dropped.
        """
        failures = verify_task_environment(
            "exec-9999", ["==bad", "pytest"], _ctx(), dict(child_process_env())
        )
        assert [f.form for f in failures] == ["syntax"]
        assert failures[0].task_id == "exec-9999"
        assert "exec-9999" in failures[0].render()


# ---------------------------------------------------------------------------
# Placeholder resolution — the constrained resolver
# ---------------------------------------------------------------------------


class TestPlaceholderResolution:
    def test_every_placeholder_resolves_from_provenance(self):
        ctx = _ctx(
            leg="chromium-visual",
            shard=3,
            shard_count=7,
            plan_id="execplan-abc",
            execution_id="run-42",
        )
        for token in PLACEHOLDER_TOKENS:
            assert ctx.placeholder_value(token) != "" or token in {"leg"}

    @pytest.mark.parametrize(
        ("token", "expected"),
        [
            ("shard", "3"),
            ("shard_count", "7"),
            ("plan_id", "execplan-abc"),
            ("execution_id", "run-42"),
            ("leg", "chromium-visual"),
        ],
    )
    def test_placeholder_values(self, token, expected):
        ctx = _ctx(
            leg="chromium-visual",
            shard=3,
            shard_count=7,
            plan_id="execplan-abc",
            execution_id="run-42",
        )
        assert ctx.placeholder_value(token) == expected

    def test_unknown_token_is_rejected_rather_than_left_literal(self):
        """An unexpanded ``@token`` in CI is indistinguishable from a correct value.

        Leaving it literal would let a leg run against the wrong path and report a
        green run. It must be a hard failure.
        """
        failure = verify_environment_requirement(
            "FOO=@nope/x", _ctx(), {"FOO": "anything"}
        )
        assert failure is not None
        assert failure.form == "syntax"
        assert "@nope" in failure.detail

    def test_partial_token_match_is_rejected(self):
        """``@shard_count`` must not be read as ``@shard`` followed by junk."""
        failure = verify_environment_requirement(
            "FOO=@shard_count_suffix", _ctx(), {"FOO": "x"}
        )
        assert failure is not None
        assert failure.form == "syntax"

    def test_at_sign_followed_by_a_non_token_is_a_hard_error(self):
        """Fail closed on any unrecognised ``@`` sequence.

        The resolver cannot distinguish ``user@host`` from an unexpanded
        ``@host``, and guessing wrong means a leg runs against the wrong path and
        reports green. Constrained means constrained: an unrecognised ``@token``
        is rejected rather than passed through.
        """
        failure = verify_environment_requirement("FOO=user@host", _ctx(), {"FOO": "x"})
        assert failure is not None
        assert failure.form == "syntax"

    def test_local_and_ci_leg_declarations_agree_for_the_same_obligation(self):
        """The point of the resolver: one declaration, correct in every context.

        A Playwright leg declares ``FINANCE_DB_PATH=@workspace/backend/data/e2e-$LEG.db``.
        Locally the leg id is empty and the value resolves without the suffix; in CI
        the leg supplies it. Both are correct *for their own leg*, which is what makes
        local execution a faithful reproduction rather than an approximation.
        """
        req = "FINANCE_DB_PATH=@workspace/backend/data/e2e.db"
        assert (
            verify_environment_requirement(
                req, _ctx(), {"FINANCE_DB_PATH": f"{REPO_ROOT}/backend/data/e2e.db"}
            )
            is None
        )
        # A leg that forgot to set its own variable fails by name, at second zero.
        assert (
            verify_environment_requirement(req, _ctx(leg="chromium-visual"), {})
        ) is not None


# ---------------------------------------------------------------------------
# Enforcement — every form is real
# ---------------------------------------------------------------------------


class TestRequirementEnforcement:
    def test_missing_tool_is_named(self):
        failure = verify_environment_requirement("definitely-not-a-real-tool", _ctx(), {})
        assert failure is not None
        assert failure.form == "tool"
        assert "definitely-not-a-real-tool" in failure.requirement

    def test_present_tool_passes(self):
        assert verify_environment_requirement("pytest", _ctx(), {}) is None

    def test_pinned_tool_version_satisfied(self):
        assert verify_environment_requirement("mutmut==3.7.0", _ctx(), {}) is None

    def test_pinned_tool_version_mismatch_names_both_sides(self):
        failure = verify_environment_requirement("mutmut==0.0.0", _ctx(), {})
        assert failure is not None
        assert failure.form == "tool_version"
        assert "0.0.0" in failure.detail
        assert "3.7.0" in failure.detail

    def test_version_probe_does_not_trust_a_broken_cli(self):
        """``mutmut --version`` raises in this repository.

        A ``--version``-only probe would therefore report the *correct* pin as a
        mismatch and manufacture a false prerequisite failure on every mutation
        revalidation task. Installed-distribution metadata must be preferred.
        """
        from runtime.foundation.verification.execution_orchestrator import (
            _tool_version_of,
        )

        assert _tool_version_of(REPO_ROOT / ".venv" / "bin" / "mutmut") == "3.7.0"

    def test_missing_path_is_named(self):
        failure = verify_environment_requirement("no/such/path", _ctx(), {})
        assert failure is not None
        assert failure.form == "path"

    def test_present_path_passes(self):
        assert verify_environment_requirement(".venv", _ctx(), {}) is None

    def test_unset_variable_is_named(self):
        failure = verify_environment_requirement("FINANCE_DB_PATH", _ctx(), {})
        assert failure is not None
        assert failure.form == "variable"
        assert "FINANCE_DB_PATH" in failure.detail
        assert "not set" in failure.detail

    def test_set_variable_passes(self):
        assert (
            verify_environment_requirement("FINANCE_DB_PATH", _ctx(), {"FINANCE_DB_PATH": "/x"})
            is None
        )

    def test_wrong_variable_value_is_named_with_both_values(self):
        failure = verify_environment_requirement(
            "PLAYWRIGHT_PROJECT=chromium", _ctx(), {"PLAYWRIGHT_PROJECT": "webkit"}
        )
        assert failure is not None
        assert "webkit" in failure.detail and "chromium" in failure.detail

    def test_multiple_failures_are_all_reported_not_just_the_first(self):
        """A preflight that stops at the first problem forces N round trips."""
        failures = verify_task_environment(
            "exec-0001",
            ["FINANCE_DB_PATH", "PLAYWRIGHT_PROJECT=chromium", "no-such-tool"],
            _ctx(),
            {},
        )
        assert len(failures) == 3
        assert all(f.task_id == "exec-0001" for f in failures)


# ---------------------------------------------------------------------------
# Consolidation — one field, not two
# ---------------------------------------------------------------------------


class TestFieldConsolidation:
    def test_spec_declares_required_environment_and_not_prerequisites(self):
        names = {f.name for f in ExecutionTaskSpec.__dataclass_fields__.values()}
        assert "required_environment" in names
        assert "prerequisites" not in names, (
            "the split between 'prerequisites' (paths only, and silently skipping "
            "five of its own values) and a never-read 'required_environment' is "
            "the duplication M10-R3 removed; do not reintroduce it"
        )

    def test_serialised_plan_emits_one_key(self):
        spec = _spec()
        d = spec.to_dict()
        assert d["required_environment"] == [".venv", "pytest", "FINANCE_DB_PATH"]
        assert "prerequisites" not in d

    def test_legacy_plan_key_is_folded_in_not_dropped(self):
        """A pre-M10-R3 plan must keep its declarations.

        Dropping them would silently convert a satisfied requirement into an
        unenforced one — the exact defect class this work removes.
        """
        legacy = {
            "task_id": "exec-0001",
            "source_task_id": "cp-1",
            "primary_capability": "c",
            "capabilities": ["c"],
            "verification_kind": "unit",
            "command": "true",
            "profile": "backend",
            "scope": "s",
            "is_mandatory": True,
            "is_escalation": False,
            "reason": "r",
            "origin": "control_plane",
            "prerequisites": [".venv", "backend/pyproject.toml"],
            "timeout_seconds": 600,
        }
        spec = ExecutionTaskSpec.from_dict(legacy)
        assert ".venv" in spec.required_environment
        assert "backend/pyproject.toml" in spec.required_environment

    def test_legacy_and_modern_keys_merge_without_duplicates(self):
        spec = ExecutionTaskSpec.from_dict(
            {
                **_spec().to_dict(),
                "prerequisites": [".venv", "FINANCE_DB_PATH", "extra"],
            }
        )
        assert spec.required_environment == (".venv", "pytest", "FINANCE_DB_PATH", "extra")

    def test_tuple_type_survives_both_paths(self):
        for payload in (_spec().to_dict(), {**_spec().to_dict(), "prerequisites": [".venv"]}):
            spec = ExecutionTaskSpec.from_dict(payload)
            assert isinstance(spec.required_environment, tuple)

    def test_plan_round_trips_through_json(self):
        """Serialise -> deserialise -> serialise must be byte-stable.

        This is what makes a ``plan.json`` an execution contract rather than a
        snapshot: a CI worker given the file executes exactly what the planner
        decided, including its requirements.
        """
        spec = _spec()
        once = spec.to_dict()
        twice = ExecutionTaskSpec.from_dict(json.loads(json.dumps(once))).to_dict()
        assert once == twice


# ---------------------------------------------------------------------------
# Enforcement on a real plan — before spawn, and it blocks
# ---------------------------------------------------------------------------


class TestPlanLevelEnforcement:
    def test_real_plan_passes_prerequisites(self):
        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionOrchestrator,
        )

        plan = _plan()
        ok, missing = ExecutionOrchestrator().verify_prerequisites(plan)
        assert ok, missing
        assert missing == []

    def test_unsatisfied_requirement_blocks_and_names_the_task(self):
        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionOrchestrator,
        )

        plan = _plan(requirements=("FINANCE_DB_PATH",))
        ok, missing = ExecutionOrchestrator().verify_prerequisites(plan, env={})
        assert not ok
        assert any("exec-0001" in m and "FINANCE_DB_PATH" in m for m in missing)

    def test_structured_failures_carry_form_and_task(self):
        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionOrchestrator,
        )

        failures = ExecutionOrchestrator().collect_requirement_failures(
            _plan(requirements=("PLAYWRIGHT_PROJECT=chromium",)), env={}
        )
        assert len(failures) == 1
        assert failures[0].form == "variable"
        assert failures[0].task_id == "exec-0001"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _spec(**over) -> ExecutionTaskSpec:
    base = dict(
        task_id="exec-0001",
        source_task_id="cp-1",
        primary_capability="cap",
        capabilities=("cap",),
        verification_kind="unit",
        command="true",
        profile="backend",
        scope="repo",
        is_mandatory=True,
        is_escalation=False,
        reason="r",
        origin="control_plane",
        required_environment=(".venv", "pytest", "FINANCE_DB_PATH"),
        timeout_seconds=600,
    )
    base.update(over)
    return ExecutionTaskSpec(**base)


def _plan(*, requirements: tuple[str, ...] = (".venv",)) -> ExecutionPlan:
    from runtime.foundation.verification.execution_orchestrator import (
        RepositoryFingerprint,
    )

    fp = RepositoryFingerprint.capture()
    return ExecutionPlan(
        plan_id="execplan-test",
        generated_at="2026-10-04T00:00:00+00:00",
        rationale="test",
        repository_fingerprint=fp,
        plan_fingerprint="f" * 64,
        changed_files=["backend/src/x.py"],
        source_plan_id="cpplan-test",
        affected_capabilities=["cap"],
        affected_components=["backend"],
        invalidated_evidence=[],
        reusable_evidence=[],
        tasks=[_spec(required_environment=requirements)],
        escalation_conditions=[],
        measurement_requirements=[],
        certification_requirements=[],
    )
