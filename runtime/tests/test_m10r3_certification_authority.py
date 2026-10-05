"""M10-R3 / Checkpoint B2 — one certification authority, six producers.

Before B2 the repository had six ways to execute a verification obligation and only
one of them could produce a verdict. ``verify check`` / ``verify run`` built an
``ExecutionPlan``, bracketed execution with a repository fingerprint, and classified
the result into a 7-value ``FinalDecision``. The other five — profile aliases,
obligation legs, runtime shards, Playwright legs and mutation — used the same
subprocess worker and then reported "certified" whenever no shell happened to exit
non-zero. ``_check_fingerprint_integrity`` had exactly one call site.

A green ``verify backend`` was therefore evidence that no shell exited non-zero. It
was not evidence that the repository was unchanged. These tests pin the difference.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification.execution_orchestrator import (
    _DECISION_EXIT_CODES,
    CertificationRun,
    CompletionState,
    FinalDecision,
    FingerprintDrift,
    ObligationOutcome,
    RepositoryFingerprint,
    decide_final_outcome,
)

# ---------------------------------------------------------------------------
# The classifier: one precedence, no second opinion
# ---------------------------------------------------------------------------


class TestDecisionPrecedence:
    def test_all_pass_certifies(self):
        decision, _ = decide_final_outcome(
            [ObligationOutcome("a", CompletionState.PASS)]
        )
        assert decision is FinalDecision.CERTIFIED

    def test_no_outcomes_is_not_a_pass(self):
        """An execution that recorded nothing has certified nothing.

        This must not be expressible as green. It is the case that catches a crashed
        or short-circuited runner.
        """
        with CertificationRun("p") as run:
            pass
        decision, reason = run.decide()
        assert decision is FinalDecision.NOT_CERTIFIABLE
        assert "nothing was certified" in reason
        assert run.exit_code() != 0

    def test_infrastructure_outranks_a_mandatory_failure(self):
        """You cannot diagnose a test failure in a run that could not be measured."""
        decision, _ = decide_final_outcome(
            [
                ObligationOutcome("a", CompletionState.FAILED),
                ObligationOutcome("b", CompletionState.INFRASTRUCTURE),
            ]
        )
        assert decision is FinalDecision.INFRASTRUCTURE_BLOCKED

    def test_timeout_outranks_a_mandatory_failure(self):
        decision, _ = decide_final_outcome(
            [
                ObligationOutcome("a", CompletionState.FAILED),
                ObligationOutcome("b", CompletionState.TIMEOUT),
            ]
        )
        assert decision is FinalDecision.TIMEOUT_BLOCKED

    def test_drift_outranks_a_mandatory_failure(self):
        """Once the tree has moved, a failing test's result is not attributable.

        Reporting ``DIAGNOSTIC`` here would send an operator to fix a test when the
        actual fault is that the repository changed underneath the run.
        """
        decision, _ = decide_final_outcome(
            [ObligationOutcome("a", CompletionState.FAILED)],
            fingerprint_stable=False,
            fingerprint_note="before=aaa after=bbb",
        )
        assert decision is FinalDecision.VALIDATION_BLOCKED

    def test_drift_reason_carries_both_fingerprints(self):
        _, reason = decide_final_outcome(
            [ObligationOutcome("a", CompletionState.PASS)],
            fingerprint_stable=False,
            fingerprint_note="before=aaa after=bbb",
        )
        assert "aaa" in reason and "bbb" in reason

    def test_scope_state_is_treated_as_drift(self):
        """The orchestrator reports drift as a SCOPE record; the fan-outs as a bracket.

        Both must reach the same decision, or "the tree moved" means two different
        things depending on which topology noticed.
        """
        decision, _ = decide_final_outcome(
            [ObligationOutcome("a", CompletionState.SCOPE)]
        )
        assert decision is FinalDecision.VALIDATION_BLOCKED

    def test_optional_failure_does_not_block(self):
        decision, _ = decide_final_outcome(
            [
                ObligationOutcome("a", CompletionState.PASS),
                ObligationOutcome("b", CompletionState.FAILED, is_mandatory=False),
            ]
        )
        assert decision is FinalDecision.CERTIFIED

    def test_mandatory_failure_is_diagnostic_and_names_the_obligation(self):
        decision, reason = decide_final_outcome(
            [ObligationOutcome("exec-0004", CompletionState.FAILED)]
        )
        assert decision is FinalDecision.DIAGNOSTIC
        assert "exec-0004" in reason

    def test_authorization_is_its_own_decision(self):
        decision, _ = decide_final_outcome(
            [ObligationOutcome("a", CompletionState.AUTHORIZATION_REQUIRED)]
        )
        assert decision is FinalDecision.AWAITING_AUTHORIZATION

    @pytest.mark.parametrize(
        ("outcome", "expected_exit"),
        [
            (CompletionState.FAILED, 1),
            (CompletionState.TIMEOUT, 124),
            (CompletionState.INFRASTRUCTURE, 3),
            (CompletionState.SCOPE, 5),
        ],
    )
    def test_every_blocked_state_has_its_documented_nonzero_exit(
        self, outcome, expected_exit
    ):
        with CertificationRun("p") as run:
            run.record("a", outcome)
        assert run.exit_code() == expected_exit
        assert (
            run.exit_code() != 0
        ), f"{outcome} must never be expressible as a green exit status"

    def test_pass_is_the_only_zero(self):
        with CertificationRun("p") as run:
            run.record("a", CompletionState.PASS)
        assert run.exit_code() == 0

    def test_exit_codes_are_distinct_per_blocked_decision_class(self):
        """A CI leg must be able to tell the failure modes apart from the status alone.

        The single documented collision is NOT_CERTIFIABLE / DIAGNOSTIC sharing 1:
        both mean "the run happened and something failed", and neither is an
        infrastructure fault. They are distinguished by the ``decision`` string in the
        certification document, which is written on every path.
        """
        blocked = {
            FinalDecision.NOT_CERTIFIABLE: 1,
            FinalDecision.DIAGNOSTIC: 1,
            FinalDecision.AWAITING_AUTHORIZATION: 6,
            FinalDecision.INFRASTRUCTURE_BLOCKED: 3,
            FinalDecision.TIMEOUT_BLOCKED: 124,
            FinalDecision.VALIDATION_BLOCKED: 5,
        }
        assert _DECISION_EXIT_CODES[FinalDecision.CERTIFIED] == 0
        for decision, expected in blocked.items():
            assert _DECISION_EXIT_CODES[decision] == expected
        assert 0 not in blocked.values(), "no blocked decision may exit 0"
        # exactly one collision, and it is the documented one
        assert len(set(blocked.values())) == len(blocked) - 1

    def test_timeout_keeps_the_gnu_timeout_exit_convention(self):
        """124 is GNU ``timeout``'s code and is read as such by CI and by humans.

        Renumbering it would be a gratuitous break; the value of distinct codes is
        realised by the *other* modes, not by discarding a convention.
        """
        assert _DECISION_EXIT_CODES[FinalDecision.TIMEOUT_BLOCKED] == 124

    def test_authorization_does_not_collide_with_argparse_usage_error(self):
        assert _DECISION_EXIT_CODES[FinalDecision.AWAITING_AUTHORIZATION] != 2


# ---------------------------------------------------------------------------
# The bracket: the anti-tamper invariant the five topologies were missing
# ---------------------------------------------------------------------------


class TestFingerprintBracket:
    def test_a_clean_run_reports_a_stable_bracket(self):
        with CertificationRun("p") as run:
            run.record("a", CompletionState.PASS)
        assert run.fingerprint_stable is True
        assert run.fingerprint_before is not None
        assert run.fingerprint_after is not None
        assert run.fingerprint_before.matches(run.fingerprint_after)

    def test_an_unclosed_bracket_cannot_assert_stability(self):
        """A bracket that only closes on the happy path is not an invariant.

        ``__enter__`` without ``__exit__`` happens on any hard exit. Reporting
        "stable" there would let a crashed runner certify silently.
        """
        run = CertificationRun("p")
        run.__enter__()
        run.record("a", CompletionState.PASS)
        assert run.fingerprint_stable is False

    def test_drift_is_detected_and_blocks_certification(self, tmp_path):
        """A file inside the hashed set is modified during the run.

        The verdict must become VALIDATION_BLOCKED with both fingerprints in the
        reason. This is the invariant the five plan-less topologies did not have.
        """
        target = (
            Path(__file__).resolve().parents[2]
            / "backend"
            / "src"
            / "engines"
            / "loan_engine"
            / "emi.py"
        )
        original = target.read_bytes()
        try:
            with CertificationRun("drift") as run:
                run.record("a", CompletionState.PASS)
                target.write_bytes(original + b"\n# M10-R3 drift probe\n")
            assert run.fingerprint_stable is False
            decision, reason = run.decide()
            assert decision is FinalDecision.VALIDATION_BLOCKED
            # Either wording is acceptable; both must name the fault and carry the
            # two fingerprints so an operator can compare them by hand.
            assert "drift" in reason or "fingerprint" in reason
            assert run.fingerprint_before.fingerprint[:12] in reason
            assert run.fingerprint_after.fingerprint[:12] in reason
        finally:
            target.write_bytes(original)

    def test_strict_mode_raises_on_drift(self):
        target = (
            Path(__file__).resolve().parents[2]
            / "backend"
            / "src"
            / "engines"
            / "loan_engine"
            / "emi.py"
        )
        original = target.read_bytes()
        try:
            with pytest.raises(FingerprintDrift):
                with CertificationRun("drift", strict=True) as run:
                    run.record("a", CompletionState.PASS)
                    target.write_bytes(original + b"\n# M10-R3 drift probe\n")
        finally:
            target.write_bytes(original)

    def test_non_strict_mode_does_not_raise(self):
        """Drift normally *records*; it does not discard useful partial evidence."""
        target = (
            Path(__file__).resolve().parents[2]
            / "backend"
            / "src"
            / "engines"
            / "loan_engine"
            / "emi.py"
        )
        original = target.read_bytes()
        try:
            with CertificationRun("drift") as run:
                run.record("a", CompletionState.PASS)
                target.write_bytes(original + b"\n# M10-R3 drift probe\n")
            assert run.decision is FinalDecision.VALIDATION_BLOCKED
        finally:
            target.write_bytes(original)

    def test_the_bracket_never_swallows_an_exception(self):
        """``__exit__`` returns False so the body's exception still propagates."""
        with pytest.raises(RuntimeError, match="body failed"):
            with CertificationRun("p"):
                raise RuntimeError("body failed")

    def test_the_bracket_closes_even_when_the_body_raises(self):
        run = CertificationRun("p")
        with pytest.raises(RuntimeError):
            with run:
                raise RuntimeError("boom")
        assert run.fingerprint_after is not None
        assert run.fingerprint_stable is True


