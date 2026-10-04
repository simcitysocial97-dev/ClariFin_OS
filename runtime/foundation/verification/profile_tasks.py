"""M10-R2 — expose canonical profile tasks to GitHub Actions as a matrix.

Why this exists
---------------
The three required verification gates each run **one** canonical profile command
(``verify backend``, ``verify frontend``, ``verify runtime``). In-process
parallelism (``M10-R2-C3``) made those tasks overlap inside one runner, which on a
2-core CI runner is a ceiling of roughly 2x. The remaining win needs GitHub to
schedule the independent obligations on **separate runners**.

That is only sound if the matrix legs are real canonical verification obligations.
This module therefore derives the matrix from the *same* task list
(:func:`runtime.foundation.verification.profiles.get_profile`) that the in-process
executor runs, so a leg cannot drift from what would have run in-process. It is not a
list of shell commands discovered by grepping a script.

The shape mirrors ``mutation.yml``: a plan step emits a dynamic matrix document, one
matrix leg executes one obligation, and a gate aggregates.

Obligation inventory (measured, not assumed)
--------------------------------------------
============  ==========================  =========  ==============
profile       executable obligations      serial est  longest single
============  ==========================  =========  ==============
``backend``   6 (ruff, black, mypy,      600 s      180 s
              unit, integration,
              schemathesis)
``runtime``   1 as a profile task, but    2730 s     2700 s
              the task wraps 2 distinct
              canonical obligations
``frontend``  1                            600 s      600 s
============  ==========================  =========  ==============

So:

* ``backend`` fans out cleanly — 6 independent obligations, ~3.3x available.
* ``frontend`` has **one** obligation. There is nothing to fan out, and pretending
  otherwise would be theatre. It is left alone and the reason is recorded.
* ``runtime`` is one 2700 s monolith that internally tracks two distinct canonical
  outcomes in its own ``FAILED_CHECKS`` list: the runtime test suite and
  ``runtime.verify integrity``. Those are separate obligations with separate
  evidence, so they are modelled as separate tasks rather than by splitting a shell
  script.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.foundation.verification.profiles import VerificationTask, get_profile

__all__ = [
    "ProfileLegResult",
    "AGGREGATED_TASK_NAME",
    "DEFAULT_MAX_PARALLEL",
    "aggregate_tasks",
    "executable_tasks",
    "expected_obligation_ids",
    "is_aggregate_task",
    "obligation_tasks",
    "profile_matrix",
    "read_leg_results",
    "run_obligation_leg",
    "summarise_legs",
    "verify_legs",
]

#: The rollup task a profile runs *after* its real obligations. It is name-skipped by
#: the in-process executor (a rollup of evidence that does not exist yet is not an
#: obligation), so it must be skipped here too or the matrix would contain a leg that
#: does nothing.
AGGREGATED_TASK_NAME = "Aggregate evidence"

#: Upper bound on concurrent legs per workflow. Deliberately modest: each leg may
#: itself fan out internally (``run_contract_tests.sh`` passes ``-n auto``), so a large
#: matrix multiplied by a large executor pool oversubscribes the runner and trades
#: elapsed time for flaky timeouts. 4 matches the executor's own bound.
DEFAULT_MAX_PARALLEL = 4


def executable_tasks(profile_op: str) -> list[VerificationTask]:
    """The canonical obligations of a profile, in declaration order.

    Declaration order is preserved deliberately: it is the order the in-process
    executor would have used, so evidence and failure reporting read the same whether
    a run was fanned out or not.
    """
    profile = get_profile(profile_op)
    return [t for t in profile.tasks if t.name != AGGREGATED_TASK_NAME]


# M10-R3 (L1c): one teardown margin for every backstop the runtime publishes.
from runtime.foundation.verification.execution_shards import (
    INFRA_BACKSTOP_MARGIN_SECONDS,
)


@dataclass(frozen=True, slots=True)
class ProfileLegResult:
    """One matrix leg's outcome, as written to disk for the gate to read."""

    profile: str
    task_id: str
    task_name: str
    status: str  # "passed" | "failed" | "timed_out"
    exit_code: int
    duration_seconds: float
    stdout_path: str = ""
    stderr_path: str = ""
    # M10-R3 (B2). The leg's own certification verdict and the fingerprint bracket it
    # was executed inside. Before this a leg reported only a status and an exit code,
    # so the aggregate could not tell a clean run on a stable tree from a clean run on
    # a tree that had moved underneath it — and it had no way to say so even after the
    # fact. Defaults keep an older document readable; absence is treated as
    # "not certified" by the gate rather than as a pass.
    decision: str = ""
    decision_reason: str = ""
    fingerprint_before: dict | None = None
    fingerprint_after: dict | None = None
    fingerprint_stable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "fingerprint_before": self.fingerprint_before,
            "fingerprint_after": self.fingerprint_after,
            "fingerprint_stable": self.fingerprint_stable,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ProfileLegResult:
        return cls(
            profile=d.get("profile", ""),
            task_id=d.get("task_id", ""),
            task_name=d.get("task_name", ""),
            status=d.get("status", ""),
            exit_code=int(d.get("exit_code", 1)),
            duration_seconds=float(d.get("duration_seconds", 0.0)),
            stdout_path=d.get("stdout_path", ""),
            stderr_path=d.get("stderr_path", ""),
            decision=d.get("decision", ""),
            decision_reason=d.get("decision_reason", ""),
            fingerprint_before=d.get("fingerprint_before"),
            fingerprint_after=d.get("fingerprint_after"),
            # Absent means unknown, and unknown is not stable.
            fingerprint_stable=bool(d.get("fingerprint_stable", False)),
        )

    @property
    def ok(self) -> bool:
        return self.status == "passed"


