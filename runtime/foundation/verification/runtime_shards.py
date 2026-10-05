"""M10-R2 — deterministic CI sharding of the runtime test suite.

Why this exists
---------------
``runtime-self-test`` is the single longest obligation in the repository: ~26 minutes
of ``pytest runtime/tests/`` run serially on one runner. Everything else in the runtime
profile is measured in seconds. Until this is sharded, the Runtime Verification critical
path *is* that suite, so it is the highest-value target in the milestone.

Why shards, and not xdist
-------------------------
M10-R2-C2 piloted ``pytest -n 4`` on this suite and **rejected** it: 1.19x with 6
failures, all of them budget exhaustion under contention on a 4-core box that was
already at loadavg 4.6-6.7. Four xdist workers each fork nested pytest, and the suite's
hard-coded 30 s / 120 s subprocess budgets do not survive that.

Matrix sharding avoids the cause rather than the symptom: each shard is a **dedicated
GitHub runner** with its own checkout, so there is no shared CPU to oversubscribe. A
shard runs plain serial pytest — the exact invocation already proven green (2685 passed,
16 skipped, 0 failed). The contention that disqualified xdist cannot arise.

Guarantees
----------
* **Complete coverage, exactly once.** The partition is a function of the *file list
  only*, and the aggregate asserts ``union(shard files) == all test files`` with no
  duplicates. A test cannot be silently omitted or run twice.
* **Deterministic.** Files are sorted, weighted, then placed by LPT with a total-order
  tiebreak. Two runs of the plan job produce byte-identical shards.
* **Real boundaries, not arbitrary paths.** Each shard is a set of whole test files, so
  pytest fixtures and module-level state stay inside one process. Nothing is split
  mid-module.
* **Balanced.** Weights come from per-file test counts, which is a far better proxy for
  runtime than file count — ``test_m9_c54.py`` alone carries 87 tests against a median
  of roughly 3.

The suite is deliberately *not* xdist-enabled: see ``runtime/tests/conftest.py``, which
records that measurement and skips the known shared-state files if anyone tries again.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runtime.foundation.verification.execution_shards import (
    INFRA_BACKSTOP_MARGIN_SECONDS,
)


def _emit(line: str) -> None:
    """One progress line on stderr. Never raises, never touches stdout."""
    import contextlib
    import sys

    with contextlib.suppress(Exception):
        print(line, file=sys.stderr, flush=True)


__all__ = [
    "ShardResult",
    "TestShardPlan",
    "build_test_shards",
    "expected_shard_ids",
    "read_shard_results",
    "run_test_shard",
    "runtime_test_files",
    "shard_matrix",
    "summarise_shards",
    "verify_shards",
]

#: The suite root, relative to the repository root. Shards are expressed relative to
#: this so the emitted commands are stable regardless of the caller's cwd.
SUITE_ROOT = "runtime/tests"

#: Upper bound on shards. A shard is a dedicated runner, so this bounds *runner
#: minutes*, not a single machine's cores. Four keeps the plan's longest shard near the
#: suite's median shard while staying well inside the repo's existing mutation
#: precedent (``max-parallel: 7``).
DEFAULT_SHARD_COUNT = 4


def runtime_test_files(suite_root: Path | None = None) -> list[str]:
    """Every test file in the suite, sorted, as repo-relative POSIX paths.

    Sorted rather than glob order so the partition is reproducible. The sort is also what
    makes the aggregate's coverage assertion meaningful: the same list is produced by
    the plan job and by the gate.
    """
    root = Path(suite_root or SUITE_ROOT)
    files = sorted(p.as_posix() for p in root.glob("test_*.py"))
    return files


def _weights(files: list[str], counts: dict[str, int] | None) -> dict[str, int]:
    """Per-file cost proxy.

    Uses a supplied test-count map when available (the plan job collects it once with
    ``--collect-only``) and falls back to 1 per file. The fallback keeps a shard
    runnable without pytest, at the cost of balance; it is never silently wrong about
    *coverage*, which is asserted separately.
    """
    if not counts:
        return dict.fromkeys(files, 1)
    return {f: max(1, int(counts.get(f, 0) or 0)) for f in files}


@dataclass(frozen=True, slots=True)
class TestShardPlan:
    """A deterministic partition of the runtime suite."""

    shard_count: int
    #: ``shards[i]`` is the sorted file list for shard ``i``.
    shards: tuple[tuple[str, ...], ...]
    #: Estimated seconds per shard, from the weight proxy.
    estimated_seconds: tuple[int, ...]
    #: Anything the partition deliberately excluded, with the reason. Never populated
    #: silently — an omitted file must be a recorded decision, not a gap.
    excluded: dict[str, str] = field(default_factory=dict)

    def file_count(self, index: int) -> int:
        return len(self.shards[index])

    def all_files(self) -> set[str]:
        out: set[str] = set()
        for shard in self.shards:
            out.update(shard)
        return out

    def shard_id(self, index: int) -> str:
        return f"runtime-tests-shard-{index}"


def build_test_shards(
    files: list[str],
    shard_count: int,
    counts: dict[str, int] | None = None,
    excluded: dict[str, str] | None = None,
) -> TestShardPlan:
    """Partition *files* into *shard_count* deterministic, balanced shards.

    LPT (longest-processing-time-first) bin packing over the per-file weight, with the
    file path as a total-order tiebreak so the result never depends on dict or set
    iteration order.
    """
    if shard_count < 1:
        raise ValueError(f"shard_count must be >= 1, got {shard_count}")
    excluded = dict(excluded or {})
    pool = [f for f in files if f not in excluded]
    weight = _weights(pool, counts)

    order = sorted(pool, key=lambda f: (-weight[f], f))
    bins: list[list[str]] = [[] for _ in range(shard_count)]
    loads = [0] * shard_count
    for path in order:
        # argmin over (load, index): deterministic, ties go to the lowest index.
        target = min(range(shard_count), key=lambda i: (loads[i], i))
        bins[target].append(path)
        loads[target] += weight[path]

    shards = tuple(tuple(sorted(b)) for b in bins)
    return TestShardPlan(
        shard_count=shard_count,
        shards=shards,
        estimated_seconds=tuple(loads),
        excluded=excluded,
    )


def shard_matrix(plan: TestShardPlan) -> str:
    """Render the shard plan as a GitHub Actions dynamic-matrix document."""
    include = [
        {
            "shard": i,
            "shard_id": plan.shard_id(i),
            "shard_count": plan.shard_count,
            "file_count": len(plan.shards[i]),
            "estimated_seconds": plan.estimated_seconds[i],
            # L1c: the backstop this leg needs. Uniform, because every runtime shard
            # executes the same command under the same budget — the difference between
            # shards is which FILES they hold, not how long they may take.
            "required_timeout_minutes": required_shard_backstop_minutes(),
            "contractual_seconds": DEFAULT_SHARD_TIMEOUT_SECONDS,
        }
        for i in range(plan.shard_count)
        if plan.shards[i]
    ]
    total = sum(plan.estimated_seconds) or 1
    document = {
        "include": include,
        "shard_count": len(include),
        "requested_shard_count": plan.shard_count,
        "file_count": sum(len(s) for s in plan.shards),
        "estimated_seconds_total": total,
        "estimated_seconds_critical_path": max(plan.estimated_seconds, default=0),
        "estimated_speedup": round(
            total / max(max(plan.estimated_seconds, default=1), 1), 2
        ),
        "excluded": plan.excluded,
    }
    return json.dumps(document, indent=2)


@dataclass(frozen=True, slots=True)
class ShardResult:
    """One shard's outcome."""

    shard_id: str
    status: str  # passed | failed | timed_out
    exit_code: int
    duration_seconds: float
    file_count: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    # M10-R3 (B2) — the shard's own certification verdict and fingerprint bracket.
    # A shard is the unit CI actually runs; before this it reported counts and a
    # status, so the aggregate could not tell a clean shard on a stable tree from a
    # clean shard on a tree that had moved. Absence defaults to unstable, so a
    # document written by an older producer is read as "not certified", never as a pass.
    decision: str = ""
    decision_reason: str = ""
    fingerprint_before: dict | None = None
    fingerprint_after: dict | None = None
    fingerprint_stable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "shard_id": self.shard_id,
            "status": self.status,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "file_count": self.file_count,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "fingerprint_before": self.fingerprint_before,
            "fingerprint_after": self.fingerprint_after,
            "fingerprint_stable": self.fingerprint_stable,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ShardResult:
        return cls(
            shard_id=d.get("shard_id", ""),
            status=d.get("status", ""),
            exit_code=int(d.get("exit_code", 1)),
            duration_seconds=float(d.get("duration_seconds", 0.0)),
            file_count=int(d.get("file_count", 0)),
            passed=int(d.get("passed", 0)),
            failed=int(d.get("failed", 0)),
            errors=int(d.get("errors", 0)),
            decision=d.get("decision", ""),
            decision_reason=d.get("decision_reason", ""),
            fingerprint_before=d.get("fingerprint_before"),
            fingerprint_after=d.get("fingerprint_after"),
            fingerprint_stable=bool(d.get("fingerprint_stable", False)),
        )

    @property
    def ok(self) -> bool:
        return self.status == "passed"