# ---------------------------------------------------------------------------
# The fail-open hole this work closed
# ---------------------------------------------------------------------------


class TestNoFailOpen:
    def test_an_exception_in_a_task_body_is_not_a_pass(self):
        """The defect B2 removed, pinned so it cannot come back.

        ``execute_tasks_in_parallel`` returns the *exception object* when a task body
        raises. The pre-B2 verdict logic read only ``dict`` outcomes, so an
        all-exception run produced no detectable failure, returned exit code 0, and
        recorded ``final_decision="certified"`` — a run that executed nothing
        reporting success.

        This is not hypothetical: ``test_profile_alias_returns_the_real_profile_exit_code``
        was passing at HEAD for exactly this reason. Its stub pinned an exact keyword
        signature, did not match the real call, and every task raised.
        """
        with CertificationRun("p") as run:
            run.record(
                "TypeError", CompletionState.INFRASTRUCTURE, detail="task body raised"
            )
        assert run.decision is FinalDecision.INFRASTRUCTURE_BLOCKED
        assert run.exit_code() != 0

    def test_profile_alias_survives_an_all_exception_run(self):
        """End-to-end: a profile whose every task raises must not certify.

        Guards the real entry point, not just the classifier.
        """
        from unittest.mock import patch

        from runtime.foundation.verification.control_plane_facade import (
            _run_profile_alias,
        )
        from runtime.foundation.verification.parallel_executor import CommandResult

        def _fake_worker(command, *, stdout_path, stderr_path, timeout_seconds, **kw):
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text("", encoding="utf-8")
            stderr_path.write_text("", encoding="utf-8")
            return CommandResult(
                command=command,
                exit_code=0,
                timed_out=False,
                infra_error=None,
                stdout="",
                stderr="",
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                duration_seconds=0.0,
            )

        with patch(
            "runtime.foundation.verification.parallel_executor."
            "run_streaming_command",
            side_effect=_fake_worker,
        ):
            assert _run_profile_alias("quick") == 0

        # Now the same profile with every task raising.
        with patch(
            "runtime.foundation.verification.parallel_executor."
            "run_streaming_command",
            side_effect=RuntimeError("worker exploded"),
        ):
            rc = _run_profile_alias("quick")
        assert rc != 0, (
            "a profile in which every task raised reported success — the fail-open "
            "certification hole has reopened"
        )


