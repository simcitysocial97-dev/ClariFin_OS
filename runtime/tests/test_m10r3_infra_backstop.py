"""M10-R3 / L1c — the infrastructure backstop is the runtime's, and it is validated.

The reconcile workflow wrapped each shard leg in a literal GNU `timeout 85m`, repeated in
three places. The literal was not merely redundant — it was **smaller than an obligation's
own declared budget**. Reconcile shard 3 holds a single task with
``timeout_seconds=5400`` (90 minutes), so an 85-minute wrapper would have killed it five
minutes before its contractual expiry: the runner reporting a timeout for work that was
still legitimately running.

That is the failure class this milestone exists to end, so the state is now rejected
mechanically rather than documented against.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification.execution_orchestrator import (
    ExecutionPlan,
    ExecutionTaskSpec,
    RepositoryFingerprint,
)
from runtime.foundation.verification.execution_shards import (
    INFRA_BACKSTOP_MARGIN_SECONDS,
    assign_shards,
    plan_matrix,
    required_backstop_minutes,
    shard_intended_termination_seconds,
    validate_infra_backstop,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

#: A GNU `timeout` whose budget is a literal, in either shell spelling:
#: `${VAR:-85}` and `${VAR:-85}m`. Written as a normal string because a raw
#: triple-quoted one collides with the `["']?` character class.
PATTERN_HARDCODED_TIMEOUT = (
    "timeout\\s+[\"']?\\$\\{[A-Z0-9_]+:-(\\d+)\\}?"
)


def _spec(task_id: str, *, timeout: int = 600, command: str = "true") -> ExecutionTaskSpec:
    return ExecutionTaskSpec(
        task_id=task_id,
        source_task_id=f"cp-{task_id}",
        primary_capability="cap",
        capabilities=("cap",),
        verification_kind="unit",
        command=command,
        profile="backend",
        scope="repo",
        is_mandatory=True,
        is_escalation=False,
        reason="r",
        origin="control_plane",
        timeout_seconds=timeout,
        estimated_duration_seconds=timeout,
    )


def _plan(*specs: ExecutionTaskSpec) -> ExecutionPlan:
    return ExecutionPlan(
        plan_id="execplan-backstop",
        generated_at="2026-10-04T00:00:00+00:00",
        rationale="test",
        repository_fingerprint=RepositoryFingerprint.capture(),
        plan_fingerprint="c" * 64,
        changed_files=["backend/src/x.py"],
        source_plan_id="cpplan-backstop",
        affected_capabilities=["cap"],
        affected_components=["backend"],
        invalidated_evidence=[],
        reusable_evidence=[],
        escalation_conditions=[],
        measurement_requirements=[],
        certification_requirements=[],
        tasks=list(specs),
    )


class TestContractualWallClock:
    def test_a_single_task_is_its_own_contract(self):
        assert shard_intended_termination_seconds([_spec("a", timeout=5400)]) == 5400

    def test_heavy_tasks_serialise_so_budgets_add(self):
        """Two 4-CPU tasks cannot overlap on a 4-core budget, so their budgets add.

        Using the max would size a backstop that expires mid-shard — the precise defect
        this mechanism exists to prevent.
        """
        tasks = [
            _spec("heavy-a", timeout=3600, command="pytest -n auto"),
            _spec("heavy-b", timeout=3600, command="pytest -n auto"),
        ]
        assert shard_intended_termination_seconds(tasks, cpu_budget=4) == 7200

    def test_light_tasks_share_a_wave(self):
        tasks = [_spec("a", timeout=600), _spec("b", timeout=600), _spec("c", timeout=600)]
        assert shard_intended_termination_seconds(tasks, cpu_budget=4) == 600

    def test_derived_from_budgets_not_estimates(self):
        """The budget is the obligation; the estimate is advisory.

        A backstop sized from estimates would be a guess. Sized from budgets it is a
        contract, which is what an infrastructure timeout must be.
        """
        task = _spec("a", timeout=900)
        object.__setattr__(task, "estimated_duration_seconds", 1)
        assert shard_intended_termination_seconds([task]) == 900


class TestBackstopValidation:
    def test_a_backstop_shorter_than_the_contract_is_rejected(self):
        tasks = [_spec("a", timeout=5400)]
        problem = validate_infra_backstop(tasks, 5100)  # 85m against a 90m obligation
        assert problem is not None
        assert "5100" in problem and "5400" in problem

    def test_the_rejection_says_how_much_to_use(self):
        tasks = [_spec("a", timeout=5400)]
        problem = validate_infra_backstop(tasks, 5100)
        assert str(required_backstop_minutes(tasks)) in problem

    def test_an_adequate_backstop_is_accepted(self):
        tasks = [_spec("a", timeout=5400)]
        assert validate_infra_backstop(tasks, 5700) is None

    def test_the_margin_is_teardown_not_slack_for_a_slow_task(self):
        """A task exceeding its own budget is a defect and must be reported as one.

        Sizing the backstop from budgets plus a small teardown margin keeps that true: a
        slow task surfaces as a task timeout rather than being absorbed by a larger job
        timeout that makes it invisible.
        """
        tasks = [_spec("a", timeout=600)]
        assert required_backstop_minutes(tasks) == max(
            1, -(-(600 + INFRA_BACKSTOP_MARGIN_SECONDS) // 60)
        )


class TestMatrixPublishesTheBackstop:
    def test_every_shard_carries_its_required_backstop(self):
        plan = _plan(*[_spec(f"exec-{i:04d}", timeout=600 + i) for i in range(1, 8)])
        document = json.loads(plan_matrix(assign_shards(plan, 3), plan))
        assert document["include"]
        for entry in document["include"]:
            assert entry["required_timeout_minutes"] >= 1
            assert entry["contractual_seconds"] > 0

    def test_a_shard_holding_a_long_task_gets_a_long_backstop(self):
        plan = _plan(_spec("short", timeout=600), _spec("long", timeout=5400))
        document = json.loads(plan_matrix(assign_shards(plan, 2), plan))
        by_task = {t: e for e in document["include"] for t in (e.get("task_ids") or [])}
        long_entry = by_task["long"]
        short_entry = by_task["short"]
        assert long_entry["required_timeout_minutes"] > short_entry["required_timeout_minutes"]


class TestWorkflowsNoLongerHardCodeIt:
    def _workflow(self, name: str) -> str:
        return (REPO_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")

    @pytest.mark.parametrize(
        "name",
        ["verification-reconcile.yml", "verification-runtime.yml", "backend-verify.yml"],
    )
    def test_no_per_leg_timeout_default_survives(self, name):
        """Rule 14's regression, asserted on the real files.

        A `${VAR:-N}` default in a GNU `timeout` is a literal budget in disguise. The
        value must come from the runtime's published `required_timeout_minutes`.
        """
        import re

        offenders = re.findall(
            PATTERN_HARDCODED_TIMEOUT, self._workflow(name)
        )
        assert not offenders, f"{name} still hard-codes a per-leg timeout: {offenders}"

    @pytest.mark.parametrize(
        "name",
        ["verification-reconcile.yml", "verification-runtime.yml", "backend-verify.yml"],
    )
    def test_the_backstop_is_exported_so_the_runtime_can_validate_it(self, name):
        raw = self._workflow(name)
        assert "VERIFY_INFRA_BACKSTOP_SECONDS" in raw, (
            f"{name} must hand the runtime the backstop it is actually running under, "
            f"or the runtime cannot reject one that expires too early"
        )