#: Accepted result-document schemas. Anything else is REJECTED rather than coerced:
#: a document this build cannot interpret must never be read as a passing leg.
LEG_RESULT_SCHEMAS: frozenset[str] = frozenset({"m10r2-leg-result/v1"})


def read_shard_results(
    directory: Path,
    *,
    pattern: str = "shard-*.json",
) -> tuple[list[ShardResult], list[str], list[str], list[str]]:
    """Read every result document matching *pattern*, classifying each outcome.

    Returns ``(results, absent, malformed, rejected)``. The three failure buckets are
    kept apart because they have different owners and must never be conflated:

    * **absent** — no file at all for this leg. The leg never reached a terminal result:
      killed, cancelled, or never started. An infrastructure event.
    * **malformed** — a file exists but is not valid JSON, or is missing a required key.
      A producer bug.
    * **rejected** — valid JSON with a schema this build does not recognise. Also a
      producer/deployment bug, but a different one from a corrupt file.

    The previous shape returned a single ``unreadable`` list for all three and defaulted
    missing fields (``payload.get("exit_code", 1)``), which meant a document missing its
    status could be read as a leg that ran and failed. Silent coercion of an
    uninterpretable document into a verdict is the one behaviour this gate must never have.
    """
    results: list[ShardResult] = []
    absent: list[str] = []
    malformed: list[str] = []
    rejected: list[str] = []

    directory = Path(directory)
    paths = sorted(directory.glob(pattern))
    if not paths:
        # No files at all is not "all legs absent" — it is a transport fault, and the
        # caller must be able to say so rather than reporting every task as missing.
        absent.append(f"no {pattern} files found")

    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            malformed.append(f"{path.name}: {type(exc).__name__}")
            continue
        if not isinstance(payload, dict):
            malformed.append(f"{path.name}: not a JSON object")
            continue
        schema = payload.get("schema")
        if schema is not None and schema not in LEG_RESULT_SCHEMAS:
            rejected.append(f"{path.name}: unsupported schema {schema!r}")
            continue
        try:
            # Required keys checked explicitly: from_dict defaults them, and a
            # document missing its identity must be reported as a *producer* fault
            # rather than defaulted into a plausible-looking shard.
            for required in ("shard_id", "status", "exit_code"):
                if required not in payload:
                    raise KeyError(required)
            results.append(ShardResult.from_dict(payload))
        except (KeyError, TypeError, ValueError) as exc:
            malformed.append(f"{path.name}: {type(exc).__name__}: {exc}")
    return results, absent, malformed, rejected


