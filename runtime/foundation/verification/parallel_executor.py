"""M10-R2 — the single parallel execution core for verification.

This module is the one place a verification subprocess is run, and the one place
concurrent execution is scheduled. Both canonical call paths go through it:

* ``ExecutionOrchestrator.execute`` (``verify check``)
* ``ControlPlane._run_profile_alias`` (``verify backend|frontend|runtime|quick|…``)

Why this module exists (M10-R2 D1)
----------------------------------
``ParallelExecutor` already existed and was **unwired** — imported by nothing in the
executor path. It was not reused as-is because four things were wrong for the
canonical path:

1. **Buffered output.** It used ``capture_output=True``. The orchestrator's own worker
   deliberately streams to per-task evidence files instead, because on 2026-09-30 a
   killed run left all 20 task logs at zero bytes and the failing obligation's output
   was unrecoverable. Reintroducing buffering would regress that fix.
2. **No process-group kill.** A wrapper timeout orphaned the
   shell → pytest → children tree.
3. **Wrong dependency model.** It read ``dependency_on``/``dependencies``; the plan
   model uses ``depends_on`` and gates on ``is_escalation``.
4. **No result vocabulary.** It returned dicts, so nothing downstream could read a
   termination reason or a completion state.

What was kept is the part that was right: bounded workers, group planning,
non-fail-fast collection, per-task timeout. ``TaskGroup``/``ExecutionReport``/
``ParallelExecutor`` remain as the group-oriented façade (their tests are preserved);
the low-level process execution beneath them is now the promoted streaming worker.

Concurrency primitive: **threads**, not processes.
--------------------------------------------------------
The work is "wait for a subprocess", which is I/O-bound. ``ProcessPoolExecutor``
would additionally require the task spec, plan and orchestrator (``self``) to be
picklable — they are not (they hold command-override dicts, registries and unpicklable
evidence objects). Threads also keep ``on_record`` callbacks in-process, so partial
progress stays observable exactly as it is today. This is a deliberate divergence from
the original implementation, not an oversight.
"""

from __future__ import annotations

import contextlib
import os
import re
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "CommandResult",
    "DEFAULT_MAX_WORKERS",
    "ExecutionReport",
    "ParallelExecutor",
    "TaskGroup",
    "TaskResult",
    "classify_termination",
    "execute_tasks_in_parallel",
    "max_workers_for",
    "plan_parallel_groups",
    "resolve_max_workers",
    "run_streaming_command",
    "summarise_pytest_outcome",
]

#: Upper bound on concurrent subprocesses. Never ``os.cpu_count()`` unbounded: a
#: developer laptop must not become a process storm, and every task already forks its
#: own pytest/xdist workers (``run_contract_tests.sh`` passes ``-n auto``), so
#: unbounded concurrency would oversubscribe rather than speed anything up.
DEFAULT_MAX_WORKERS = 4

REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Promoted worker primitives (moved from execution_orchestrator)
# ---------------------------------------------------------------------------


@dataclass
class CommandResult:
    """Everything observable about one subprocess execution.

    Both the orchestrator's record builder and the group-oriented façade consume this,
    which is what makes the streaming worker the *single* execution path rather than
    two runners with the same name.
    """

    command: str
    exit_code: int | None
    timed_out: bool
    infra_error: str | None
    stdout: str
    stderr: str
    stdout_path: Path
    stderr_path: Path
    duration_seconds: float


def _tee(pipe, path: Path) -> None:
    """Stream a pipe to *path*, flushing per line.

    Moved from ``execution_orchestrator._tee``. The flush-per-line is the whole point:
    it makes the evidence file exist and grow *while* the child runs, so a kill, a
    signal or an orchestrator crash still leaves the output produced up to that instant.
    """
    try:
        with open(path, "a", encoding="utf-8", errors="replace") as fh:
            for line in iter(pipe.readline, ""):
                fh.write(line)
                fh.flush()
    except (OSError, ValueError):
        pass
    finally:
        with contextlib.suppress(Exception):
            pipe.close()


def _kill_process_group(proc) -> None:
    """Kill the child's whole process group.

    A shell task runs a shell that runs pytest that runs more processes; killing only
    the direct child orphans them and they keep running against the evidence
    directory. ``start_new_session=True`` at spawn time is what makes this possible.
    """
    try:
        os.killpg(os.getpgid(proc.pid), 9)
    except (ProcessLookupError, PermissionError, OSError):
        with contextlib.suppress(Exception):
            proc.kill()
    with contextlib.suppress(Exception):
        proc.wait(timeout=5)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


