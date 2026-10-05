# runtime/tests/test_m11_r4_reconcile_aggregate.py
#
# M11-R4 — the reconcile aggregate must be able to read a shard's evidence.
#
# WHAT FAILED IN CI
# -----------------
# Every `Verification Reconcile` run crashed in its aggregate job:
#
#     File ".../control_plane_facade.py", line 1436, in _aggregate_shard_reports
#       records.append(TaskExecutionRecord(**record))
#     TypeError: TaskExecutionRecord.__init__() missing 20 required positional
#                arguments: 'record_id', 'plan_id', 'primary_capability', ...
#
# Identical text in run 37257612911 (03:24) and run 37270708886 (06:29), so it
# predates this phase and is not an M11 regression. It was invisible for as long
# as the shards were independently red: the gate was already failing, so nobody
# was reading its traceback. Once STEP 4/STEP 5 turned all seven shards green,
# the crash became the only thing left.
#
# ROOT CAUSE
# ----------
# Two halves of one contract disagreed. The shard producer emitted three keys per
# record:
#
#     {"task_id": ..., "completion_state": ..., "reason": ...}
#
# while the aggregator rebuilds records as `TaskExecutionRecord(**record)` against
# the full 23-field dataclass. Producer wins: a shard now writes `r.to_dict()`.
#
# These tests pin both halves — that a shard's document is complete, and that an
# incomplete one is reported as a producer fault instead of taking the whole gate
# verdict down with it.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification.execution_orchestrator import (
    CompletionState,
    TaskExecutionRecord,
)


def _record(task_id: str = "exec-0001") -> TaskExecutionRecord:
    return TaskExecutionRecord(
        record_id=f"rec-{task_id}",
        plan_id="plan-1",
        task_id=task_id,
        primary_capability="account-engine",
        capabilities=["account-engine", "ledger"],
        command="pytest backend/tests -q",
        scope="unit",
        is_mandatory=True,
        is_escalation=False,
        verification_kind="unit",
        started_at="2026-10-05T05:00:00Z",
        completed_at="2026-10-05T05:00:12Z",
        duration_seconds=12.5,
        exit_code=0,
        completion_state=CompletionState.PASS.value,
        stdout_path="runtime/generated/logs/exec-0001.stdout.log",
        stderr_path="runtime/generated/logs/exec-0001.stderr.log",
        artifacts=[],
        measurement_truth=None,
        diagnostic={"termination": "EXIT_ZERO"},
        next_action="",
        reason="",
        prerequisites_satisfied=True,
    )


class TestShardDocumentIsComplete:
    """The producer half, exercised through the real canonical path.

    Written against `runtime.verify run --task … --result-out …` rather than
    against `_write_leg_result`, because the defect was never in that helper — it
    was in what the caller handed it.
    """

    def test_real_shard_run_emits_a_reconstructable_record(self, tmp_path):
        from runtime.foundation.verification.control_plane_facade import ControlPlane
        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionPlan,
            ExecutionTaskSpec,
            RepositoryFingerprint,
        )

        fingerprint = RepositoryFingerprint.capture()
        task = ExecutionTaskSpec(
            task_id="t-1",
            primary_capability="account-engine",
            capabilities=["account-engine", "ledger"],
            verification_kind="unit",
            command=f'{__import__("sys").executable} -c "print(1)"',
            profile="unit",
            scope="unit",
            is_mandatory=True,
            is_escalation=False,
            reason="probe",
            source_task_id="cp-t-1",
            origin="control_plane",
        )
        plan = ExecutionPlan(
            plan_id="probe-plan",
            source_plan_id="cp",
            repository_fingerprint=fingerprint,
            changed_files=[],
            affected_capabilities=[],
            affected_components=[],
            invalidated_evidence=[],
            reusable_evidence=[],
            tasks=[task],
            escalation_conditions=[],
            measurement_requirements=[],
            certification_requirements=[],
            rationale="probe",
            plan_fingerprint=fingerprint.fingerprint,
            generated_at="2026-10-05T00:00:00Z",
        )
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(plan.to_dict(), default=str), encoding="utf-8")
        out = tmp_path / "shard-0.json"

        ControlPlane().run(
            plan_path=str(plan_file),
            task_scope=["t-1"],
            result_out=str(out),
        )

        payload = json.loads(out.read_text(encoding="utf-8"))
        assert len(payload["records"]) == 1
        written = payload["records"][0]

        # Every field `TaskExecutionRecord(**record)` demands must be present. This
        # is the exact call `_aggregate_shard_reports` makes, and it is the call that
        # raised `missing 20 required positional arguments`.
        record = dict(written)
        record["completion_state"] = CompletionState(record["completion_state"])
        assert TaskExecutionRecord(**record).task_id == "t-1"

        # And the evidence, not a summary: this is what the aggregate lost before.
        assert written["duration_seconds"] >= 0
        assert written["exit_code"] == 0
        assert written["command"]
        assert written["diagnostic"] is not None
        # Capability names, not a count label.
        assert written["capabilities"] == ["account-engine", "ledger"]


class TestAggregatorSurvivesAMalformedRecord:
    """The aggregator's own contract already says an unusable document is
    *reported*, never coerced into a verdict. A truncated record used to raise
    straight through and cost the operator the entire gate verdict."""

    @staticmethod
    def _write_shard(directory: Path, records) -> Path:
        # The aggregator only needs a plan it can load and a task list to check
        # coverage against; a hand-written document keeps this test focused on the
        # record contract rather than on ExecutionPlan's constructor.
        (directory / "plan.json").write_text(
            json.dumps(
                {
                    "plan_id": "plan-1",
                    "plan_fingerprint": "f" * 64,
                    "tasks": [],
                }
            ),
            encoding="utf-8",
        )
        out = directory / "shard-0.json"
        out.write_text(
            json.dumps(
                {
                    "plan_id": "plan-1",
                    "report_id": "shard-0",
                    "records": records,
                    "final_decision": "certified",
                    "decision_reason": "",
                }
            ),
            encoding="utf-8",
        )
        return directory

    def test_truncated_record_does_not_abort_the_gate(self, tmp_path, capsys):
        """The regression: `TaskExecutionRecord(**record)` raised TypeError."""
        from runtime.foundation.verification.control_plane_facade import ControlPlane

        directory = self._write_shard(
            tmp_path,
            # Exactly what CI shipped: three keys.
            [{"task_id": "exec-0004", "completion_state": "failed", "reason": "x"}],
        )

        exit_code = ControlPlane()._aggregate_shard_reports(str(directory))

        err = capsys.readouterr().err
        assert "MALFORMED" in err
        assert "shard-0.json#0" in err
        # Refused to certify, which is the fail-closed outcome. Not a traceback.
        assert exit_code != 0

    def test_full_record_is_accepted(self, tmp_path, capsys):
        from runtime.foundation.verification.control_plane_facade import ControlPlane

        directory = self._write_shard(tmp_path, [_record().to_dict()])
        ControlPlane()._aggregate_shard_reports(str(directory))
        assert "MALFORMED" not in capsys.readouterr().err

    @pytest.mark.parametrize(
        "record",
        [
            {"task_id": "exec-0004", "completion_state": "failed", "reason": "x"},
            {"task_id": "exec-0004"},
            {},
        ],
    )
    def test_no_truncated_shape_raises(self, tmp_path, record):
        """Whatever a producer emits, the aggregator decides rather than crashing."""
        from runtime.foundation.verification.control_plane_facade import ControlPlane

        directory = self._write_shard(tmp_path, [record])
        assert ControlPlane()._aggregate_shard_reports(str(directory)) != 0