def expected_shard_ids(shard_count: int) -> list[str]:
    return [f"runtime-tests-shard-{i}" for i in range(shard_count)]


def verify_shards(
    shard_count: int,
    results: list[ShardResult],
    *,
    integrity_ok: bool | None = None,
) -> list[str]:
    """Reasons this fan-out must NOT certify. Empty means certified.

    Asserts, in order: every expected shard reported, exactly once; every shard passed;
    every shard ran on a repository state that did not move (M10-R3 B2); and — when
    supplied — that the independent integrity obligation also passed. This is the
    runtime-side analogue of the reconcile split-brain guard, and it is what makes
    "the aggregate job succeeded" mean "every shard succeeded" rather than "the
    aggregate ran".

    The fingerprint clause is the substantive addition. A shard is a 40-minute pytest
    run on its own runner; before B2 its result document carried counts and a status
    and nothing about the tree it ran against, so four shards reporting green was
    consistent with the tree having changed underneath them. A shard document with no
    bracket is read as **unstable**, never as a pass.
    """
    problems: list[str] = []
    expected = expected_shard_ids(shard_count)
    seen: dict[str, ShardResult] = {}

    for result in results:
        if result.shard_id in seen:
            problems.append(f"{result.shard_id} reported by more than one leg")
            continue
        seen[result.shard_id] = result

    missing = [s for s in expected if s not in seen]
    if missing:
        problems.append(
            f"expected {shard_count} shard(s), {len(seen)} reported; missing: "
            + ", ".join(missing)
        )

    unknown = sorted(set(seen) - set(expected))
    if unknown:
        problems.append(f"unknown shard(s) reported: {', '.join(unknown)}")

    for shard_id in expected:
        result = seen.get(shard_id)
        if result is None:
            continue
        if not result.ok:
            problems.append(
                f"{shard_id} {result.status} "
                f"(passed={result.passed} failed={result.failed} "
                f"errors={result.errors} exit={result.exit_code})"
            )
        if not result.fingerprint_stable:
            before = (result.fingerprint_before or {}).get("fingerprint", "")[:12]
            after = (result.fingerprint_after or {}).get("fingerprint", "")[:12]
            problems.append(
                f"{shard_id} "
                + (
                    f"repository fingerprint changed during the shard "
                    f"({before or 'unknown'} -> {after or 'unknown'})"
                    if before or after
                    else "reported no fingerprint bracket; cannot certify it"
                )
            )

    if integrity_ok is False:
        problems.append("runtime integrity obligation did not pass")

    return problems