def is_aggregate_task(task: VerificationTask) -> bool:
    """True for a profile's evidence-rollup task.

    ``VerificationTask.dependencies`` is empty for every task in every profile, so the
    real data dependency — a rollup reads the evidence its siblings produced — is not
    represented in the model. In-process it is satisfied only by accident: the executor
    walks ``profile.tasks`` in declaration order, which happens to place the rollup
    last. A matrix destroys that accident, so the rollup is modelled explicitly as a
    **barrier phase**: it runs after every obligation leg, never beside one.

    This is a real dependency, not an ordering preference, which is why it earns a
    ``needs:`` edge and the obligation legs do not get one between themselves.
    """
    return task.name.startswith("Aggregate") or task.id.endswith("aggregate")


def obligation_tasks(profile_op: str) -> list[VerificationTask]:
    """Independent obligations: everything that is not the evidence rollup.

    These are the matrix legs. They carry no ``needs:`` between themselves because the
    profile declares no dependency among them, and adding a chain
    (``unit -> integration -> contract``) would serialise obligations that are in fact
    independent.
    """
    return [t for t in executable_tasks(profile_op) if not is_aggregate_task(t)]


def aggregate_tasks(profile_op: str) -> list[VerificationTask]:
    """Evidence rollups, which run after every obligation leg."""
    return [t for t in executable_tasks(profile_op) if is_aggregate_task(t)]


