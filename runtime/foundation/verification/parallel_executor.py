"""
M9-C57 — Parallel execution support for independent verification tasks.

Groups independent tasks into parallel bundles and executes them via
ProcessPoolExecutor while respecting dependency ordering.  Falls back
to sequential execution when the parallel path is unavailable.

Design contract:
  * Tasks with no inter-dependencies run in parallel.
  * Tasks that depend on other tasks form a separate sequential group.
  * max_workers defaults to min(cpu_count, 4).
  * Timeout is enforced per-task, not per-group.
  * Results are collected incrementally as each task completes.
  * If parallel execution raises, the whole run falls back to sequential.
"""

from __future__ import annotations

import concurrent.futures
import multiprocessing
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# ---------------------------------------------------------------------------
# Public data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TaskResult:
    """Result of a single parallel task execution."""

    task_id: str
    component: str
    capability: str
    success: bool
    exit_code: int
    duration_seconds: float
    error: str | None = None
    output_path: str = ""


@dataclass(frozen=True, slots=True)
class TaskGroup:
    """A group of tasks that can be executed together."""

    tasks: tuple[Any, ...]
    parallel: bool
    dependency_on: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_ids": [t.task_id if hasattr(t, "task_id") else str(i) for i, t in enumerate(self.tasks)],
            "parallel": self.parallel,
            "dependency_on": self.dependency_on,
        }


@dataclass
class ExecutionReport:
    """Aggregate report from a parallel execution run."""

    plan_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    total_duration_seconds: float = 0.0
    results: list[TaskResult] = field(default_factory=list)
    groups_executed: int = 0
    parallel_groups: int = 0
    sequential_groups: int = 0
    fallback_sequential: bool = False
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_seconds": self.total_duration_seconds,
            "results": [r.__dict__ for r in self.results],
            "groups_executed": self.groups_executed,
            "parallel_groups": self.parallel_groups,
            "sequential_groups": self.sequential_groups,
            "fallback_sequential": self.fallback_sequential,
            "errors": list(self.errors),
        }

    @property
    def all_passed(self) -> bool:
        return all(r.success for r in self.results)

    @property
    def exit_code(self) -> int:
        failed = [r for r in self.results if not r.success]
        return 1 if failed else 0


# ---------------------------------------------------------------------------
# Worker function (must be top-level for ProcessPoolExecutor pickling)
# ---------------------------------------------------------------------------