@dataclass(frozen=True, slots=True)
class ProgressContext:
    """Opt-in live-logging context for one long-running command.

    M10-R2 closeout. This exists because M10-R2-C3 moved task output out of stdout and
    into per-task evidence files. That change was correct — it fixed the 0-byte-log
    problem — but it silently removed the only *live* signal a CI operator had. A leg
    would print one line and then go silent for the twenty minutes that mattered, and
    the two remaining CI failures were undiagnosable for exactly that reason.

    The contract is deliberately narrow:

    * **Lifecycle, not content.** The start/heartbeat/terminal lines say what is running,
      for how long, and how it ended. The command's own output stays in the artifact.
      A twenty-minute pytest run must not become a twenty-minute CI log.
    * **Opt-in.** ``progress=None`` is byte-identical to the pre-M10-R2 behaviour, so
      local runs and the existing suite are untouched.
    * **Driven by a watchdog, not by the output stream.** The parent blocks in
      ``proc.wait(timeout=...)``, so anything driven by the child's output emits nothing
      during exactly the window the operator needs to see. A command shorter than one
      interval never reaches a tick, so a fast obligation costs only its two lifecycle
      lines with no extra suppression rule needed.
    """

    label: str
    #: One of "shard", "obligation", "task", "integrity". Purely descriptive; it appears
    #: in the start line so a reader can tell what kind of unit is executing.
    kind: str
    #: Where the FULL output lives, echoed once so the log points at the artifact.
    log_dir: Path
    timeout_seconds: int


def _progress_stream():
    """The stream progress lines go to: stderr, resolved at CALL time.

    Never stdout — stdout is reserved for machine-readable documents, the invariant
    established when a `[check] boundary=` banner corrupted a shard report.

    Resolved per call rather than bound at import so that any later redirection of
    ``sys.stderr`` (a test harness, a log wrapper) is honoured. Binding the stream once
    at import time silently defeats both.
    """
    return sys.stderr