def profile_matrix(profile_op: str) -> str:
    """Render a profile's obligations as a GitHub Actions dynamic-matrix document.

    Only obligation legs are emitted. Rollup tasks are excluded deliberately: they
    depend on evidence the legs have not produced yet, so emitting them as peers would
    race. The gate runs them after the legs instead.

    ``max-parallel`` is published as an output for the job summary only and is **not**
    wired into job properties: a matrix job whose own properties are dynamic
    expressions does not expand (see ``mutation.yml``).
    """
    tasks = obligation_tasks(profile_op)
    total = sum(t.estimated_duration_seconds for t in tasks)
    longest = max((t.estimated_duration_seconds for t in tasks), default=0)

    # M10-R3 (L1c): the backstop this leg needs, published rather than hard-coded.
    # `backend-verify.yml` carried its own `:-1500` literal; the budget it must respect
    # is the one `run_obligation_leg` is given, which is the profile task timeout. The
    # literal and the runtime agreed only by coincidence.
    from runtime.foundation.verification.control_plane_facade import (
        _profile_task_timeout_seconds,
    )

    leg_budget_seconds = _profile_task_timeout_seconds()
    required_minutes = max(
        1, -(-(leg_budget_seconds + INFRA_BACKSTOP_MARGIN_SECONDS) // 60)
    )

    include = [
        {
            "index": i,
            "profile": profile_op,
            "task_id": t.id,
            "task_name": t.name,
            "command_count": len(t.commands),
            "estimated_seconds": t.estimated_duration_seconds,
            "required_timeout_minutes": required_minutes,
            "contractual_seconds": leg_budget_seconds,
        }
        for i, t in enumerate(tasks)
    ]

    document = {
        "include": include,
        "profile": profile_op,
        "leg_count": len(include),
        "estimated_serial_seconds": total,
        "estimated_critical_path_seconds": longest,
        "estimated_speedup": round(total / longest, 2) if longest else 1.0,
        "suggested_max_parallel": min(len(include), DEFAULT_MAX_PARALLEL),
        "aggregate_tasks": [t.id for t in aggregate_tasks(profile_op)],
        "task_ids": [t.id for t in tasks],
    }
    return json.dumps(document, indent=2)


def expected_obligation_ids(profile_op: str) -> list[str]:
    """Every obligation id the gate must see reported before it may certify."""
    return [t.id for t in obligation_tasks(profile_op)]


def read_leg_results(directory: Path) -> tuple[list[ProfileLegResult], list[str]]:
    """Read every ``leg-*.json`` in *directory*.

    Returns ``(results, unreadable)``. An unreadable file is reported rather than
    skipped: a leg that died mid-flight leaves no result, and the gate must treat that
    as a missing obligation rather than quietly certifying the ones that survived.
    """
    results: list[ProfileLegResult] = []
    unreadable: list[str] = []
    for path in sorted(Path(directory).glob("leg-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("leg document is not a JSON object")
            # Required keys are checked explicitly even though from_dict defaults
            # them. A leg document missing its identity is a *producer* fault and
            # must be reported as unreadable; defaulting it to "" would produce a
            # leg with an empty task_id that the gate then treats as an unknown
            # obligation, converting a producer bug into a confusing plan mismatch.
            for required in ("profile", "task_id", "status", "exit_code"):
                if required not in payload:
                    raise KeyError(required)
            # via from_dict so the certification fields (decision, fingerprint
            # bracket) are populated. Constructing the dataclass field-by-field here
            # would silently drop them and every leg would read as "unstable".
            results.append(ProfileLegResult.from_dict(payload))
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            unreadable.append(f"{path.name}: {type(exc).__name__}")
    return results, unreadable


def verify_legs(profile_op: str, results: list[ProfileLegResult]) -> list[str]:
    """Return the reasons this fan-out must NOT certify. Empty means certified.

    Four ways to fail, all of them obligations:

    1. a canonical obligation produced no result at all (missing leg);
    2. an obligation reported a non-passing status;
    3. an unknown task id was reported — the plan and the legs disagree, which is the
       same split-brain risk the reconcile shard merge guards against;
    4. **a leg ran on a repository state that moved** (M10-R3 B2).

    The fourth is new and is the point of the exercise. Until B2 a leg reported only a
    status and an exit code, so "every leg passed" meant "no shell exited non-zero" —
    a claim about exit codes, not a certification. A leg now carries the fingerprint
    bracket it ran inside, and this gate refuses the fan-out when any leg's bracket
    moved. A document with no bracket is treated as **unstable**, not as a pass: an
    older producer's document must not be readable as a clean leg.
    """
    expected = expected_obligation_ids(profile_op)
    expected_set = set(expected)
    seen: dict[str, ProfileLegResult] = {}
    problems: list[str] = []

    for result in results:
        if result.task_id in seen:
            problems.append(
                f"obligation {result.task_id} reported by more than one leg"
            )
            continue
        seen[result.task_id] = result

    missing = [task_id for task_id in expected if task_id not in seen]
    if missing:
        problems.append(
            f"missing {len(missing)} of {len(expected)} obligation(s): "
            + ", ".join(missing)
        )

    for task_id in expected:
        result = seen.get(task_id)
        if result is None:
            continue
        if not result.ok:
            problems.append(
                f"{task_id} ({result.task_name}) {result.status}"
                + (f" exit={result.exit_code}" if result.exit_code else "")
            )
        # Checked independently of status: a leg can pass its own command while the
        # tree it ran against is not the tree the gate is about to certify.
        if not result.fingerprint_stable:
            before = (result.fingerprint_before or {}).get("fingerprint", "")[:12]
            after = (result.fingerprint_after or {}).get("fingerprint", "")[:12]
            detail = (
                f"repository fingerprint changed during the leg "
                f"({before or 'unknown'} -> {after or 'unknown'})"
                if before or after
                else "leg reported no fingerprint bracket; cannot certify it"
            )
            problems.append(f"{task_id} ({result.task_name}) {detail}")

    unknown = sorted(set(seen) - expected_set)
    if unknown:
        problems.append(
            f"legs reported {len(unknown)} obligation(s) not in the canonical plan: "
            + ", ".join(unknown)
        )

    return problems


def summarise_legs(results: list[ProfileLegResult]) -> str:
    """A stable, deterministic summary for the job summary and logs."""
    rows = [
        f"| {r.task_id} | {r.task_name} | {r.status} | {r.duration_seconds:.1f} s |"
        f" {r.decision or 'unclassified'} |"
        f" {'stable' if r.fingerprint_stable else 'UNSTABLE'} |"
        for r in sorted(results, key=lambda x: x.task_id)
    ]
    return "\n".join(rows)


def run_obligation_leg(
    profile_op: str,
    task_id: str,
    *,
    result_out: Path,
    timeout_seconds: int,
) -> ProfileLegResult:
    """Execute exactly one canonical obligation and record its outcome.

    The command comes from the profile's own task list and is executed by the same
    worker the in-process executor uses, writing to the same
    ``runtime/generated/profile-logs/<profile>/<task>-*`` evidence paths. So a leg is
    not a re-implementation of the obligation — it is the obligation, scheduled on its
    own runner.

    The result document is written **before** returning, including for a failing or
    timed-out task: the gate decides from these documents, and a leg that reports
    nothing is indistinguishable from a leg that never ran. That ambiguity is treated
    as a missing obligation, never as success.
    """
    from runtime.foundation.verification.parallel_executor import (
        ProgressContext,
        run_streaming_command,
    )

    tasks = {t.id: t for t in executable_tasks(profile_op)}
    task = tasks.get(task_id)
    if task is None:
        raise ValueError(
            f"{task_id!r} is not an obligation of profile {profile_op!r}; "
            f"known: {', '.join(sorted(tasks))}"
        )

    from runtime.foundation.verification.env import child_process_env

    log_root = Path("runtime/generated/profile-logs") / profile_op
    stdout_path = log_root / f"{task.id}-stdout.log"
    stderr_path = log_root / f"{task.id}-stderr.log"

    # M10-R3 (B2) — a leg brackets itself in the shared certification authority.
    #
    # A CI leg is the unit that actually runs in the matrix, so it is the unit that
    # must be able to say "the repository was provably unchanged while I ran". Before
    # this it could not: `ProfileLegResult` carried a status, an exit code and two log
    # paths, and nothing else. The gate read those documents and had no way to
    # distinguish "ran clean" from "ran clean on a tree that had moved".
    from runtime.foundation.verification.execution_orchestrator import (
        CertificationRun,
        CompletionState,
    )

    certification = CertificationRun(plan_id=f"leg:{profile_op}:{task_id}")
    certification.__enter__()

    last = None
    for index, command in enumerate(task.commands):
        suffix = f"-{index}" if len(task.commands) > 1 else ""
        last = run_streaming_command(
            command,
            stdout_path=log_root / f"{task.id}{suffix}-stdout.log",
            stderr_path=log_root / f"{task.id}{suffix}-stderr.log",
            timeout_seconds=timeout_seconds,
            env=child_process_env(),
            # M10-R2 closeout: live lifecycle logging. This is the seam the backend
            # obligation legs and the Playwright legs both execute through, so one change
            # covers both without either workflow inventing its own heartbeat.
            progress=ProgressContext(
                label=f"{profile_op}:{task.id}",
                kind="obligation",
                log_dir=log_root,
                timeout_seconds=timeout_seconds,
            ),
        )
        if last.infra_error or last.timed_out or last.exit_code != 0:
            break

    certification.__exit__(None, None, None)

    if last is None:
        status, exit_code, duration = "failed", 127, 0.0
        state, detail = CompletionState.INFRASTRUCTURE, "no command was executed"
    elif last.timed_out:
        status, exit_code, duration = "timed_out", 124, last.duration_seconds
        state = CompletionState.TIMEOUT
        detail = f"exceeded the {timeout_seconds}s obligation budget"
    elif last.infra_error:
        status, exit_code, duration = "failed", 127, last.duration_seconds
        state = CompletionState.INFRASTRUCTURE
        detail = last.infra_error
    elif last.exit_code != 0:
        status, exit_code, duration = (
            "failed",
            int(last.exit_code or 1),
            (last.duration_seconds),
        )
        state = CompletionState.FAILED
        detail = f"exit {last.exit_code}"
    else:
        status, exit_code, duration = "passed", 0, last.duration_seconds
        state, detail = CompletionState.PASS, ""

    certification.record(task.id, state, is_mandatory=True, detail=detail)
    decision, reason = certification.decide()
    outcome = certification.to_dict()
    outcome["topology"] = f"leg:{profile_op}"

    result = ProfileLegResult(
        profile=profile_op,
        task_id=task.id,
        task_name=task.name,
        status=status,
        exit_code=exit_code,
        duration_seconds=round(duration, 2),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        # The leg's own classification, alongside its status. The gate can now refuse a
        # leg whose tree moved without re-deriving anything.
        decision=decision.value,
        decision_reason=reason,
        fingerprint_before=outcome["fingerprint_before"],
        fingerprint_after=outcome["fingerprint_after"],
        fingerprint_stable=outcome["fingerprint_stable"],
    )
    result_out.parent.mkdir(parents=True, exist_ok=True)
    result_out.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return result