def _run_task(
    task: Any,
    worker_id: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Execute a single task inside a worker process.

    Accepts either an ExecutableVerificationTask (with execution_command)
    or a plain dict with at least a 'command' key.
    """
    import subprocess  # noqa: PLC0415

    if hasattr(task, "execution_command"):
        command = task.execution_command
        task_id = task.task_id
        component = task.component
        capability = task.capability
    elif isinstance(task, dict):
        command = task.get("command", "")
        task_id = task.get("task_id", f"unknown-{worker_id}")
        component = task.get("component", "")
        capability = task.get("capability", "")
    else:
        return {
            "task_id": str(worker_id),
            "success": False,
            "exit_code": -1,
            "duration_seconds": 0.0,
            "error": f"Unsupported task type: {type(task).__name__}",
        }

    if not command:
        return {
            "task_id": task_id,
            "success": False,
            "exit_code": -1,
            "duration_seconds": 0.0,
            "error": "Empty command",
        }

    start = datetime.now(UTC)
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=os.environ.copy(),
        )
        duration = (datetime.now(UTC) - start).total_seconds()
        return {
            "task_id": task_id,
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "duration_seconds": duration,
            "error": proc.stderr if proc.returncode != 0 else None,
            "output_path": "",
        }
    except subprocess.TimeoutExpired:
        duration = (datetime.now(UTC) - start).total_seconds()
        return {
            "task_id": task_id,
            "success": False,
            "exit_code": -1,
            "duration_seconds": duration,
            "error": f"Timed out after {timeout_seconds}s",
            "output_path": "",
        }
    except Exception as exc:
        duration = (datetime.now(UTC) - start).total_seconds()
        return {
            "task_id": task_id,
            "success": False,
            "exit_code": -1,
            "duration_seconds": duration,
            "error": str(exc),
            "output_path": "",
        }


# ---------------------------------------------------------------------------
# ParallelExecutor
# ---------------------------------------------------------------------------


class ParallelExecutor:
    """Executes independent verification tasks in parallel groups.

    Parameters
    ----------
    max_workers : int
        Maximum number of concurrent worker processes.  Capped at 4 and at
        least 1.  Defaults to the number of CPUs (clamped to [1, 4]).
    per_task_timeout : int
        Per-task timeout in seconds.  Defaults to 600.
    """

    def __init__(
        self,
        max_workers: int | None = None,
        per_task_timeout: int = 600,
    ) -> None:
        cpu_count = max(1, multiprocessing.cpu_count())
        self.max_workers = max(1, min(cpu_count, 4, max_workers or cpu_count))
        self.per_task_timeout = per_task_timeout

    # -- planning ----------------------------------------------------------

    def plan_parallel_groups(
        self,
        tasks: list[Any],
    ) -> list[TaskGroup]:
        """Partition *tasks* into parallel and sequential groups.

        Grouping rules:
          1. Tasks whose ``depends_on`` (or ``dependencies``) are empty form
             a single parallel group.
          2. Tasks that declare dependencies on other task IDs form sequential
             groups ordered by dependency depth.
          3. A task with ``dependency_on`` set is placed in a group after the
             referenced task finishes.
        """
        if not tasks:
            return []

        id_set = {getattr(t, "task_id", str(i)) for i, t in enumerate(tasks)}

        # Partition into independent vs dependent
        independent: list[Any] = []
        dependent: list[Any] = []

        for t in tasks:
            deps = getattr(t, "depends_on", ()) or getattr(t, "dependencies", [])
            if not deps:
                independent.append(t)
            else:
                dependent.append(t)

        groups: list[TaskGroup] = []

        if independent:
            groups.append(TaskGroup(
                tasks=tuple(independent),
                parallel=True,
                dependency_on=None,
            ))

        # Sort dependent tasks by dependency depth for sequential ordering
        sorted_dependent = self._topological_sort(dependent, id_set)
        if sorted_dependent:
            groups.append(TaskGroup(
                tasks=tuple(sorted_dependent),
                parallel=False,
                dependency_on=None,
            ))

        # If any task references another via dependency_on, split it out
        final_groups: list[TaskGroup] = []
        for group in groups:
            has_ext_dep = any(
                getattr(t, "dependency_on", None)
                for t in group.tasks
            )
            if not has_ext_dep:
                final_groups.append(group)
            else:
                standalone = [t for t in group.tasks if not getattr(t, "dependency_on", None)]
                dependent_tasks = [t for t in group.tasks if getattr(t, "dependency_on", None)]
                if standalone:
                    final_groups.append(TaskGroup(
                        tasks=tuple(standalone),
                        parallel=len(standalone) > 1,
                        dependency_on=None,
                    ))
                for dt in dependent_tasks:
                    final_groups.append(TaskGroup(
                        tasks=(dt,),
                        parallel=False,
                        dependency_on=getattr(dt, "dependency_on"),
                    ))

        return final_groups if final_groups else [TaskGroup(
            tasks=tuple(tasks),
            parallel=len(tasks) > 1,
            dependency_on=None,
        )]

    def _topological_sort(
        self,
        tasks: list[Any],
        known_ids: set[str],
    ) -> list[Any]:
        """Order dependent tasks by depth so prerequisites execute first."""
        visited: set[str] = set()
        order: list[Any] = []

        def _visit(task: Any, depth: int = 0) -> None:
            tid = getattr(task, "task_id", str(depth))
            if tid in visited:
                return
            visited.add(tid)
            deps = getattr(task, "depends_on", ()) or getattr(task, "dependencies", [])
            for dep_id in deps:
                if dep_id in known_ids and dep_id != tid:
                    dep_task = next(
                        (t for t in tasks if getattr(t, "task_id", "") == dep_id),
                        None,
                    )
                    if dep_task and dep_task not in order:
                        _visit(dep_task, depth + 1)
            order.append(task)

        for t in tasks:
            _visit(t)
        return order

    # -- execution ---------------------------------------------------------

    def execute_parallel(
        self,
        groups: list[TaskGroup],
        *,
        plan_id: str = "",
    ) -> ExecutionReport:
        """Execute task groups and return an ExecutionReport.

        Parallel groups are dispatched via ProcessPoolExecutor; sequential
        groups run one task at a time.  Results stream in as each task
        completes.

        If ProcessPoolExecutor cannot be initialised (e.g. frozen-stdio
        environment), execution falls back to the sequential path.
        """
        report = ExecutionReport(
            plan_id=plan_id,
            started_at=datetime.now(UTC).isoformat(),
        )
        all_results: list[TaskResult] = []

        try:
            use_parallel = self._can_use_pool()
        except Exception:
            use_parallel = False

        for group_idx, group in enumerate(groups):
            group_started = datetime.now(UTC)

            if group.parallel and use_parallel:
                group_results = self._execute_parallel_group(group)
                report.parallel_groups += 1
            else:
                group_results = self._execute_sequential_group(group)
                report.sequential_groups += 1

            all_results.extend(group_results)
            report.groups_executed += 1

            group_duration = (
                datetime.now(UTC) - group_started
            ).total_seconds()

        report.results = all_results
        report.completed_at = datetime.now(UTC).isoformat()
        report.total_duration_seconds = (
            datetime.fromisoformat(report.completed_at)
            - datetime.fromisoformat(report.started_at)
        ).total_seconds()

        if not use_parallel and len(groups) > 1:
            report.fallback_sequential = True

        return report

    def _execute_parallel_group(
        self,
        group: TaskGroup,
    ) -> list[TaskResult]:
        """Run all tasks in a parallel group concurrently."""
        results: list[TaskResult] = []
        futures: dict[concurrent.futures.Future, Any] = {}

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers,
        ) as pool:
            for idx, task in enumerate(group.tasks):
                future = pool.submit(
                    _run_task,
                    task,
                    idx,
                    self.per_task_timeout,
                )
                futures[future] = task

            for future in concurrent.futures.as_completed(futures):
                task = futures[future]
                try:
                    data = future.result(timeout=self.per_task_timeout + 10)
                except Exception as exc:
                    data = {
                        "task_id": getattr(task, "task_id", "unknown"),
                        "success": False,
                        "exit_code": -1,
                        "duration_seconds": 0.0,
                        "error": str(exc),
                    }

                results.append(TaskResult(
                    task_id=data.get("task_id", "unknown"),
                    component=getattr(task, "component", ""),
                    capability=getattr(task, "capability", ""),
                    success=data.get("success", False),
                    exit_code=data.get("exit_code", -1),
                    duration_seconds=data.get("duration_seconds", 0.0),
                    error=data.get("error"),
                    output_path=data.get("output_path", ""),
                ))

        return results

    def _execute_sequential_group(
        self,
        group: TaskGroup,
    ) -> list[TaskResult]:
        """Run tasks in a group one after another."""
        results: list[TaskResult] = []
        for idx, task in enumerate(group.tasks):
            data = _run_task(task, idx, self.per_task_timeout)
            results.append(TaskResult(
                task_id=data.get("task_id", "unknown"),
                component=getattr(task, "component", ""),
                capability=getattr(task, "capability", ""),
                success=data.get("success", False),
                exit_code=data.get("exit_code", -1),
                duration_seconds=data.get("duration_seconds", 0.0),
                error=data.get("error"),
                output_path=data.get("output_path", ""),
            ))
        return results

    @staticmethod
    def _can_use_pool() -> bool:
        """Return True if a ProcessPoolExecutor can be safely created."""
        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=1) as pool:
                return pool._shutdown is False  # type: ignore[attr-defined]
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def execute_tasks_in_parallel(
    tasks: list[Any],
    *,
    max_workers: int | None = None,
    plan_id: str = "",
) -> ExecutionReport:
    """One-shot helper: plan groups then execute."""
    executor = ParallelExecutor(max_workers=max_workers)
    groups = executor.plan_parallel_groups(tasks)
    return executor.execute_parallel(groups, plan_id=plan_id)


__all__ = [
    "ExecutionReport",
    "ParallelExecutor",
    "TaskGroup",
    "TaskResult",
    "execute_tasks_in_parallel",
]