def _progress_enabled() -> bool:
    return os.environ.get("VERIFY_PROGRESS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _heartbeat_seconds(override: int | None) -> int:
    if override is not None:
        return max(0, int(override))
    raw = os.environ.get("VERIFY_HEARTBEAT_SECONDS")
    if raw:
        with contextlib.suppress(ValueError):
            return max(0, int(raw))
    return 60


def _emit_progress(line: str) -> None:
    """Write one progress line, never raising.

    Instrumentation must not be able to fail a verification run.
    """
    # Diagnostics must never be able to fail a verification run.
    with contextlib.suppress(Exception):
        print(line, file=_progress_stream(), flush=True)


def _heartbeat_loop(
    stop: threading.Event,
    label: str,
    t0: float,
    interval: int,
) -> None:
    """Emit ``running elapsed=Ns`` until *stop* is set.

    A plain daemon thread rather than anything derived from the child's output: the
    parent is blocked in ``proc.wait()`` for the whole run, so an output-driven heartbeat
    would be silent for the entire duration it exists to cover.
    """
    while not stop.wait(interval):
        _emit_progress(f"[{label}] running elapsed={int(time.monotonic() - t0)}s")


def run_streaming_command(
    command: str,
    *,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: int,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    progress: ProgressContext | None = None,
    heartbeat_seconds: int | None = None,
) -> CommandResult:
    """Run *command*, streaming stdout/stderr to the given evidence files.

    Promoted verbatim in behaviour from
    ``ExecutionOrchestrator._execute_shell_task``, minus the record/classification
    layer that belongs to the caller. Guarantees:

    * both evidence files are truncated up front, so a file means "this execution"
      (the tee appends, so leftover content from an earlier run would otherwise
      masquerade as this run's output);
    * output is streamed, never buffered;
    * the child gets its own process group and a timeout kills the whole tree;
    * both files are touched afterwards so they exist even if the child produced
      nothing and was killed before its first line.

    *progress* adds live lifecycle lines to stderr. It is None by default, which is
    exactly the behaviour above with no output at all.
    """
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    for stale in (stdout_path, stderr_path):
        with contextlib.suppress(OSError):
            stale.unlink()

    t0 = time.monotonic()
    exit_code: int | None = None
    timed_out = False
    infra_error: str | None = None

    emit = progress is not None and _progress_enabled()
    if emit and progress is not None:
        _emit_progress(
            f"[{progress.label}] start kind={progress.kind} "
            f"timeout={timeout_seconds}s logs={progress.log_dir}"
        )

    interval = _heartbeat_seconds(heartbeat_seconds)
    stop = threading.Event()
    watchdog: threading.Thread | None = None
    if emit and progress is not None and interval > 0:
        watchdog = threading.Thread(
            target=_heartbeat_loop,
            args=(stop, progress.label, t0, interval),
            daemon=True,
        )
        watchdog.start()

    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            cwd=str(cwd or REPO_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        readers = [
            threading.Thread(target=_tee, args=(proc.stdout, stdout_path), daemon=True),
            threading.Thread(target=_tee, args=(proc.stderr, stderr_path), daemon=True),
        ]
        for reader in readers:
            reader.start()
        try:
            proc.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            exit_code = 124
            _kill_process_group(proc)
        for reader in readers:
            reader.join(timeout=5)
        # A shell that dies on a signal reports 128+signum, so >128 is a termination
        # rather than a command's own exit status.
        if exit_code is None:
            exit_code = proc.returncode
    except FileNotFoundError as exc:
        infra_error = f"command not found: {exc}"
    except Exception as exc:  # defensive
        infra_error = f"subprocess raised: {type(exc).__name__}: {exc}"
    finally:
        stop.set()
        if watchdog is not None:
            watchdog.join(timeout=2)

    stdout_path.touch(exist_ok=True)
    stderr_path.touch(exist_ok=True)

    duration = time.monotonic() - t0
    termination = classify_termination(exit_code, timed_out, infra_error)

    if emit and progress is not None:
        # The terminal line carries the termination KIND, not just a non-zero status, so
        # the log distinguishes a timeout from a signal death from an ordinary failure
        # without anyone opening an artifact.
        _emit_progress(
            f"[{progress.label}] exit={exit_code} elapsed={duration:.1f}s "
            f"timeout={'true' if timed_out else 'false'} "
            f"term={termination['kind']} stdout={stdout_path} stderr={stderr_path}"
        )

    return CommandResult(
        command=command,
        exit_code=exit_code,
        timed_out=timed_out,
        infra_error=infra_error,
        stdout=_read_text(stdout_path),
        stderr=_read_text(stderr_path),
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        duration_seconds=duration,
    )


_PYTEST_FAILURE_LINE = re.compile(r"^(FAILED|ERROR)\s+(\S+)", re.MULTILINE)
_PYTEST_TIMEOUT_MARKER = "from pytest-timeout"
_PYTEST_SUMMARY = re.compile(
    r"^(?:(\d+) failed)?(?:,?\s*(\d+) passed)?(?:,?\s*(\d+) skipped)?"
    r"(?:,?\s*(\d+) error)?(?:,?\s*(\d+) xfailed)?"
    r"(?:,?\s*(\d+) xpassed)?.*?in\s+(\d+\.?\d*)s",
    re.MULTILINE,
)


def summarise_pytest_outcome(text: str) -> dict | None:
    """Name the inner pytest failure precisely, from its own output.

    A verification script that runs pytest and then aggregates several checks exits
    with a single non-zero status, which loses the distinction the investigation
    actually needs: was this an assertion failure, a per-test timeout, or a
    collection/internal error? Those have different causes and different fixes, and
    "the suite failed" is not evidence for any of them.

    Returns None when the text contains no pytest signal at all, so callers can leave
    non-pytest tasks untouched. The classification is derived only from pytest's own
    summary and short-summary lines — it never re-runs anything and never guesses.

    Moved here from ``execution_orchestrator`` in M10-R2 so the diagnosis vocabulary
    lives with the worker that produces the output being diagnosed.
    """
    if not text or ("pytest" not in text and "passed" not in text):
        return None

    failed = _PYTEST_FAILURE_LINE.findall(text)
    summary = _PYTEST_SUMMARY.search(text)
    counts = {
        "failed": int(summary.group(1)) if summary and summary.group(1) else 0,
        "passed": int(summary.group(2)) if summary and summary.group(2) else 0,
        "skipped": (int(summary.group(3)) if summary and summary.group(3) else 0),
        "errors": int(summary.group(4)) if summary and summary.group(4) else 0,
        "xfailed": (int(summary.group(5)) if summary and summary.group(5) else 0),
        "xpassed": (int(summary.group(6)) if summary and summary.group(6) else 0),
    }
    duration = float(summary.group(7)) if summary and summary.group(7) else None

    if not failed and not summary:
        return None

    timed_out = _PYTEST_TIMEOUT_MARKER in text
    errored = any(tag == "ERROR" for tag, _ in failed) or counts["errors"] > 0

    if timed_out:
        kind = "TEST_TIMEOUT"
    elif errored:
        kind = "COLLECTION_OR_INTERNAL_ERROR"
    elif counts["failed"] or failed:
        kind = "TEST_ASSERTION_FAILURE"
    else:
        kind = "PASSED"

    return {
        "kind": kind,
        "failed_nodeids": [nodeid for _, nodeid in failed],
        "counts": counts,
        "duration_seconds": duration,
    }


def classify_termination(
    exit_code: int | None,
    timed_out: bool,
    infra_error: str | None,
) -> dict:
    """Say *how* a task's process ended, not just that it did not pass.

    "the command exited non-zero" is not a diagnosis. A verification run can end
    because a test failed, because the wrapper killed it, because the process was
    killed by a signal, or because the command never started, and each of those points
    at a different cause. The record keeps them apart so a long run cannot be misread
    as a flaky one.

    Moved here from ``execution_orchestrator`` (M10-R2) so every caller of the worker
    shares one termination vocabulary.
    """
    if infra_error:
        return {
            "kind": "INFRASTRUCTURE",
            "detail": infra_error,
            "signal": None,
        }
    if timed_out:
        return {
            "kind": "WRAPPER_TIMEOUT",
            "detail": "verification wrapper killed the command before it finished",
            "signal": None,
        }
    if exit_code is not None and exit_code < 0:
        return {
            "kind": "SIGNAL_TERMINATION",
            "detail": f"child terminated by signal {-exit_code}",
            "signal": -exit_code,
        }
    if exit_code is not None and exit_code > 128:
        signum = exit_code - 128
        try:
            signame = signal.Signals(signum).name
        except ValueError:
            signame = f"SIG{signum}"
        return {
            "kind": "SIGNAL_TERMINATION",
            "detail": f"shell reported 128+{signum} ({signame})",
            "signal": signum,
        }
    if exit_code == 0:
        return {
            "kind": "EXIT_ZERO",
            "detail": "command exit 0",
            "signal": None,
        }
    return {
        "kind": "EXIT_NONZERO",
        "detail": f"command reported exit {exit_code}",
        "signal": None,
    }


# ---------------------------------------------------------------------------
# Worker bound
# ---------------------------------------------------------------------------


def resolve_max_workers(requested: int | None = None) -> int:
    """Bounded concurrency policy.

    ``VERIFY_MAX_WORKERS`` is the explicit override. The default is
    ``min(cpu_count, 4)`` and is clamped to ``>= 1``; it is never unbounded.
    """
    if requested is None:
        env = os.environ.get("VERIFY_MAX_WORKERS")
        if env:
            with contextlib.suppress(ValueError):
                requested = int(env)
    if requested is None:
        requested = DEFAULT_MAX_WORKERS
    try:
        requested = int(requested)
    except (TypeError, ValueError):
        requested = DEFAULT_MAX_WORKERS
    cpus = os.cpu_count() or 2
    return max(1, min(requested, cpus, DEFAULT_MAX_WORKERS * 4))


def max_workers_for(item_count: int, requested: int | None = None) -> int:
    """Concurrency never exceeds the work available."""
    return max(1, min(resolve_max_workers(requested), max(1, item_count)))


# ---------------------------------------------------------------------------
# CPU budget (M10-R3 / D)
#
# The missing execution condition.
#
# Checkpoint A reproduced the reconcile failure and established its mechanism. The
# shard planner assigns by *estimated_seconds*, and the matrix renders that as a SUM —
# which is only correct if a shard executes serially. It does not: the executor runs up
# to DEFAULT_MAX_WORKERS tasks concurrently. Worse, some of those tasks fork their own
# worker pools: `run_contract_tests.sh:78` and `run_fast_checks.sh:89` both pass
# `-n auto` to pytest.
#
# So shard 6 ran `exec-0002` (contract, `-n auto`), `exec-0003` (fast_checks, `-n
# auto`) and `exec-0004` (property) concurrently — roughly 7 CPU-bound Python processes
# against 4 cores, and against 2 on a standard GitHub runner. The measured consequence
# was that `exec-0002` burned 180.3 s of a 360 s budget while `exec-0003` burned 352.2 s
# of a task declared `estimated_duration=60`. Correct obligations were reclassified
# TIMED_OUT, and the run looked like a slow or broken suite rather than
# oversubscription.
#
# Nothing in the runtime modelled CPU as a consumable resource. Concurrency was a
# *worker count*, which is only the same thing as CPU when every task is single-threaded
# — an assumption this repository violates in two of its own shell scripts.
# ---------------------------------------------------------------------------

#: Matches an xdist/pytest worker-count flag in any of its spellings. Used to *derive*
#: CPU demand from the command rather than trusting a hand-maintained declaration —
#: a declared value that can drift from the command is exactly the kind of inert field
#: this milestone is removing.
#: ``-n`` is also the prefix of six shell comparison operators — ``-ne``, ``-eq``,
#: ``-lt``, ``-gt``, ``-le``, ``-ge`` — which appear inside ``[ ... ]`` tests. The
#: lookahead rejects exactly those. It deliberately does not reject ``-nauto``: the
#: operator set is enumerated rather than expressed as "any letters", because
#: ``-n auto`` is xdist and ``-nauto`` is also xdist, while every other suffix belongs
#: to something else.
_CPU_FLAG_RE = re.compile(
    r"(?:^|\s)(?:-n(?![qe][dlgt]?\b)|--numprocesses)(?:[=\s]+)?([A-Za-z0-9_$'\"$]+)"
)

#: ``bash <script>`` / ``sh <script>`` / ``. <script>`` — the indirection that hides a
#: worker-count flag from a plain scan of the command string.
_SCRIPT_INDIRECTION_RE = re.compile(
    r"(?:^|\s)(?:bash|sh|zsh|\.)\s+([^\s;|]+\.sh)\b"
)

#: A shell string test — ``[ -n "$X" ]``, ``[ -n "$X" -a -n "$Y" ]``.
#:
#: Without this, ``_CPU_FLAG_RE`` matches the ``-n`` inside every ``[ -n ... ]``
#: conditional in a shell script and reports the *variable name* as a worker count.
#: Every one of this repository's scripts is full of them, so the exclusion is what
#: makes the scan find the real flag at all — ``run_contract_tests.sh`` contains both
#: ``[ -n "$CHANGED_FILES" ]`` (line 31) and a genuine ``-n auto`` (line 78).
_SHELL_TEST_BEFORE_RE = re.compile(r"\[\s*$")

#: How deep to follow script indirection. One level is deliberate: following further
#: would mean parsing arbitrary shell control flow to decide a scheduling parameter, and
#: an unbounded traversal is the "general-purpose templating engine" this design refuses
#: to become. One level covers this repository exactly, because its heavy tasks are all
#: ``bash .github/scripts/<name>.sh``.
_MAX_SCRIPT_DEPTH = 1


def _repo_relative(path_text: str) -> str:
    """Make *path_text* repo-relative without mangling a leading dot-directory.

    ``lstrip("./")`` is wrong here: ``lstrip`` strips a *set of characters*, so
    ``".github/scripts/x.sh"`` becomes ``"github/scripts/x.sh"`` — the leading dot is
    removed along with the intended ``./``, the path does not exist, and every task's
    demand silently falls back to 1. That is precisely the inert-scheduler failure this
    function exists to prevent, found by checking the resolved value rather than
    trusting that the code "looked right".
    """
    text = path_text
    if text.startswith("./"):
        text = text[2:]
    return text.lstrip("/")


#: Shell punctuation that terminates a token in a script. ``-n auto; then`` must read as
#: ``auto``, not ``auto;`` — and an unstripped ``;`` made every such flag unresolvable,
#: so a genuinely fanning-out task was reported as single-threaded.
_TOKEN_TRAILING_JUNK = ";&|)<>'\""


def _token_to_demand(token: str) -> int | None:
    """Interpret a worker-count token, or ``None`` when it is not resolvable.

    ``None`` means *unresolved*, which is deliberately not the same as 1: a token like
    ``"$NPROC"`` or ``"$(nproc)"`` means the script may fan out by an unknown amount,
    and silently treating that as single-threaded would re-introduce the exact
    oversubscription this mechanism exists to bound.
    """
    cleaned = token.strip().strip(_TOKEN_TRAILING_JUNK).strip()
    if not cleaned or cleaned.startswith("$"):
        return None
    if cleaned.lower() == "auto":
        return cpu_count()
    if cleaned.isdigit():
        return max(1, int(cleaned))
    return None


def _first_worker_flag(text: str) -> int | None:
    """The first genuine xdist/pytest worker count in *text*.

    Shell ``[ -n "$X" ]`` tests are skipped; the first *resolvable* flag wins.
    """
    for match in _CPU_FLAG_RE.finditer(text):
        # Reject a `[ -n ... ]` test: the character before the flag must not be `[`.
        preceding = text[: match.start()].rstrip()
        if preceding.endswith("["):
            continue
        demand = _token_to_demand(match.group(1))
        if demand is not None:
            return demand
    return None


def cpu_demand_in_script(script_text: str) -> int | None:
    """CPU demand declared by a shell script's contents, or ``None`` if it declares none."""
    return _first_worker_flag(script_text)


def cpu_demand_for(item: Any, *, default: int = 1, _depth: int = 0) -> int:
    """How many CPUs *item* will actually consume concurrently.

    Resolution order, most authoritative first:

    1. an explicit ``cpu_demand`` attribute — an int, or the string ``"auto"``;
    2. a worker-count flag in the item's own command (``-n auto``, ``-n4``);
    3. **a worker-count flag inside the shell script the command invokes.**

    Step 3 is not optional. Every heavy task in this repository is
    ``bash .github/scripts/<name>.sh``, and the ``-n auto`` lives *inside* those
    scripts — ``run_contract_tests.sh:78``, ``run_fast_checks.sh:89``. Scanning only the
    command string returns 1 for all of them, which would make the CPU budget a second
    inert abstraction in precisely the place it was introduced to fix something real:
    the measured shard-6 oversubscription. A scheduler that cannot see the fan-out
    cannot bound it.

    Traversal is one level deep and confined to repo-relative ``.sh`` paths, so it
    cannot be turned into a shell interpreter or a general dependency walk. A flag
    deeper than that, or behind an unresolvable variable, is reported by
    :func:`unresolved_cpu_demand_tasks` rather than silently guessed.
    """
    declared = getattr(item, "cpu_demand", None)
    if declared is not None:
        if isinstance(declared, str):
            return (
                cpu_count()
                if declared.strip().lower() == "auto"
                else max(1, int(declared))
            )
        return max(1, int(declared))

    command = getattr(item, "command", None)
    if command is None and isinstance(item, dict):
        command = item.get("command")
    if not isinstance(command, str):
        return max(1, default)

    direct = _first_worker_flag(command)
    if direct is not None:
        return direct

    if _depth < _MAX_SCRIPT_DEPTH:
        for script_match in _SCRIPT_INDIRECTION_RE.finditer(command):
            rel = _repo_relative(script_match.group(1))
            path = REPO_ROOT / rel
            try:
                if not path.is_file() or path.stat().st_size > 512 * 1024:
                    continue
                script_text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            declared_in_script = cpu_demand_in_script(script_text)
            if declared_in_script is not None:
                return declared_in_script
    return max(1, default)


def _script_has_unresolved_worker_flag(script_text: str) -> bool:
    """True when *script_text* contains a worker-count flag that cannot be resolved.

    Precise on purpose. A script with **no** worker flag at all — like
    ``run_property_tests.sh`` — genuinely is single-threaded, and reporting it would
    bury the real findings in noise. Only a flag that is present and unreadable counts,
    because only that case admits the task and then oversubscribes.
    """
    for match in _CPU_FLAG_RE.finditer(script_text):
        preceding = script_text[: match.start()].rstrip()
        if preceding.endswith("["):
            continue  # a shell `[ -n "$X" ]` string test, not a flag
        if _token_to_demand(match.group(1)) is None:
            return True
    return False


def unresolved_cpu_demand_tasks(items: Sequence[Any]) -> list[str]:
    """Tasks whose CPU demand could only be guessed as 1.

    A task that shells into a script carrying a worker count that cannot be resolved —
    behind a variable, or two levels deep — will be *admitted* as single-threaded and
    will then oversubscribe the box. That is the defect this whole mechanism exists to
    prevent, so it is reported rather than tolerated: the scheduler is honest about what
    it does not know.
    """
    unresolved: list[str] = []
    for item in items:
        if getattr(item, "cpu_demand", None) is not None:
            continue
        command = getattr(item, "command", None)
        if not isinstance(command, str) or not command:
            continue
        if _first_worker_flag(command) is not None:
            continue  # resolved directly from the command
        for script_match in _SCRIPT_INDIRECTION_RE.finditer(command):
            path = REPO_ROOT / _repo_relative(script_match.group(1))
            try:
                if not path.is_file() or path.stat().st_size > 512 * 1024:
                    continue
                script_text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if _script_has_unresolved_worker_flag(script_text):
                unresolved.append(
                    f"{getattr(item, 'task_id', '?')}: {command[:70]} invokes a script "
                    "whose worker count could not be resolved; declare cpu_demand "
                    "explicitly"
                )
            break
    return unresolved


def cpu_count() -> int:
    """Usable CPU count for scheduling, overridable for testing and CI pinning."""
    override = os.environ.get("VERIFY_CPU_BUDGET")
    if override:
        try:
            return max(1, int(override))
        except ValueError:
            pass
    return max(1, os.cpu_count() or 1)


class CpuBudget:
    """Admission control over a fixed number of CPUs.

    Deliberately a *resource* rather than a worker count. A worker count answers "how
    many things at once"; a CPU budget answers "how much CPU at once", which is the
    question that actually has an answer when the work is heterogeneous. Four serial
    tasks and one ``-n auto`` task are both "one worker" and neither is one CPU.

    Non-blocking by design: :meth:`try_acquire` never waits, because the caller is
    mid-iteration over a work list and must be able to skip an item it cannot admit
    and come back to it.
    """

    __slots__ = ("_capacity", "_in_flight", "_peak")

    def __init__(self, capacity: int | None = None) -> None:
        self._capacity = max(1, capacity if capacity is not None else cpu_count())
        self._in_flight = 0
        self._peak = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def in_flight(self) -> int:
        return self._in_flight

    @property
    def peak(self) -> int:
        """Highest concurrent demand observed. Evidence for the estimator."""
        return self._peak

    def try_acquire(self, demand: int) -> bool:
        demand = max(1, demand)
        if self._in_flight + demand > self._capacity:
            return False
        self._in_flight += demand
        self._peak = max(self._peak, self._in_flight)
        return True

    def release(self, demand: int) -> None:
        self._in_flight = max(0, self._in_flight - max(1, demand))

    def would_admit(self, demand: int) -> bool:
        return self._in_flight + max(1, demand) <= self._capacity


def schedule_within_budget(
    items: Sequence[Any],
    budget: CpuBudget,
    *,
    demand_of: Callable[[Any], int] | None = None,
) -> list[list[Any]]:
    """Partition *items* into waves, each fitting inside *budget*.

    Ordered longest-processing-time-first, by *declared duration*, with CPU demand as
    the tiebreak. Duration is the primary key because it is what determines the number
    of waves, and the wave count is what the wall-clock estimate is made of. Sorting by
    demand instead would pack the greedy first-fit worse: it would place every
    single-threaded task first and leave the heavy ones contending at the end.

    Returns the waves in order. Within a wave, items are independent and may run
    concurrently.
    """
    demand_of = demand_of or (lambda item: cpu_demand_for(item))

    def sort_key(item: Any) -> tuple[float, int, str]:
        return (
            -float(getattr(item, "estimated_duration_seconds", 0) or 0),
            -demand_of(item),
            str(getattr(item, "task_id", "")),
        )

    remaining = sorted(items, key=sort_key)
    waves: list[list[Any]] = []
    for item in remaining:
        demand = demand_of(item)
        for wave in waves:
            used = sum(demand_of(w) for w in wave)
            if used + demand <= budget.capacity:
                wave.append(item)
                break
        else:
            waves.append([item])
    return waves


def estimate_wall_seconds(
    items: Sequence[Any], budget: CpuBudget
) -> float:
    """Wall-clock estimate for *items* under *budget*, from their declared durations.

    This is the sum over *waves* of the slowest item in each wave — i.e. the critical
    path — rather than the sum over items. The old matrix figure was the plain sum,
    which describes a serial machine and therefore understated nothing and overstated
    everything depending on how much parallelism the executor actually applied.
    """
    waves = schedule_within_budget(items, budget)
    total = 0.0
    for wave in waves:
        total += max((float(getattr(i, "estimated_duration_seconds", 0) or 0) for i in wave), default=0.0)
    return total


# ---------------------------------------------------------------------------
# Generic concurrent driver
# ---------------------------------------------------------------------------


def execute_tasks_in_parallel(
    items: Sequence[Any],
    worker: Callable[[Any], Any],
    *,
    max_workers: int | None = None,
    on_result: Callable[[Any, Any], None] | None = None,
) -> list[Any]:
    """Run ``worker(item)`` over *items* concurrently and collect **every** result.

    Non-fail-fast by design (M10-R2 §2.3): one task failing must not erase the results
    of independent tasks that still diagnose the run. An unexpected worker exception is
    captured as the item's result rather than propagating, because losing the remaining
    results would be exactly the failure mode this replaces.

    Results are returned in *input* order regardless of completion order, so
    reconciliation never depends on scheduling.
    """
    if not items:
        return []
    workers = max_workers_for(len(items), max_workers)
    if workers == 1 or len(items) == 1:
        out: list[Any] = []
        for item in items:
            try:
                result = worker(item)
            except Exception as exc:  # noqa: BLE001 - collected, not raised
                result = exc
            out.append(result)
            if on_result is not None:
                on_result(item, result)
        return out

    results: list[Any] = [None] * len(items)

    def _run(index: int, item: Any) -> None:
        try:
            outcome = worker(item)
        except Exception as exc:  # noqa: BLE001 - collected, not raised
            outcome = exc
        results[index] = outcome
        if on_result is not None:
            with contextlib.suppress(Exception):
                on_result(item, outcome)

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="verify") as pool:
        futures = [pool.submit(_run, i, item) for i, item in enumerate(items)]
        for future in futures:
            # ``result()`` re-raises only if _run itself raised, which it cannot; the
            # wait is still needed so shutdown is ordered.
            future.result()
    return results


# ---------------------------------------------------------------------------
# Group-oriented façade (preserved API; now built on the promoted worker)
# ---------------------------------------------------------------------------


@dataclass
class TaskResult:
    task_id: str
    command: str
    success: bool
    exit_code: int | None
    duration_seconds: float
    stdout_tail: str = ""
    stderr_tail: str = ""
    timed_out: bool = False
    error: str = ""
    artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TaskGroup:
    """A set of tasks that may run concurrently.

    ``parallel=False`` marks a group whose tasks must run in order — a real dependency,
    or a task that mutates state another task in the same group reads.
    """

    group_id: int
    task_ids: list[str]
    tasks: list[Any] = field(default_factory=list)
    parallel: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "task_ids": list(self.task_ids),
            "tasks": [getattr(t, "task_id", str(t)) for t in self.tasks],
            "parallel": self.parallel,
        }


