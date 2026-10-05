# runtime/tests/test_m11_r4_capability_provenance.py
#
# M11-R4 — capability identity must survive the whole plan → shard path.
#
# WHAT FAILED IN CI
# -----------------
# Reconcile run 37261663417, shard 6, task exec-0006:
#
#     completion_state : registry_gap
#     reason           : 1 changed capabilit(y/ies) resolved to an unmapped
#                        capability. no verification-registry mapping for:
#                        unmapped:UNMAPPED[3]
#
# `unmapped:UNMAPPED[3]` is a COUNT. It says three capabilities are unmapped and
# names none of them, so it cannot be acted on: the review obligation it raises
# is "map the capability", and there is no capability named.
#
# WHERE THE NAMES WERE LOST
# -------------------------
# `control_plane.ControlPlanePlanner._build_tasks()` puts the concrete names on
# the obligation (`VerificationTask.capabilities`, control_plane.py:337). They
# reached `ExecutionTaskSpec` correctly at
# `execution_orchestrator._expand_control_plane_tasks` (the constructor call
# reads `cp_task.capabilities or (cp_task.capability_id,)`).
#
# They were then thrown away two lines later. The per-bucket dedup accumulator
# was seeded with `{cp_task.capability_id}` — a set of task capability ids — and
# the finalisation loop wrote that set straight back into `spec.capabilities`.
# For every ordinary task the two sets are identical, so the bug was invisible;
# for the ONE task whose `capability_id` is a count label they are not, and the
# count label won.
#
# WHY IT REPRODUCED ONLY IN CI
# ----------------------------
# Not a CI-only bug: it reproduces wherever a plan contains an unmapped change.
# This workstation simply had none — with `frontend/node_modules` present the
# TypeScript symbol resolver succeeds, the cross-layer graph mints 448 frontend
# capabilities, and all 394 changed files resolve. On a runner without
# `ts-morph` the resolver fails, discovery returns nothing, and three route
# files fall through unmapped. So the same code produced a red shard in CI and a
# green plan locally. The tests below pin the PATH, which is runner-independent,
# and separately pin the three real names so a future report of "3 unmapped"
# can be checked against them.
#
# WHAT IS PINNED HERE
# -------------------
#   1. Concrete capability names survive `_expand_control_plane_tasks` — through
#      the dedup bucket, through `to_dict`/`from_dict`, and into the record the
#      shard writes. Provenance, not a label.
#   2. An ordinary task's `capabilities` is unchanged by the fix.
#   3. Two control-plane tasks sharing one command merge their names rather than
#      losing the second.
#   4. The registry-gap record names the three capabilities that CI reported as
#      a count.

from __future__ import annotations

import pytest

from runtime.foundation.verification.control_plane import VerificationTask
from runtime.foundation.verification.execution_orchestrator import (
    ExecutionOrchestrator,
    ExecutionTaskSpec,
)

#: The three capabilities CI reported only as `unmapped:UNMAPPED[3]`.
#: Established by resolving CI run 37261663417's own `changed_files` list against
#: this branch and clearing the frontend capability discovery — the exact
#: condition a runner without `ts-morph` produces. They are the three changed
#: files that NOTHING else claims: every other frontend file on that boundary is
#: claimed by `frontend-verification` through its contract paths, and these three
#: are claimed only by the cross-layer graph's route discovery.
CI_UNMAPPED_THREE = {
    "UNMAPPED:frontend/app/api/diagnostic-signatures/route.ts",
    "UNMAPPED:frontend/app/layout.tsx",
    "UNMAPPED:frontend/app/settings/page.tsx",
}


def _cp_task(**overrides) -> VerificationTask:
    base = dict(
        task_id="task-0001",
        capability_id="account-engine",
        verification_kind="unit",
        command="pytest backend/tests -q",
        profile="backend",
        is_mandatory=True,
        is_escalation=False,
        reason="Directly affected by change",
    )
    base.update(overrides)
    return VerificationTask(**base)