# ---------------------------------------------------------------------------
# One document shape for every topology
# ---------------------------------------------------------------------------


class TestCertificationDocument:
    def test_document_carries_decision_reason_bracket_and_obligations(self):
        with CertificationRun("execplan-x") as run:
            run.record("exec-0001", CompletionState.PASS)
            run.record("exec-0004", CompletionState.FAILED, detail="exit 1")
        doc = run.to_dict()
        assert doc["schema"] == "m10r3-certification-run/v1"
        assert doc["decision"] == FinalDecision.DIAGNOSTIC.value
        assert doc["exit_code"] == 1
        assert doc["fingerprint_stable"] is True
        assert doc["fingerprint_before"]["fingerprint"]
        assert doc["fingerprint_after"]["fingerprint"]
        assert [o["task_id"] for o in doc["obligations"]] == ["exec-0001", "exec-0004"]
        assert doc["obligations"][1]["detail"] == "exit 1"

    def test_document_is_json_serialisable(self):
        with CertificationRun("p") as run:
            run.record("a", CompletionState.PASS)
        assert json.loads(json.dumps(run.to_dict()))["decision"] == "certified"

    def test_records_the_repository_sha_it_ran_against(self):
        with CertificationRun("p") as run:
            run.record("a", CompletionState.PASS)
        assert (
            run.fingerprint_before.repository_sha
            == RepositoryFingerprint.capture().repository_sha
        )

    def test_the_profile_alias_publishes_one(self, tmp_path, monkeypatch):
        """Every topology writes the same document to the same place."""
        from unittest.mock import patch

        from runtime.foundation.verification import control_plane_facade as facade
        from runtime.foundation.verification.parallel_executor import CommandResult

        def _fake_worker(command, *, stdout_path, stderr_path, timeout_seconds, **kw):
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text("", encoding="utf-8")
            stderr_path.write_text("", encoding="utf-8")
            return CommandResult(
                command=command,
                exit_code=0,
                timed_out=False,
                infra_error=None,
                stdout="",
                stderr="",
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                duration_seconds=0.0,
            )

        root = tmp_path / "runtime" / "generated"
        monkeypatch.setattr(facade, "REPO_ROOT", tmp_path)
        with patch(
            "runtime.foundation.verification.parallel_executor."
            "run_streaming_command",
            side_effect=_fake_worker,
        ):
            facade._run_profile_alias("quick")
        published = root / "certification" / "quick.json"
        assert published.exists(), (
            "the profile alias did not publish a certification document; six "
            "topologies reporting six shapes is the defect B2 removes"
        )
        doc = json.loads(published.read_text())
        assert doc["topology"] == "quick"
        assert doc["schema"] == "m10r3-certification-run/v1"
        assert doc["fingerprint_stable"] is True