@dataclass
class ExecutionReport:
    run_id: str
    results: list[TaskResult] = field(default_factory=list)
    total_duration: float = 0.0

    @property
    def all_passed(self) -> bool:
        return all(r.success for r in self.results)

    @property
    def exit_code(self) -> int:
        return 0 if self.all_passed else 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "results": [r.to_dict() for r in self.results],
            "total_duration": self.total_duration,
            "all_passed": self.all_passed,
        }


def _command_of(task: Any) -> str:
    for attr in ("command", "execution_command"):
        value = getattr(task, attr, None)
        if value:
            return str(value)
    if isinstance(task, dict):
        for key in ("command", "execution_command"):
            if task.get(key):
                return str(task[key])
    return ""


def _task_id_of(task: Any) -> str:
    for attr in ("task_id", "id"):
        value = getattr(task, attr, None)
        if value:
            return str(value)
    if isinstance(task, dict) and task.get("task_id"):
        return str(task["task_id"])
    return f"task-{id(task)}"


def _depends_on(task: Any) -> tuple[str, ...]:
    """Read the real dependency field.

    M10-R2 B4: the original read ``dependency_on``/``dependencies``, which the plan model
    never sets. ``depends_on`` is the field ``_add_dependency_edges`` populates, and
    ``depends_on_task`` is accepted for callers that spell it that way.
    """
    for attr in ("depends_on", "dependencies", "depends_on_task"):
        value = getattr(task, attr, None)
        if value:
            return tuple(str(v) for v in value)
    if isinstance(task, dict):
        for key in ("depends_on", "dependencies", "depends_on_task"):
            if task.get(key):
                return tuple(str(v) for v in task[key])
    return ()