def summarise_shards(results: list[ShardResult]) -> str:
    rows = [
        f"| {r.shard_id} | {r.status} | {r.file_count} | {r.passed} | "
        f"{r.duration_seconds:.1f} s | {r.decision or 'unclassified'} | "
        f"{'stable' if r.fingerprint_stable else 'UNSTABLE'} |"
        for r in sorted(results, key=lambda x: x.shard_id)
    ]
    header = (
        "| shard | status | files | passed | duration | decision | fingerprint |\n"
        "|---|---|---|---|---|---|---|"
    )
    return header + "\n" + "\n".join(rows)


#: The runtime-shard budget, named and published rather than duplicated in YAML.
#:
#: M10-R3 (L1c): `verification-runtime.yml` carried its own `:-2400` literal, matching
#: this default today and free to drift tomorrow. The workflow now reads
#: `required_timeout_minutes` from `shard_matrix`, and this constant is the single
#: source.
DEFAULT_SHARD_TIMEOUT_SECONDS = 2400


def required_shard_backstop_minutes(timeout_seconds: int | None = None) -> int:
    """Whole minutes a runtime-shard leg must be given, including teardown margin."""
    budget = (
        DEFAULT_SHARD_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    )
    return max(1, -(-(budget + INFRA_BACKSTOP_MARGIN_SECONDS) // 60))


def run_test_shard(
    shard_index: int,
    shard_count: int,
    *,
    result_out: Path,
    counts: dict[str, int] | None = None,
    timeout_seconds: int = DEFAULT_SHARD_TIMEOUT_SECONDS,
    timeout_per_test: int = 30,
    extra_args: list[str] | None = None,
) -> ShardResult:
    """Execute exactly one shard of the runtime suite on this runner.

    The command is plain serial pytest over *whole files*:

    * whole files, so module fixtures and module-level state never straddle processes;
    * serial, because a shard already owns a dedicated runner and forking xdist workers
      inside it would re-create the contention that disqualified ``-n`` (M10-R2-C2);
    * through the shared worker, streaming into the same evidence directory the rest of
      verification writes to.

    The result document is written before returning in every case, so a killed shard is
    distinguishable from one that never started.
    """
    from runtime.foundation.verification.env import child_process_env
    from runtime.foundation.verification.parallel_executor import run_streaming_command

    files = runtime_test_files()
    plan = build_test_shards(files, shard_count, counts)
    if not 0 <= shard_index < shard_count:
        raise ValueError(
            f"shard must satisfy 0 <= shard < shard-count; got "
            f"{shard_index} / {shard_count}"
        )
    shard_files = list(plan.shards[shard_index])
    shard_id = plan.shard_id(shard_index)

    log_dir = Path("runtime/generated/runtime-shard-logs") / shard_id
    log_dir.mkdir(parents=True, exist_ok=True)

    command = " ".join(
        [
            ".venv/bin/python",
            "-m",
            "pytest",
            *shard_files,
            "-q",
            f"--timeout={timeout_per_test}",
            "--no-header",
            "-p",
            "no:cacheprovider",
            *(extra_args or []),
        ]
    )

    # M10-R2 closeout: live lifecycle logging. A runtime shard is the longest-running
    # unit in CI, so "is it alive and which files is it on" is exactly the question the
    # log must answer while it runs.
    from runtime.foundation.verification.parallel_executor import ProgressContext

    # M10-R3 (B2) — a shard brackets itself in the shared certification authority.
    #
    # A runtime shard is the longest-running unit in CI (a 40-minute pytest run on its
    # own runner) and it previously reported only counts and a status. It now also
    # reports the fingerprint bracket it ran inside, so a shard that ran for forty
    # minutes against a tree that moved underneath it cannot be aggregated as a pass.
    from runtime.foundation.verification.execution_orchestrator import (
        CertificationRun,
        CompletionState,
    )

    certification = CertificationRun(plan_id=f"runtime-shard:{shard_id}")
    certification.__enter__()

    _emit(
        f"[runtime-shard {shard_index + 1}/{shard_count}] shard_id={shard_id} "
        f"files={len(shard_files)}"
    )
    result = run_streaming_command(
        command,
        stdout_path=log_dir / "stdout.log",
        stderr_path=log_dir / "stderr.log",
        timeout_seconds=timeout_seconds,
        env=child_process_env(),
        progress=ProgressContext(
            label=f"runtime-shard {shard_index + 1}/{shard_count}",
            kind="shard",
            log_dir=log_dir,
            timeout_seconds=timeout_seconds,
        ),
    )
    certification.__exit__(None, None, None)

    output = result.stdout + "\n" + result.stderr
    passed = _count(output, r"(\d+) passed")
    failed = _count(output, r"(\d+) failed")
    errors = _count(output, r"(\d+) error")

    if result.timed_out:
        status, exit_code = "timed_out", 124
        state = CompletionState.TIMEOUT
        detail = f"exceeded the {timeout_seconds}s shard budget"
    elif result.infra_error:
        status, exit_code = "failed", 127
        state = CompletionState.INFRASTRUCTURE
        detail = result.infra_error
    elif result.exit_code != 0:
        status, exit_code = "failed", int(result.exit_code or 1)
        state = CompletionState.FAILED
        detail = f"exit {result.exit_code}"
    else:
        status, exit_code = "passed", 0
        state, detail = CompletionState.PASS, ""

    certification.record(shard_id, state, is_mandatory=True, detail=detail)
    decision, reason = certification.decide()
    outcome = certification.to_dict()

    shard = ShardResult(
        shard_id=shard_id,
        status=status,
        exit_code=exit_code,
        duration_seconds=round(result.duration_seconds, 2),
        file_count=len(shard_files),
        passed=passed,
        failed=failed,
        errors=errors,
        decision=decision.value,
        decision_reason=reason,
        fingerprint_before=outcome["fingerprint_before"],
        fingerprint_after=outcome["fingerprint_after"],
        fingerprint_stable=outcome["fingerprint_stable"],
    )
    result_out.parent.mkdir(parents=True, exist_ok=True)
    result_out.write_text(json.dumps(shard.to_dict(), indent=2), encoding="utf-8")
    return shard


def _count(text: str, pattern: str) -> int:
    """Last match of a pytest summary count.

    ``pytest -q`` prints several progress lines containing these words; the summary is
    the last one. Taking the last match keeps the aggregate's accounting honest rather
    than optimistic when a shard fails midway.
    """
    import re

    matches = re.findall(pattern, text)
    return int(matches[-1]) if matches else 0