# ---------------------------------------------------------------------------
# The fan-out gates must consume the bracket, or the field is inert again
# ---------------------------------------------------------------------------


class TestFanOutGatesConsumeTheBracket:
    def test_a_passed_shard_that_drifted_is_refused(self):
        from runtime.foundation.verification.runtime_shards import (
            ShardResult,
            verify_shards,
        )

        shard = ShardResult(
            shard_id="runtime-tests-shard-0",
            status="passed",
            exit_code=0,
            duration_seconds=1.0,
            decision="certified",
            fingerprint_before={"fingerprint": "a" * 64},
            fingerprint_after={"fingerprint": "b" * 64},
            fingerprint_stable=False,
        )
        problems = verify_shards(1, [shard])
        assert problems, "a shard that reported passed on a moved tree was certified"
        assert "fingerprint changed" in problems[0]

    def test_a_legacy_shard_document_is_refused_not_laundered(self):
        """A document from a pre-B2 producer has no bracket.

        It must read as *unstable*. Defaulting it to stable would make the new field
        opt-in — exactly the "declared but inert" failure this milestone removes.
        """
        from runtime.foundation.verification.runtime_shards import (
            ShardResult,
            verify_shards,
        )

        legacy = ShardResult.from_dict(
            {
                "shard_id": "runtime-tests-shard-0",
                "status": "passed",
                "exit_code": 0,
                "duration_seconds": 1.0,
            }
        )
        problems = verify_shards(1, [legacy])
        assert problems
        assert "no fingerprint bracket" in problems[0]

    def test_a_passed_leg_that_drifted_is_refused(self):
        from runtime.foundation.verification.profile_tasks import (
            ProfileLegResult,
            expected_obligation_ids,
            verify_legs,
        )

        task_id = expected_obligation_ids("backend")[0]
        leg = ProfileLegResult(
            profile="backend",
            task_id=task_id,
            task_name="x",
            status="passed",
            exit_code=0,
            duration_seconds=1.0,
            decision="certified",
            fingerprint_before={"fingerprint": "a" * 64},
            fingerprint_after={"fingerprint": "b" * 64},
            fingerprint_stable=False,
        )
        problems = verify_legs("backend", [leg])
        assert any("fingerprint changed" in p for p in problems)

    def test_a_legacy_leg_document_is_refused(self):
        from runtime.foundation.verification.profile_tasks import (
            ProfileLegResult,
            expected_obligation_ids,
            verify_legs,
        )

        task_id = expected_obligation_ids("backend")[0]
        leg = ProfileLegResult(
            profile="backend",
            task_id=task_id,
            task_name="x",
            status="passed",
            exit_code=0,
            duration_seconds=1.0,
        )
        problems = verify_legs("backend", [leg])
        assert any("no fingerprint bracket" in p for p in problems)

    def test_the_readers_populate_the_bracket(self, tmp_path):
        """A reader that dropped the new fields would make the gate refuse everything
        — or, worse, a future refactor could drop the check. Assert the plumbing."""
        from runtime.foundation.verification.runtime_shards import (
            ShardResult,
            read_shard_results,
        )

        shard = ShardResult(
            shard_id="runtime-tests-shard-0",
            status="passed",
            exit_code=0,
            duration_seconds=1.0,
            decision="certified",
            decision_reason="ok",
            fingerprint_before={"fingerprint": "a" * 64},
            fingerprint_after={"fingerprint": "a" * 64},
            fingerprint_stable=True,
        )
        (tmp_path / "shard-0.json").write_text(json.dumps(shard.to_dict()))
        results, absent, malformed, rejected = read_shard_results(tmp_path)
        assert (absent, malformed, rejected) == ([], [], [])
        assert results[0].fingerprint_stable is True
        assert results[0].decision == "certified"

    def test_a_malformed_document_is_still_reported_as_malformed(self, tmp_path):
        """``from_dict`` defaults missing keys, so the required-key check is explicit.

        Without it a document missing its identity would become a plausible-looking
        shard with an empty id, converting a producer fault into a confusing
        plan-mismatch report.
        """
        from runtime.foundation.verification.runtime_shards import read_shard_results

        (tmp_path / "shard-0.json").write_text(json.dumps({"status": "passed"}))
        results, absent, malformed, rejected = read_shard_results(tmp_path)
        assert results == []
        assert malformed and "KeyError" in malformed[0]

    def test_leg_reader_still_reports_malformed_documents(self, tmp_path):
        from runtime.foundation.verification.profile_tasks import read_leg_results

        (tmp_path / "leg-a.json").write_text(json.dumps({"status": "passed"}))
        # M10-R3: four-way since read_leg_results was aligned with read_shard_results.
        # Unpacking two here is exactly the mismatch that broke the Backend
        # Verification gate, and this test is how it reaches CI rather than a
        # workflow log.
        results, absent, malformed, rejected = read_leg_results(tmp_path)
        assert results == []
        assert malformed and "KeyError" in malformed[0]
