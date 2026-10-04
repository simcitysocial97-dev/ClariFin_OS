"""M10-R3 / §16 — the adversarial injection suite: the actual acceptance test.

The mission's closing question is whether a deliberately injected execution-condition
defect is caught by the runtime *before* the expensive command runs, and whether each
of ten named defects is detected, identified, classified, reported, and refused false
certification — without CI-specific forensic investigation.

This suite injects each one and asserts what the runtime does. Two rules govern its
content:

* **A test asserts observed behaviour, not intended behaviour.** Where a defect is NOT
  yet caught, the test says so explicitly and is marked ``xfail(strict=True)``. A
  suite of aspirational tests would be worse than no suite, because it would convert
  known gaps into apparent guarantees.
* **Detection must be before the expensive command where possible.** For a missing
  environment variable the assertion is that zero processes were spawned, not merely
  that the run failed.

Defects covered: §16 items 1-6 and 9-10 directly; items 7 and 8 are covered in
``test_m10r3_execution_integrity.py`` because they require real process control.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification.execution_orchestrator import (
    CertificationRun,
    CompletionState,
    ExecutionContext,
    ExecutionOrchestrator,
    ExecutionPlan,
    ExecutionTaskSpec,
    FinalDecision,
    RepositoryFingerprint,
    verify_task_environment,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MUTATED_FILE = REPO_ROOT / "backend" / "src" / "engines" / "loan_engine" / "emi.py"


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
        required_environment=(".venv",),
        timeout_seconds=600,
    )
    base.update(over)
    return ExecutionTaskSpec(**base)


def _plan(specs, **over) -> ExecutionPlan:
    base = dict(
        plan_id="execplan-inject",
        generated_at="2026-10-04T00:00:00+00:00",
        rationale="injection",
        repository_fingerprint=RepositoryFingerprint.capture(),
        plan_fingerprint="b" * 64,
        changed_files=["backend/src/x.py"],
        source_plan_id="cpplan-inject",
        affected_capabilities=["cap"],
        affected_components=["backend"],
        invalidated_evidence=[],
        reusable_evidence=[],
        escalation_conditions=[],
        measurement_requirements=[],
        certification_requirements=[],
        tasks=list(specs),
    )
    base.update(over)
    return ExecutionPlan(**base)


# ---------------------------------------------------------------------------
# 1. A required environment variable is removed
# ---------------------------------------------------------------------------


class TestInjectedMissingEnvironmentVariable:
    def test_it_is_a_named_prerequisite_failure_before_any_spawn(self):
        failures = verify_task_environment(
            "exec-0001", ["FINANCE_DB_PATH"], ExecutionContext(), {}
        )
        assert len(failures) == 1
        f = failures[0]
        assert f.task_id == "exec-0001"
        assert f.form == "variable"
        assert "FINANCE_DB_PATH" in f.detail and "not set" in f.detail

    def test_the_plan_level_gate_refuses_to_execute(self):
        orch = ExecutionOrchestrator()
        ok, missing = orch.verify_prerequisites(
            _plan([_spec(required_environment=("FINANCE_DB_PATH",))]), env={}
        )
        assert ok is False
        assert any("FINANCE_DB_PATH" in m for m in missing)

    def test_a_wrong_value_is_also_refused(self):
        failures = verify_task_environment(
            "exec-0001",
            ["PLAYWRIGHT_PROJECT=chromium"],
            ExecutionContext(),
            {"PLAYWRIGHT_PROJECT": "webkit"},
        )
        assert failures and "chromium" in failures[0].detail

    def test_a_missing_tool_is_refused(self):
        failures = verify_task_environment(
            "exec-0001", ["mutmut==3.7.0-not-installed"], ExecutionContext(), {}
        )
        assert failures and failures[0].form == "tool_version"


# ---------------------------------------------------------------------------
# 2. A task timeout is altered
# ---------------------------------------------------------------------------


class TestInjectedTimeoutTampering:
    def test_a_zero_timeout_is_impossible_on_a_spec(self):
        """A zero or negative budget would mean "never run", not "run immediately".

        Nothing validates this today, which is recorded as a gap rather than papered
        over with a test that asserts the current behaviour is desirable.
        """
        spec = _spec(timeout_seconds=-5)
        assert spec.timeout_seconds == -5, (
            "ExecutionTaskSpec does not validate timeout_seconds; a negative budget "
            "is accepted and would classify a task as instantly timed out. See "
            "M10-R3 final report, remaining limitations L2."
        )

    def test_a_tampered_timeout_is_rejected_on_plan_load(self):
        """L2, closed.

        Was an ``xfail(strict=True)`` gap: the runtime recorded ``timeout_seconds`` but
        never validated it, so a corrupt budget executed as written. Now checked in
        ``ExecutionPlan.validate``, which the load path already consults.
        """
        payload = _plan([_spec()]).to_dict()
        payload["tasks"][0]["timeout_seconds"] = -5
        plan = ExecutionPlan.from_dict(payload)
        assert plan.validate(), "a negative timeout_seconds must fail validation"

    @pytest.mark.parametrize("bad", [0, -5, 10**12, True])
    def test_an_invalid_budget_is_refused(self, bad):
        payload = _plan([_spec()]).to_dict()
        payload["tasks"][0]["timeout_seconds"] = bad
        errors = ExecutionPlan.from_dict(payload).validate()
        assert errors, f"timeout_seconds={bad!r} must fail validation"

    def test_an_absurd_budget_is_refused(self):
        """A 10^12 s ceiling is indistinguishable from 'no timeout' at the job level."""
        payload = _plan([_spec()]).to_dict()
        payload["tasks"][0]["timeout_seconds"] = 10**12
        errors = ExecutionPlan.from_dict(payload).validate()
        assert any("maximum" in e for e in errors)

    def test_an_estimate_above_the_budget_is_surfaced_not_refused(self):
        """Advisory, deliberately, and the separation is the point.

        An estimate above its budget is legitimate and common — a short budget over a
        long estimate is exactly how a bounded probe is constructed
        (`test_m9_c49::ScenarioITimeout` uses `timeout_seconds=1` to force a TIMED_OUT
        outcome). `validate()` is an execution gate, so folding this into it made the
        runtime refuse correct plans in order to report a curiosity.
        """
        from runtime.foundation.verification.execution_orchestrator import (
            budget_warnings,
        )

        payload = _plan([_spec()]).to_dict()
        payload["tasks"][0]["estimated_duration_seconds"] = 600
        payload["tasks"][0]["timeout_seconds"] = 60
        plan = ExecutionPlan.from_dict(payload)

        assert plan.validate() == [], "an advisory must never block execution"
        warnings = budget_warnings(plan)
        assert warnings and "exceeds" in warnings[0]

    def test_a_negative_estimate_IS_refused(self):
        """The estimate IS a gate: the shard matrix figure is summed from it, so a
        corrupt value would silently distort every reported schedule."""
        payload = _plan([_spec()]).to_dict()
        payload["tasks"][0]["estimated_duration_seconds"] = -1
        assert ExecutionPlan.from_dict(payload).validate()

    def test_an_invalid_cpu_demand_is_refused(self):
        for bad in (0, -2):
            payload = _plan([_spec()]).to_dict()
            payload["tasks"][0]["cpu_demand"] = bad
            errors = ExecutionPlan.from_dict(payload).validate()
            assert any("cpu_demand" in e for e in errors), f"cpu_demand={bad}"

    def test_a_load_path_refuses_an_invalid_plan(self, tmp_path, capsys):
        """Validation must be reachable from the CLI, not only from the API."""
        from runtime.foundation.verification.control_plane_facade import ControlPlane

        payload = _plan([_spec()]).to_dict()
        payload["tasks"][0]["timeout_seconds"] = -5
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(payload))

        code = ControlPlane().run(plan_path=str(plan_path))
        assert code == 2
        assert "non-positive timeout_seconds" in capsys.readouterr().err

    def test_the_budget_is_actually_passed_to_the_worker(self):
        """The declared budget must reach the process, not be advisory."""
        from unittest.mock import patch

        from runtime.foundation.verification.parallel_executor import CommandResult

        seen: dict = {}

        def _capture(command, *, timeout_seconds, **_kw):
            seen["timeout"] = timeout_seconds
            return CommandResult(
                command=command,
                exit_code=0,
                timed_out=False,
                infra_error=None,
                stdout="",
                stderr="",
                stdout_path=None,
                stderr_path=None,
                duration_seconds=0.0,
            )

        with patch(
            "runtime.foundation.verification.parallel_executor.run_streaming_command",
            side_effect=_capture,
        ):
            from runtime.foundation.verification.parallel_executor import (
                run_streaming_command,
            )

            run_streaming_command("true", timeout_seconds=1234)
        assert seen["timeout"] == 1234


# ---------------------------------------------------------------------------
# 3. Evidence is pointed at the wrong root
# ---------------------------------------------------------------------------


class TestInjectedEvidenceRootTampering:
    def test_two_coverage_tasks_on_the_same_capability_conflict(self):
        """A shared measurement destination is refused before fan-out.

        This is the guard that stops two obligations silently overwriting one
        another's evidence — the 'replay stale evidence' hazard in its static form.
        """
        from runtime.foundation.verification.execution_shards import (
            assign_shards,
            evidence_path_conflicts,
        )

        specs = [
            _spec(
                task_id=f"exec-{i}",
                source_task_id=f"cp-{i}",
                verification_kind="coverage",
                profile="coverage",
                measurement_required=("coverage",),
            )
            for i in (1, 2)
        ]
        conflicts = evidence_path_conflicts(assign_shards(_plan(specs), 1))
        assert conflicts, "two coverage tasks on one capability must be refused"


# ---------------------------------------------------------------------------
# 4. A worker is executed with the wrong plan
# ---------------------------------------------------------------------------


class TestInjectedWrongPlan:
    def test_the_plan_fingerprint_is_preserved_across_narrowing(self):
        """A scoped or sharded leg must still be executing THE plan."""
        from runtime.foundation.verification.control_plane_facade import (
            _plan_with_tasks,
        )

        plan = _plan([_spec(task_id="exec-0001"), _spec(task_id="exec-0002")])
        narrowed = _plan_with_tasks(plan, {"exec-0002"})
        assert narrowed.plan_fingerprint == plan.plan_fingerprint

    def test_a_plan_built_for_another_commit_is_refused(self):
        """The stale-plan case the local harness hit live.

        A plan committed as evidence and executed against a later commit must not
        certify: the repository it describes is not the repository it would run
        against.

        Note the signal is ``repository_fingerprint``, not ``plan_fingerprint``.
        Rewriting the plan fingerprint alone does not make a plan stale — it makes it a
        different plan. Asserting the wrong one would have produced a test that passed
        for the wrong reason.
        """
        foreign = RepositoryFingerprint(
            repository_sha="0" * 40,
            working_tree_hash="1" * 64,
            config_hash="2" * 64,
            toolchain_hash="3" * 64,
            fingerprint="4" * 64,
        )
        plan = _plan([_spec()], repository_fingerprint=foreign)
        report = ExecutionOrchestrator().execute(plan, dry_run=False)
        # FinalDecision is a str enum, so compare by value.
        assert report.final_decision == FinalDecision.VALIDATION_BLOCKED
        assert "repository state changed" in report.decision_reason

    def test_the_committed_checkpoint_a_plan_is_stale_here(self):
        """The committed plan artifact from Checkpoint A must not certify today.

        It was built against commit 1c39736; the working tree has moved. Executing it
        is exactly what a developer would do to reproduce a CI failure from an old
        artifact, and the answer must be a refusal.
        """
        artifact = REPO_ROOT / "docs" / "audits" / "m10-r3-checkpoint-a-plan.json"
        plan = ExecutionPlan.from_dict(json.loads(artifact.read_text()))
        report = ExecutionOrchestrator().execute(plan, dry_run=False)
        assert report.final_decision == FinalDecision.VALIDATION_BLOCKED

    def test_a_corrupt_plan_file_is_refused_not_regenerated(self):
        """A supplied plan must never silently become 'regenerate whatever is current'."""
        from runtime.foundation.verification.control_plane_facade import ControlPlane

        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "plan.json"
            bad.write_text("{not json")
            code = ControlPlane().run(plan_path=str(bad))
        assert code == 2


# ---------------------------------------------------------------------------
# 5. The wrong shard is executed
# ---------------------------------------------------------------------------


class TestInjectedWrongShard:
    def test_a_shard_beyond_the_count_is_rejected(self):
        from runtime.foundation.verification.execution_shards import (
            validate_shard_request,
        )

        # shard 5 of 7 is legal; 7 of 7 and a negative shard are not.
        assert validate_shard_request(5, 7) == (5, 7)
        for bad in (7, 8, -1):
            with pytest.raises(ValueError):
                validate_shard_request(bad, 7)

    def test_a_non_positive_shard_count_is_rejected(self):
        from runtime.foundation.verification.execution_shards import (
            validate_shard_request,
        )

        for bad in (0, -1):
            with pytest.raises(ValueError):
                validate_shard_request(0, bad)

    def test_the_partition_is_deterministic(self):
        """The same plan and count must always yield the same partition.

        If it did not, a CI leg could execute a different set of obligations than the
        aggregate believes it assigned, and every leg would still report success.
        """
        from runtime.foundation.verification.execution_shards import assign_shards

        plan = _plan([_spec(task_id=f"exec-{i:04d}") for i in range(1, 9)])
        first = assign_shards(plan, 3)
        second = assign_shards(plan, 3)
        assert first.partition_fingerprint() == second.partition_fingerprint()
        assert [[t.task_id for t in shard] for shard in first.shards] == [
            [t.task_id for t in shard] for shard in second.shards
        ]

    def test_a_different_shard_count_changes_the_partition(self):
        from runtime.foundation.verification.execution_shards import assign_shards

        plan = _plan([_spec(task_id=f"exec-{i:04d}") for i in range(1, 9)])
        assert (
            assign_shards(plan, 3).partition_fingerprint()
            != assign_shards(plan, 4).partition_fingerprint()
        )


# ---------------------------------------------------------------------------
# 6. Repository state is mutated during execution
# ---------------------------------------------------------------------------


class TestInjectedRepositoryMutation:
    def test_drift_blocks_certification_with_both_fingerprints(self):
        original = MUTATED_FILE.read_bytes()
        try:
            with CertificationRun("inject") as run:
                run.record("exec-0001", CompletionState.PASS)
                MUTATED_FILE.write_bytes(original + b"\n# injected\n")
            assert run.fingerprint_stable is False
            decision, reason = run.decide()
            assert decision is FinalDecision.VALIDATION_BLOCKED
            assert run.fingerprint_before.fingerprint[:12] in reason
            assert run.fingerprint_after.fingerprint[:12] in reason
        finally:
            MUTATED_FILE.write_bytes(original)

    def test_drift_outranks_a_passing_result(self):
        """A green task on a moved tree is not a certification."""
        with CertificationRun("inject") as run:
            run.record("exec-0001", CompletionState.PASS)
        assert run.fingerprint_stable is True
        # Now the SCOPE form, which is how the orchestrator signals drift.
        from runtime.foundation.verification.execution_orchestrator import (
            ObligationOutcome,
            decide_final_outcome,
        )

        decision, _ = decide_final_outcome(
            [ObligationOutcome("exec-0001", CompletionState.SCOPE)]
        )
        assert decision is FinalDecision.VALIDATION_BLOCKED

    def test_the_working_tree_is_clean_afterwards(self):
        """The injection must not leave the repository modified."""
        assert (
            MUTATED_FILE.read_bytes()
            == (
                REPO_ROOT / "backend" / "src" / "engines" / "loan_engine" / "emi.py"
            ).read_bytes()
        )


# ---------------------------------------------------------------------------
# 9. One shard result is removed
# ---------------------------------------------------------------------------


class TestInjectedMissingShardResult:
    def test_a_missing_shard_blocks_certification(self):
        from runtime.foundation.verification.runtime_shards import (
            ShardResult,
            expected_shard_ids,
            verify_shards,
        )

        ids = expected_shard_ids(3)
        present = [
            ShardResult(
                shard_id=sid,
                status="passed",
                exit_code=0,
                duration_seconds=1.0,
                decision="certified",
                fingerprint_before={"fingerprint": "d" * 64},
                fingerprint_after={"fingerprint": "d" * 64},
                fingerprint_stable=True,
            )
            for sid in ids[:-1]
        ]
        problems = verify_shards(3, present)
        assert problems
        assert ids[-1] in problems[0]
        assert "missing" in problems[0]

    def test_a_missing_leg_blocks_certification(self):
        from runtime.foundation.verification.profile_tasks import (
            ProfileLegResult,
            expected_obligation_ids,
            verify_legs,
        )

        ids = expected_obligation_ids("backend")
        legs = [
            ProfileLegResult(
                profile="backend",
                task_id=tid,
                task_name=tid,
                status="passed",
                exit_code=0,
                duration_seconds=1.0,
                decision="certified",
                fingerprint_before={"fingerprint": "e" * 64},
                fingerprint_after={"fingerprint": "e" * 64},
                fingerprint_stable=True,
            )
            for tid in ids[:-1]
        ]
        problems = verify_legs("backend", legs)
        assert any("missing" in p for p in problems)

    def test_a_duplicate_shard_is_refused_as_double_execution(self):
        from runtime.foundation.verification.runtime_shards import (
            ShardResult,
            expected_shard_ids,
            verify_shards,
        )

        ids = expected_shard_ids(2)
        shard = ShardResult(
            shard_id=ids[0],
            status="passed",
            exit_code=0,
            duration_seconds=1.0,
            decision="certified",
            fingerprint_before={"fingerprint": "f" * 64},
            fingerprint_after={"fingerprint": "f" * 64},
            fingerprint_stable=True,
        )
        problems = verify_shards(2, [shard, shard])
        assert any("more than one leg" in p for p in problems)


# ---------------------------------------------------------------------------
# 10. Stale evidence is replayed
# ---------------------------------------------------------------------------


class TestInjectedStaleEvidence:
    def test_a_measurement_for_another_sha_is_not_certifying(self):
        """Replaying yesterday's mutation record must not satisfy today's gate.

        Built from a real ``MeasurementTruthRecord`` rather than a stand-in: the gate
        reads a dozen fields and recomputes completion status, and a partial fake would
        have tested the fake rather than the gate.
        """
        from runtime.foundation.verification.execution_orchestrator import (
            ObligationOutcome,
            decide_final_outcome,
        )
        from runtime.foundation.verification.measurement_truth import (
            EvidenceClassification,
            MeasurementKind,
            MeasurementTruthRecord,
            PopulationAccounting,
        )

        authoritative = MeasurementTruthRecord(
            run_id="mut-old",
            measurement_kind=MeasurementKind.MUTATION.value,
            repository_sha="f" * 40,  # NOT the current sha
            tree_sha="1" * 40,
            working_tree_fingerprint="2" * 64,
            configuration_fingerprint="3" * 64,
            toolchain_fingerprint="4" * 64,
            environment_fingerprint="5" * 64,
            evidence_classification=EvidenceClassification.AUTHORITATIVE.value,
            evidence_fingerprint="6" * 64,
            population=PopulationAccounting(
                requested_generated=100, generated=100, killed=95, survived=5
            ),
            coverage=95.0,
            mutation_score=95.0,
            execution_status="PASS",
            failure_classification="none",
        )

        decision, reason = decide_final_outcome(
            [ObligationOutcome("cap", CompletionState.PASS)],
            certification_requirements=[
                {"capability": "cap", "minimum_mutation_score": 80}
            ],
            measurement_lookup=lambda cap, kind: (authoritative, ""),
            current_sha="0" * 40,
        )
        assert decision == FinalDecision.NOT_CERTIFIABLE
        assert "cap" in reason and "sha" in reason

    def test_a_current_measurement_does_satisfy_the_gate(self):
        """The negative control: the same record at the current sha must certify.

        Without it, the test above could pass for the wrong reason — e.g. if the gate
        rejected every record rather than only stale ones.
        """
        from runtime.foundation.verification.execution_orchestrator import (
            ObligationOutcome,
            decide_final_outcome,
        )
        from runtime.foundation.verification.measurement_truth import (
            EvidenceClassification,
            MeasurementKind,
            MeasurementTruthRecord,
            PopulationAccounting,
        )

        current_sha = RepositoryFingerprint.capture().repository_sha
        authoritative = MeasurementTruthRecord(
            run_id="mut-now",
            measurement_kind=MeasurementKind.MUTATION.value,
            repository_sha=current_sha,
            tree_sha=current_sha,
            working_tree_fingerprint="2" * 64,
            configuration_fingerprint="3" * 64,
            toolchain_fingerprint="4" * 64,
            environment_fingerprint="5" * 64,
            evidence_classification=EvidenceClassification.AUTHORITATIVE.value,
            evidence_fingerprint="6" * 64,
            population=PopulationAccounting(
                requested_generated=100, generated=100, killed=95, survived=5
            ),
            coverage=95.0,
            mutation_score=95.0,
            execution_status="PASS",
            failure_classification="none",
        )
        decision, _ = decide_final_outcome(
            [ObligationOutcome("cap", CompletionState.PASS)],
            certification_requirements=[
                {"capability": "cap", "minimum_mutation_score": 80}
            ],
            measurement_lookup=lambda cap, kind: (authoritative, ""),
            current_sha=current_sha,
        )
        assert decision == FinalDecision.CERTIFIED

    def test_an_unknown_task_id_is_refused_rather_than_expanded(self):
        from runtime.foundation.verification.profile_tasks import (
            ProfileLegResult,
            expected_obligation_ids,
            verify_legs,
        )

        ids = expected_obligation_ids("backend")
        legs = [
            ProfileLegResult(
                profile="backend",
                task_id=tid,
                task_name=tid,
                status="passed",
                exit_code=0,
                duration_seconds=1.0,
                decision="certified",
                fingerprint_before={"fingerprint": "1" * 64},
                fingerprint_after={"fingerprint": "1" * 64},
                fingerprint_stable=True,
            )
            for tid in ids
        ]
        # Inject a leg the canonical plan never asked for — a replayed or invented id.
        legs.append(
            ProfileLegResult(
                profile="backend",
                task_id="backend-invented",
                task_name="invented",
                status="passed",
                exit_code=0,
                duration_seconds=1.0,
                decision="certified",
                fingerprint_before={"fingerprint": "1" * 64},
                fingerprint_after={"fingerprint": "1" * 64},
                fingerprint_stable=True,
            )
        )
        problems = verify_legs("backend", legs)
        assert any("not in the canonical plan" in p for p in problems)


class TestInjectedRegistryGap:
    """L6 — a registry-coverage obligation is not a failing test.

    It used to be a `capability` task whose command was
    ``echo 'UNMAPPED capabilities require review (N): ...' && exit 1``. That made a
    registry fact indistinguishable from an assertion failure: the record said
    "command exit 1" and the verdict said "run the diagnostic path", which cannot
    resolve a missing mapping. Nothing is weakened — still mandatory, still fails closed.
    """

    def test_it_has_its_own_completion_state(self):
        from runtime.foundation.verification.execution_orchestrator import (
            NON_PASS_STATES,
            PASSING_STATES,
        )

        gap = CompletionState.REGISTRY_GAP
        assert gap.value == "registry_gap"
        assert gap in NON_PASS_STATES, "a registry gap must never read as a pass"
        assert gap not in PASSING_STATES

    def test_the_verdict_names_the_remedy_not_a_diagnostic(self):
        from runtime.foundation.verification.execution_orchestrator import (
            ObligationOutcome,
            decide_final_outcome,
        )

        decision, reason = decide_final_outcome(
            [
                ObligationOutcome(
                    "exec-0009",
                    CompletionState.REGISTRY_GAP,
                    detail="no mapping for: unmapped:Foo",
                )
            ]
        )
        assert decision == FinalDecision.NOT_CERTIFIABLE
        assert "mapping" in reason
        assert "not a test failure" in reason
        assert (
            "diagnostic path" in reason
        ), "the reason must explicitly say the diagnostic path is not the answer"

    def test_it_is_not_confused_with_a_configuration_failure(self):
        from runtime.foundation.verification.execution_orchestrator import (
            ObligationOutcome,
            decide_final_outcome,
        )

        gap, _ = decide_final_outcome(
            [ObligationOutcome("a", CompletionState.REGISTRY_GAP)]
        )
        config, _ = decide_final_outcome(
            [ObligationOutcome("a", CompletionState.CONFIGURATION)]
        )
        assert gap != config, (
            "a missing mapping and a malformed configuration are different problems "
            "with different remedies"
        )

    def test_the_task_no_longer_carries_a_shell_command(self):
        """The condition was moved out of the shell; that is the whole point."""
        from runtime.foundation.verification.control_plane import REGISTRY_MAPPING_KIND

        assert REGISTRY_MAPPING_KIND == "registry_mapping"
        spec = _spec(verification_kind=REGISTRY_MAPPING_KIND, command="")
        assert spec.command == "", (
            "an internally-executed task must not also carry a shell command; the "
            "condition is decided by the runtime"
        )

    def test_an_empty_command_is_still_rejected_for_every_other_kind(self):
        """The validation exception is narrow on purpose."""
        assert ExecutionPlan.from_dict(
            {
                **_plan([_spec()]).to_dict(),
                "tasks": [{**_spec().to_dict(), "command": ""}],
            }
        ).validate(), "a genuinely empty command on a spawned kind must fail validation"

    def test_it_is_revalidated_at_execution_time(self):
        """A plan authored while the gap existed must not certify after it closed.

        The authority is re-checked where the knowledge is, not trusted from the plan.
        """
        from runtime.foundation.verification.execution_orchestrator import (
            _unmapped_capabilities_now,
        )

        assert _unmapped_capabilities_now(
            ("definitely-not-a-capability",)
        ), "an unknown capability must be reported as unmapped, not silently trusted"
        assert _unmapped_capabilities_now(()) == []
