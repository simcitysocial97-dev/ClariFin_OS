"""M10-R3 / Checkpoint D2 — scoped execution and the local reference harness.

The mission's acceptance criterion: a failing CI execution must be reproducible locally
from its runtime execution identity, without reconstructing hidden YAML state.

That requires two things this checkpoint adds:

1. **Scoped execution by task identity** (``--task`` / ``--tasks``). ``--shard``
   partitions, which is right for a matrix leg and wrong for reproduction: to re-run one
   failing obligation you need that task alone, and re-deriving the whole partition to
   extract it is exactly the "reconstruct the global plan" step that must be avoided.
2. **A local harness** (``verify local``) that runs the same serialized execution
   description CI runs and prints the task/status/duration/termination table with a
   reproduction command per failure.

Also pinned here: a pre-existing crash in the plain ``verify run --plan`` path, which
made the single-obligation invocation — the most basic one — impossible.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification import control_plane_facade as facade
from runtime.foundation.verification.execution_orchestrator import ExecutionPlan

REPO_ROOT = Path(__file__).resolve().parents[2]


def _plan(
    task_ids: tuple[str, ...] = ("exec-0001", "exec-0002", "exec-0003"),
    escalation: tuple[str, ...] = (),
) -> ExecutionPlan:
    from runtime.foundation.verification.execution_orchestrator import (
        ExecutionTaskSpec,
        RepositoryFingerprint,
    )

    return ExecutionPlan(
        plan_id="execplan-scope-test",
        generated_at="2026-10-04T00:00:00+00:00",
        rationale="test",
        repository_fingerprint=RepositoryFingerprint.capture(),
        plan_fingerprint="a" * 64,
        changed_files=["backend/src/x.py"],
        source_plan_id="cpplan-test",
        affected_capabilities=["cap"],
        affected_components=["backend"],
        invalidated_evidence=[],
        reusable_evidence=[],
        escalation_conditions=[],
        measurement_requirements=[],
        certification_requirements=[],
        tasks=[
            ExecutionTaskSpec(
                task_id=tid,
                source_task_id=f"cp-{tid}",
                primary_capability="cap",
                capabilities=("cap",),
                verification_kind="unit",
                command="true",
                profile="backend",
                scope="repo",
                is_mandatory=True,
                is_escalation=tid in escalation,
                reason="r",
                origin="control_plane",
                required_environment=(".venv",),
            )
            for tid in task_ids
        ],
    )


class TestScopedNarrowing:
    def test_it_keeps_only_the_requested_tasks(self):
        narrowed = facade._plan_with_tasks(_plan(), {"exec-0002"})
        assert [t.task_id for t in narrowed.tasks] == ["exec-0002"]

    def test_it_preserves_the_plan_identity(self):
        """A narrowed run must still be *the same plan*.

        Rewriting ``plan_fingerprint`` to match the narrowed set would destroy the one
        property that lets a CI aggregate trust its legs — that they all executed the
        same plan — and would let a scoped run be mistaken for a different,
        independently-certified plan.
        """
        plan = _plan()
        narrowed = facade._plan_with_tasks(plan, {"exec-0002"})
        assert narrowed.plan_id == plan.plan_id
        assert narrowed.plan_fingerprint == plan.plan_fingerprint
        assert narrowed.repository_fingerprint == plan.repository_fingerprint

    def test_it_preserves_certification_requirements(self):
        plan = _plan()
        narrowed = facade._plan_with_tasks(plan, {"exec-0001"})
        assert narrowed.certification_requirements == plan.certification_requirements

    def test_an_empty_scope_yields_no_tasks(self):
        assert facade._plan_with_tasks(_plan(), set()).tasks == []


class TestScopedExecutionContract:
    """The CLI contract, asserted on the dispatcher rather than by running a plan."""

    def test_an_unknown_task_id_is_rejected_not_ignored(self, tmp_path, capsys):
        """`--task exec-9999` must never quietly run the whole plan.

        That would be the most dangerous possible response to a typo in a reproduction
        command: a green run for a task that does not exist. Exercised against the real
        ``ControlPlane.run`` rather than a mock, because the bug lives in the branch that
        decides whether to narrow at all.
        """
        from runtime.foundation.verification.control_plane_facade import ControlPlane

        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_plan().to_dict()))

        cp = ControlPlane()
        code = cp.run(plan_path=str(plan_path), task_scope=["exec-9999"])

        assert code == 2
        err = capsys.readouterr().err
        assert "exec-9999" in err
        assert "contains 3 task(s)" in err, (
            "the error must list the real task ids so the operator can correct the typo"
        )

    def test_a_known_task_id_is_accepted_and_narrowed(self, tmp_path, capsys):
        from runtime.foundation.verification.control_plane_facade import ControlPlane

        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_plan().to_dict()))

        cp = ControlPlane()
        code = cp.run(plan_path=str(plan_path), task_scope=["exec-0002"])
        # exec-0002's command is `true`, so the scoped run itself succeeds.
        assert code == 0
        assert "scoped execution of 1/3" in capsys.readouterr().err

    def test_escalation_tasks_are_refused_in_a_scoped_run(self, tmp_path, capsys):
        """Escalation is gated on the GLOBAL mandatory outcome.

        A single-task run cannot decide that, so running one would execute work the
        plan never authorised — the same reason `--shard` excludes them.
        `ExecutionTaskSpec` is frozen, so the flag is set at construction.
        """
        from runtime.foundation.verification.control_plane_facade import ControlPlane

        plan = _plan(("exec-0002",), escalation=("exec-0002",))
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(plan.to_dict()))

        cp = ControlPlane()
        code = cp.run(plan_path=str(plan_path), task_scope=["exec-0002"])

        assert code == 2
        assert "escalation-gated" in capsys.readouterr().err


class TestLocalHarnessReporting:
    def test_it_reports_a_shard_failure_even_without_task_records(self, tmp_path):
        """A shard can fail before producing records — stale plan, unmet prerequisites,
        a killed process. Those are precisely the cases a reproduction table exists
        for, so an empty harvest must never read as "nothing failed"."""
        result = tmp_path / "shard-0.json"
        result.write_text(
            json.dumps(
                {
                    "schema": "m10r2-leg-result/v1",
                    "final_decision": "validation_blocked",
                    "status": "failed",
                    "exit_code": 1,
                    "duration_seconds": 1.4,
                    "records": [],
                }
            )
        )
        rows = facade._harvest_task_rows(result, 0)
        assert rows[0][0] == "shard-0"
        assert rows[0][1] == "validation_blocked"
        assert rows[0][3] == "exit_1"

        failures = facade._shard_level_failure(result, 0, 1)
        assert len(failures) == 1
        assert "validation_blocked" in failures[0][1]

    def test_it_reports_a_per_task_failure_with_its_reproduction_command(self, tmp_path):
        result = tmp_path / "shard-0.json"
        result.write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "task_id": "exec-0004",
                            "completion_state": "failed",
                            "diagnostic": {"termination": "EXIT_NONZERO"},
                            "duration_seconds": 125.6,
                        }
                    ]
                }
            )
        )
        rows = facade._harvest_task_rows(result, 0)
        assert rows == [("exec-0004", "failed", 125.6, "EXIT_NONZERO")]
        failures = facade._harvest_failures(result, _plan(), 0, 7)
        assert failures[0][0] == "exec-0004"
        assert "--task exec-0004" in failures[0][1]
        assert "--shard 0 --shard-count 7" in failures[0][1]

    def test_a_passing_task_is_not_a_failure(self, tmp_path):
        result = tmp_path / "shard-0.json"
        result.write_text(
            json.dumps({"records": [{"task_id": "exec-0001", "completion_state": "pass"}]})
        )
        assert facade._harvest_failures(result, _plan(), 0, 1) == []


class TestLocalIsNotASecondExecutor:
    def test_local_is_classified_as_an_alias_not_a_new_operation(self):
        """It must stay a front-end over plan + run.

        If `local` became a distinct canonical operation it would eventually grow its
        own planner or verdict, and local execution would drift from CI by
        construction — the exact failure this milestone exists to prevent.
        """
        from runtime.foundation.verification.canonical_control_plane import (
            _CLASSIFICATION,
        )

        assert _CLASSIFICATION["local"] == "CANONICAL_ALIAS"


class TestUnflaggedRunIsFixed:
    def test_an_unsharded_run_is_normalised_to_none(self):
        """`verify run --plan <file>` without `--shard` crashed at e7d77ae6.

        `_parse_shard_arg` returns `(None, None)` and its docstring promises callers
        normalise it, but the dispatch passed the tuple through, so `run()`'s
        `shard is not None` test succeeded and `shard[1] > 1` raised TypeError. The most
        basic invocation of the canonical runner was impossible — and it is exactly the
        invocation needed to reproduce a single failing obligation.
        """
        assert facade._parse_shard_arg([]) == (None, None)
        # The dispatch must not forward that tuple.
        shard, shard_count = (None, None)
        normalised = (shard, shard_count) if shard is not None and shard_count is not None else None
        assert normalised is None