def plan_parallel_groups(
    tasks: Sequence[Any],
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> list[TaskGroup]:
    """Layer tasks into groups; tasks within a group are independent.

    Deterministic: input order is preserved, and a task runs only in a later group
    than everything it depends on.
    """
    placed: list[str] = []
    groups: list[TaskGroup] = []
    todo = list(tasks)
    guard = 0
    while todo and guard <= len(tasks) + 1:
        guard += 1
        ready = [t for t in todo if all(dep in placed for dep in _depends_on(t))]
        if not ready:
            # A dependency cycle: run what is left in one sequential group rather than
            # dropping obligations. Ordering inside it stays input order.
            groups.append(
                TaskGroup(
                    group_id=len(groups),
                    task_ids=[_task_id_of(t) for t in todo],
                    tasks=list(todo),
                    parallel=False,
                )
            )
            break
        parallel = len(ready) > 1 and max_workers > 1
        groups.append(
            TaskGroup(
                group_id=len(groups),
                task_ids=[_task_id_of(t) for t in ready],
                tasks=list(ready),
                parallel=parallel,
            )
        )
        placed.extend(_task_id_of(t) for t in ready)
        todo = [t for t in todo if _task_id_of(t) not in placed]
    return groups


class ParallelExecutor:
    """Group-oriented execution façade over the promoted streaming worker.

    Retained for the existing callers/tests. The canonical verification paths do not
    use this class — they drive :func:`execute_tasks_in_parallel` directly with their
    own record builder, because they need ``TaskExecutionRecord`` vocabulary rather
    than ``TaskResult``. What this class still owns is dependency-aware *group*
    planning, which the orchestrator replaces with the plan's own ``depends_on``.
    """

    def __init__(
        self,
        max_workers: int | None = DEFAULT_MAX_WORKERS,
        evidence_root: Path | None = None,
        timeout_seconds: int = 900,
    ) -> None:
        self.max_workers = max_workers
        self.evidence_root = evidence_root
        self.timeout_seconds = timeout_seconds

    def plan_parallel_groups(self, tasks: Sequence[Any]) -> list[TaskGroup]:
        return plan_parallel_groups(tasks, self.max_workers)

    def _execute_one(self, task: Any, plan_id: str) -> TaskResult:
        from runtime.foundation.verification.env import child_process_env

        command = _command_of(task)
        task_id = _task_id_of(task)
        root = (
            Path(self.evidence_root)
            if self.evidence_root
            else REPO_ROOT / "runtime" / "generated"
        )
        base = root / "parallel-logs" / plan_id
        result = run_streaming_command(
            command,
            stdout_path=base / f"{task_id}-stdout.log",
            stderr_path=base / f"{task_id}-stderr.log",
            timeout_seconds=self.timeout_seconds,
            env=child_process_env(),
        )
        return TaskResult(
            task_id=task_id,
            command=command,
            success=result.exit_code == 0
            and not result.timed_out
            and not result.infra_error,
            exit_code=result.exit_code,
            duration_seconds=result.duration_seconds,
            stdout_tail=result.stdout.splitlines()[-20:],
            stderr_tail=result.stderr.splitlines()[-20:],
            timed_out=result.timed_out,
            error=result.infra_error or "",
            artifacts=[str(result.stdout_path), str(result.stderr_path)],
        )

    def execute_parallel(
        self,
        groups: Sequence[TaskGroup],
        plan_id: str = "parallel",
    ) -> ExecutionReport:
        t0 = time.monotonic()
        results: list[TaskResult] = []
        for group in groups:
            if group.parallel:
                results.extend(
                    execute_tasks_in_parallel(
                        list(group.tasks),
                        lambda t: self._execute_one(t, plan_id),
                        max_workers=self.max_workers,
                    )
                )
            else:
                results.extend(self._execute_one(t, plan_id) for t in group.tasks)
        return ExecutionReport(
            run_id=plan_id,
            results=results,
            total_duration=time.monotonic() - t0,
        )