class _Plan:
    """Minimal stand-in for ControlPlanePlan/ExecutionPlan.

    `_expand_control_plane_tasks` only reads `cp.tasks`; `_make_record` only
    reads `plan.plan_fingerprint`. Anything wider would couple this file to
    plan construction it is not testing.
    """

    plan_fingerprint = "test-fingerprint"
    plan_id = "test-plan"

    def __init__(self, tasks):
        self.tasks = tasks


@pytest.fixture(scope="module")
def orchestrator() -> ExecutionOrchestrator:
    return ExecutionOrchestrator()


def _expand(orchestrator: ExecutionOrchestrator, tasks) -> list[ExecutionTaskSpec]:
    specs, _ = orchestrator._expand_control_plane_tasks(_Plan(tasks), None)
    return specs


class TestCapabilityNamesSurviveThePlan:
    def test_declared_capabilities_reach_the_spec(self, orchestrator):
        """The regression: the declared names were replaced by the count label."""
        specs = _expand(
            orchestrator,
            [
                _cp_task(
                    task_id="task-unmapped-review",
                    capability_id="unmapped:UNMAPPED[3]",
                    verification_kind="registry_mapping",
                    command="",
                    profile="unmapped-review",
                    capabilities=sorted(CI_UNMAPPED_THREE),
                )
            ],
        )
        assert len(specs) == 1
        spec = specs[0]
        assert set(spec.capabilities) == CI_UNMAPPED_THREE
        # The label still names the obligation — only the payload changed.
        assert spec.primary_capability == "unmapped:UNMAPPED[3]"

    def test_ordinary_task_is_unchanged(self, orchestrator):
        specs = _expand(orchestrator, [_cp_task()])
        assert specs[0].capabilities == ("account-engine",)
        assert specs[0].primary_capability == "account-engine"

    def test_merged_bucket_keeps_both_names(self, orchestrator):
        """Two tasks, one command: the second task's names must not be lost."""
        specs = _expand(
            orchestrator,
            [
                _cp_task(task_id="task-0001", capability_id="account-engine"),
                _cp_task(task_id="task-0002", capability_id="ledger"),
            ],
        )
        assert len(specs) == 1
        assert set(specs[0].capabilities) == {"account-engine", "ledger"}

    def test_names_survive_serialisation(self, orchestrator):
        """The shard reads the plan from JSON, so the round trip is the contract."""
        specs = _expand(
            orchestrator,
            [
                _cp_task(
                    task_id="task-unmapped-review",
                    capability_id="unmapped:UNMAPPED[3]",
                    verification_kind="registry_mapping",
                    command="",
                    profile="unmapped-review",
                    capabilities=sorted(CI_UNMAPPED_THREE),
                )
            ],
        )
        restored = ExecutionTaskSpec.from_dict(specs[0].to_dict())
        assert set(restored.capabilities) == CI_UNMAPPED_THREE


class TestRegistryGapRecordNamesTheCapabilities:
    def test_record_names_all_three(self, orchestrator):
        """End to end through the executor: the diagnostic must name them."""
        specs = _expand(
            orchestrator,
            [
                _cp_task(
                    task_id="task-unmapped-review",
                    capability_id="unmapped:UNMAPPED[3]",
                    verification_kind="registry_mapping",
                    command="",
                    profile="unmapped-review",
                    capabilities=sorted(CI_UNMAPPED_THREE),
                )
            ],
        )
        record = orchestrator._execute_registry_mapping_task(specs[0], _Plan([]))
        assert record.completion_state == "registry_gap"
        assert record.capabilities == sorted(CI_UNMAPPED_THREE)
        detail = f"{record.reason} {record.diagnostic['message']}"
        for name in CI_UNMAPPED_THREE:
            assert name in detail
        assert record.diagnostic["unmapped_capabilities"] == sorted(CI_UNMAPPED_THREE)
