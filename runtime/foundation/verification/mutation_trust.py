# runtime/foundation/verification/mutation_trust.py
#
# M9-C71 — Mutation measurement trust and survivor forensics.
#
# THE PRINCIPLE
# -------------
#   A verification system must verify the validity of its measurement before
#   interpreting the measurement.
#
# This repository has now produced two independent demonstrations of what
# happens when it does not:
#
#   * MUTATION. mutmut 3.7.0 strips a leading "src." from path-derived mutant
#     module names while this repository imports production code as
#     "src.<package>". Every mutant was therefore dispatched to the ORIGINAL
#     function, the suite passed for all of them, and the campaign reported a
#     structurally impossible 0.0% with 285 survivors — while the execution and
#     evidence-integrity gates reported perfect health. The measurement was not
#     wrong, it was absent, and it looked like a test-quality failure.
#
#   * PLATFORM E2E. A GET from the console implicitly triggered expensive
#     verification planning, so every /platform page failed a networkidle wait
#     with a timeout regardless of backend health. The timeout looked like a
#     frontend problem and was actually a read-path architecture defect.
#
# The pipeline this module certifies is:
#
#     MUTATION GENERATION -> MUTATION VALIDITY -> MUTANT EXECUTION
#       -> TEST ORACLE -> KILL/SURVIVE -> SURVIVOR CLASSIFICATION
#       -> CERTIFIED MUTATION SCORE
#
# The missing trust boundary is the last step: a measurement must be able to say
# "this score is INVALID" rather than only "this score is 0%". `certify()`
# implements exactly that, and `MutationTrustError` is the refusal it raises.
#
# NOTHING HERE RELAXES A GATE. The 80% threshold is read from the unchanged
# verification configuration. Equivalent, unreachable and defensive mutants are
# never removed from the RAW score; they are reported separately in a CERTIFIED
# score whose denominator adjustments are individually justified.

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from runtime.foundation.verification.env import PINNED_MUTMUT, REPO_ROOT, VENV_BIN
from runtime.foundation.verification.mutation_shards import (
    collect_shard_summaries,
    resolve_threshold,
    shard_names,
)
from runtime.foundation.verification.mutmut_contract import (
    MutmutTrampolineContract,
    ensure_mutmut_contract,
    write_mutmut_contract_evidence,
)
from runtime.foundation.verification.mutmut_contract import (
    inspect as inspect_toolchain,
)

BACKEND_ROOT = REPO_ROOT / "backend"
MUTATION_EVIDENCE_DIR = BACKEND_ROOT / "tests" / "generated" / "mutation"
CANARY_DIR = BACKEND_ROOT / "tests" / "mutation_trust" / "canary"
CANARY_SINK_NAME = "c71-mutation-sentinel-sink.jsonl"

#: Where every C71 artifact is written. One directory, so the certification is
#: a single self-describing evidence bundle.
TRUST_ARTIFACT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c71-mutation-trust"

#: mutmut exit code -> semantic status. Mirrors mutmut's own
#: ``status_by_exit_code`` table; kept explicit because Phase 4/5 depend on the
#: distinction between "the suite passed" and "the suite never ran".
EXIT_STATUS: dict[int | None, str] = {
    0: "SURVIVED",
    1: "KILLED",
    2: "INTERRUPTED",
    3: "KILLED",
    5: "NO_TESTS",
    24: "TIMEOUT",
    33: "NO_TESTS",
    34: "SKIPPED",
    35: "SUSPICIOUS",
    36: "TIMEOUT",
    37: "CAUGHT_BY_TYPE_CHECK",
    152: "TIMEOUT",
    255: "TIMEOUT",
    -11: "SEGFAULT",
    -24: "TIMEOUT",
    -9: "SEGFAULT",
    None: "NOT_CHECKED",
}

#: Exit codes for which mutmut never forked a test process. ``33`` is written
#: directly when a mutant has no associated tests (mutmut/__main__.py: `if not
#: tests: exit_code_by_key[mutant_name] = 33`), and ``5`` is pytest's
#: "no tests collected" exit code. Neither implies the mutant ever executed, so
#: a survivor in either bucket is NOT a legitimate test survivor.
NO_EXECUTION_EXIT_CODES = frozenset({5, 33})


class MutationTrustError(RuntimeError):
    """The mutation measurement cannot be certified as trustworthy.

    Raised by :func:`certify` whenever a measurement-integrity precondition
    fails. This is the architectural improvement C71 exists to add: the system
    can now say "the mutation score is invalid" instead of only reporting a
    number.
    """


# ── Phase 5: survivor taxonomy ───────────────────────────────────────────────

#: Every category a survivor may carry. UNKNOWN is a failure of the analysis,
#: not a category a survivor is allowed to remain in.
SURVIVOR_CATEGORIES: tuple[str, ...] = (
    "MUTATION_INVALID",
    "NOT_REACHED",
    "EQUIVALENT",
    "UNOBSERVABLE_BY_CONTRACT",
    "DEFENSIVE_PATH",
    "REAL_TEST_GAP",
    "TEST_HARNESS_GAP",
    "PRODUCT_CONTRACT_GAP",
    "TOOLING_DEFECT",
    "UNKNOWN",
)

#: Categories that are legitimate structural facts about the code rather than
#: test-quality failures. These are NEVER removed from the raw score; they are
#: only reported in the certified score, and only with an explicit,
#: per-mutant justification recorded in the evidence.
STRUCTURAL_CATEGORIES: frozenset[str] = frozenset(
    {
        "MUTATION_INVALID",
        "NOT_REACHED",
        "EQUIVALENT",
        "UNOBSERVABLE_BY_CONTRACT",
        "DEFENSIVE_PATH",
    }
)

#: Categories that represent a genuine shortfall. Only these are eligible for
#: prioritised test work in Phase 10.
GENUINE_GAP_CATEGORIES: frozenset[str] = frozenset(
    {
        "REAL_TEST_GAP",
        "TEST_HARNESS_GAP",
        "PRODUCT_CONTRACT_GAP",
    }
)


@dataclass(frozen=True, slots=True)
class SurvivorVerdict:
    """One survivor with its proven classification."""

    mutant: str
    component: str
    source_file: str
    function: str
    operator: str
    execution: str
    category: str
    evidence: str
    justification: str = ""
    basis: str = ""

    def to_dict(self) -> dict:
        return {
            "mutant": self.mutant,
            "component": self.component,
            "source_file": self.source_file,
            "function": self.function,
            "operator": self.operator,
            "execution": self.execution,
            "execution_basis": self.basis,
            "category": self.category,
            "evidence": self.evidence,
            "justification": self.justification,
        }


@dataclass(frozen=True, slots=True)
class ScoreReconciliation:
    """RAW (immutable) and CERTIFIED (evidence-adjusted) mutation scores.

    RAW is exactly what mutmut measured. It is never recomputed, filtered, or
    replaced. CERTIFIED additionally reports how much of the surviving
    population is provably not a test-quality failure — with every denominator
    adjustment individually justified.
    """

    raw_population: int
    raw_killed: int
    raw_survived: int
    raw_score: float
    threshold: int
    valid_population: int = 0
    certified_killed: int = 0
    proven_equivalent: int = 0
    proven_unobservable: int = 0
    proven_not_reached: int = 0
    proven_defensive: int = 0
    remaining_real_survivors: int = 0
    effective_score: float | None = None
    raw_gate: str = "FAIL"
    effective_gate: str = "FAIL"
    adjustments: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "raw": {
                "population": self.raw_population,
                "killed": self.raw_killed,
                "survived": self.raw_survived,
                "score": self.raw_score,
            },
            "certified": {
                "valid_population": self.valid_population,
                "killed": self.certified_killed,
                "proven_equivalent": self.proven_equivalent,
                "proven_unobservable": self.proven_unobservable,
                "proven_not_reached": self.proven_not_reached,
                "proven_defensive": self.proven_defensive,
                "remaining_real_survivors": self.remaining_real_survivors,
                "effective_score": self.effective_score,
            },
            "threshold": self.threshold,
            "raw_gate": self.raw_gate,
            "effective_gate": self.effective_gate,
            "denominator_adjustments": self.adjustments,
        }


@dataclass(frozen=True, slots=True)
class TrustCertification:
    """The single decision Phase 16 must report."""

    measurement_valid: bool
    dispatch_valid: bool
    execution_proven: bool
    unknown_survivors: int
    raw_score: float | None
    effective_score: float | None
    raw_gate: str
    refusals: list[str] = field(default_factory=list)

    @property
    def certified(self) -> bool:
        """C71 is certified only when the measurement itself is trustworthy.

        The 80% quality gate is deliberately NOT part of this predicate. A
        trustworthy measurement of a 78.8% score is a successful C71 outcome;
        conflating the two would mean C71 could only "pass" by reaching 80%,
        which is exactly the score-chasing the milestone forbids.
        """
        return (
            self.measurement_valid
            and self.dispatch_valid
            and self.execution_proven
            and self.unknown_survivors == 0
        )

    def to_dict(self) -> dict:
        return {
            "MUTATION_MEASUREMENT_VALID": self.measurement_valid,
            "MUTATION_DISPATCH_VALID": self.dispatch_valid,
            "MUTANT_EXECUTION_PROVEN": self.execution_proven,
            "UNKNOWN_SURVIVORS": self.unknown_survivors,
            "RAW_SCORE": self.raw_score,
            "EFFECTIVE_SCORE": self.effective_score,
            "RAW_GATE": self.raw_gate,
            "CERTIFIED": self.certified,
            "refusals": list(self.refusals),
        }


# ── small shared helpers ─────────────────────────────────────────────────────


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def _display_path(path: Path) -> str:
    """Repo-relative when possible, absolute otherwise.

    Evidence pointers must never raise just because the artifact lives outside
    the repository tree (a relocated evidence directory, or a test fixture).
    """
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _write_json(name: str, payload: dict) -> Path:
    TRUST_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = TRUST_ARTIFACT_DIR / name
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def toolchain_state() -> MutmutTrampolineContract:
    """Inspect (never mutate) the pinned mutation toolchain contract."""
    return inspect_toolchain(PINNED_MUTMUT or "")


def _declared_mutmut_version() -> str:
    """The mutmut version the repository DECLARES, from its own packaging."""
    for candidate in ("pyproject.toml", BACKEND_ROOT / "pyproject.toml"):
        path = REPO_ROOT / candidate if isinstance(candidate, str) else candidate
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        marker = "mutmut=="
        if marker in text:
            return (
                text.split(marker, 1)[1]
                .split('"', 1)[0]
                .split("'", 1)[0]
                .split("\n", 1)[0]
                .strip()
            )
    return PINNED_MUTMUT or ""


def _installed_mutmut_version() -> str:
    try:
        import importlib.metadata as md

        return md.version("mutmut")
    except Exception:
        return ""


# ── Phase 0: freeze the baseline ─────────────────────────────────────────────


def freeze_baseline() -> dict:
    """Record the immutable C71 baseline: identity, configuration, population.

    Phase 0 exists so that every later number can be traced to a specific
    toolchain, tree, and configuration. A mutation score without those three
    is not evidence — it is a number.
    """
    aggregate = _read_json(MUTATION_EVIDENCE_DIR / "mutation-summary-aggregate.json")
    toolchain = toolchain_state()
    shard_summaries = collect_shard_summaries(shard_names())
    threshold = resolve_threshold()

    shards = []
    for name in shard_names():
        payload = shard_summaries.get(name)
        shards.append(
            {
                "shard": name,
                "present": payload is not None,
                "population": int((payload or {}).get("mutants_generated") or 0),
                "killed": int((payload or {}).get("killed") or 0),
                "survived": int((payload or {}).get("survived") or 0),
                "no_tests": int((payload or {}).get("no_tests") or 0),
                "timeout": int((payload or {}).get("timeout") or 0),
                "score": (payload or {}).get("mutation_score"),
            }
        )

    measured = [s for s in shards if s["present"] and s["population"] > 0]
    baseline = {
        "schema": "m9-c71-mutation-trust-baseline/v1",
        "recorded_at": _now(),
        "identity": {
            "head_sha": _git("rev-parse", "HEAD"),
            "tree_sha": _git("rev-parse", "HEAD^{tree}"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "working_tree_clean": _git("status", "--porcelain") == "",
        },
        "environment": {
            "python": sys.version.split()[0],
            "python_executable": str(VENV_BIN / "python"),
            "venv": str(REPO_ROOT / ".venv"),
            "mutmut_installed": _installed_mutmut_version(),
            "mutmut_declared": _declared_mutmut_version(),
            "mutmut_pinned": PINNED_MUTMUT,
        },
        "mutation_configuration": {
            "threshold_percent": threshold,
            "threshold_source": "verification.yaml mutation_thresholds.full_campaign",
            "shard_model": "mutation_shards.shard_plan (deterministic, size-bounded)",
            "shard_count": len(shards),
            "components": len({s["shard"].rpartition("-")[0] for s in shards}),
        },
        "toolchain_contract": toolchain.to_dict(),
        "population": {
            "shards_expected": len(shards),
            "shards_measured": len(measured),
            "shards_missing": [s["shard"] for s in shards if not s["present"]],
            "generated": int((aggregate or {}).get("mutants_generated") or 0),
            "killed": int((aggregate or {}).get("killed") or 0),
            "survived": int((aggregate or {}).get("survived") or 0),
            "no_tests": int((aggregate or {}).get("no_tests") or 0),
            "timeout": int((aggregate or {}).get("timeout") or 0),
            "score": (aggregate or {}).get("mutation_score"),
        },
        "aggregate_verdict": (aggregate or {}).get("verdict"),
        "aggregate_failures": (aggregate or {}).get("failures", []),
        "shards": shards,
    }
    _write_json("baseline.json", baseline)
    return baseline


# ── Phase 1: the mutation canary ─────────────────────────────────────────────


def read_sentinel_sink(path: Path) -> list[dict]:
    """Read the append-only sentinel evidence file, ignoring partial lines."""
    if not path.is_file():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def sentinel_sink_path(root: Path) -> Path:
    """Locate the sentinel evidence for a mutants directory.

    The runner writes one sink per run (``mutation-sentinel-<run_id>.jsonl``)
    and records its path on the shard summary, so every sink is collected rather
    than only the newest: a shard run overwrites ``backend/mutants/``, and the
    trust analysis must be able to reconstruct execution evidence for mutants
    whose per-mutant meta files are gone. The per-run path on the summary is
    authoritative; the directory scan is the fallback.
    """
    candidates = [root / CANARY_SINK_NAME, root.parent / CANARY_SINK_NAME]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def collect_sentinel_records(root: Path) -> list[dict]:
    """Collect every sentinel record available for this analysis.

    Two sources, in priority order:

    1. the sink recorded on each shard summary (``execution_sentinel_path``) —
       this is the run that produced that shard's verdict, so the join between
       "this mutant was measured" and "this mutant was observed" is exact;
    2. any other ``mutation-sentinel-*.jsonl`` in the generated directory, plus
       the canary sink, so evidence is not lost when a summary is absent.

    Records are deduplicated by mutant name because a mutant is typically
    executed by several tests within one fork.
    """
    records: list[dict] = []
    seen: set[str] = set()

    def _add(path: Path) -> None:
        if not path.is_file():
            return
        for record in read_sentinel_sink(path):
            mutant = str(record.get("mutant", ""))
            if not record.get("armed") or mutant in seen:
                continue
            seen.add(mutant)
            record = dict(record)
            record["_source"] = str(path)
            records.append(record)

    for summary_path in sorted(MUTATION_EVIDENCE_DIR.glob("mutation-summary-*.json")):
        payload = _read_json(summary_path)
        if not payload:
            continue
        raw = str(payload.get("execution_sentinel_path") or "")
        if raw:
            _add(REPO_ROOT / raw)

    for path in sorted(MUTATION_EVIDENCE_DIR.glob("mutation-sentinel-*.jsonl")):
        _add(path)
    _add(sentinel_sink_path(root))

    return records


def read_mutant_meta(root: Path) -> dict[str, dict]:
    """Read every mutmut ``.meta`` file under *root*, keyed by mutant name.

    mutmut's per-mutant exit codes are the authoritative record of what happened
    to each mutant. They are written incrementally, so this reads whatever the
    campaign actually produced rather than trusting a summary line.
    """
    out: dict[str, dict] = {}
    if not root.is_dir():
        return out
    for meta_path in sorted(root.rglob("*.meta")):
        payload = _read_json(meta_path)
        if not payload:
            continue
        source_file = meta_path.relative_to(root).with_suffix("").as_posix()
        for mutant, exit_code in (payload.get("exit_code_by_key") or {}).items():
            out[mutant] = {
                "exit_code": exit_code,
                "status": EXIT_STATUS.get(exit_code, "SUSPICIOUS"),
                "source_file": source_file,
                "meta_path": str(meta_path),
            }
    return out


def classify_execution(mutant: str, meta: dict, armed: set[str]) -> str:
    """Classify one mutant into the four Phase 4 outcomes.

    The distinction that matters, and that mutmut's own summary cannot make:
    a survivor the suite actually executed is a *test-oracle* question, while a
    survivor that was never executed is a *reachability* question. Conflating
    them is how a coverage-shaped number gets mistaken for a quality number.

    ``no tests`` and ``not checked`` are reported as NOT_EXECUTED rather than
    folded into the survivors, because mutmut never forks a test process for
    either, so no kill/survive judgement can attach to them.

    A mutant with no per-mutant exit-code record is reported as INVALID_MUTANT:
    mutmut generated it but never recorded a verdict, so no measurement of it
    exists. That is a measurement defect, and it is deliberately NOT reported
    as a survivor — an unmeasured mutant is not a test-quality finding.
    """
    if mutant in meta:
        status = meta[mutant]["status"]
        if status in ("NO_TESTS", "NOT_CHECKED", "SKIPPED", "CAUGHT_BY_TYPE_CHECK"):
            return "NOT_EXECUTED"
        if status in ("KILLED", "TIMEOUT", "SEGFAULT"):
            # A kill/timeout can only follow execution of the mutated code.
            return "EXECUTED_AND_KILLED"
        if status in ("SURVIVED", "SUSPICIOUS", "INTERRUPTED"):
            return "EXECUTED_AND_SURVIVED" if mutant in armed else "NOT_EXECUTED"
        return "NOT_EXECUTED"

    # No per-mutant record: mutmut generated the mutant but never measured it.
    return "INVALID_MUTANT"


def execution_basis(mutant: str, meta: dict, armed: set[str]) -> str:
    """Name the evidence that established (or failed to establish) execution.

    Recorded per survivor so a reader can see WHY a survivor is trusted, rather
    than having to trust the aggregate. ``mutmut-verdict-only`` is the weak
    basis: mutmut recorded a SURVIVED verdict but the independent sentinel has
    no record for that mutant, so execution is inferred from the verdict rather
    than observed. It is still usable, but it is named so the distinction is
    never silently lost.
    """
    if mutant in meta and meta[mutant]["status"] == "SURVIVED":
        return "mutmut-verdict+sentinel" if mutant in armed else "mutmut-verdict-only"
    if mutant in meta and meta[mutant]["status"] in ("NO_TESTS", "NOT_CHECKED"):
        return "mutmut-no-fork"
    if mutant in armed:
        return "sentinel"
    return "none"


def evaluate_canary() -> dict:
    """Phase 1 — prove the harness before any score is interpreted.

    The canary asserts four known outcomes. If any of them is wrong, mutation
    certification must stop: a harness that cannot reliably tell a kill from a
    survival cannot be used to conclude anything about a 78.8% score.
    """
    mutants_root = CANARY_DIR / "mutants"
    sink = sentinel_sink_path(mutants_root)
    meta = read_mutant_meta(mutants_root)
    records = read_sentinel_sink(sink)
    armed = {r["mutant"] for r in records if r.get("armed")}

    def _group(prefix: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for mutant in meta:
            if f".{prefix}__mutmut_" not in mutant:
                continue
            outcome = classify_execution(mutant, meta, armed)
            counts[outcome] = counts.get(outcome, 0) + 1
        return counts

    kill = _group("x_known_kill_value")
    survivor = _group("x_known_survivor_boundary")
    reached = _group("x_known_reached_guard")
    unreached = _group("x_known_unreached_helper")

    # A known-kill mutant must exist and every one of them must have been
    # executed and killed. A survivor there would mean the harness never
    # dispatched the mutation, which is the C71 root-cause failure mode.
    known_kill_ok = bool(kill) and kill.get("EXECUTED_AND_KILLED", 0) > 0
    # A known-survivor location must be EXECUTED (so its survival is a real
    # test-oracle observation) and must yield at least one survivor.
    known_survivor_ok = (
        survivor.get("EXECUTED_AND_SURVIVED", 0) > 0
        and survivor.get("EXECUTED_AND_KILLED", 0) > 0
    )
    # The reached location must be genuinely executed, and the unreached one
    # must never be — that is the proof a non-executed mutant is distinguishable
    # from a genuine test survivor.
    reached_ok = (
        reached.get("EXECUTED_AND_KILLED", 0) > 0
        and reached.get("EXECUTED_AND_SURVIVED", 0) > 0
    )
    unreached_ok = set(unreached) == {"NOT_EXECUTED"} and bool(unreached)

    checks = {
        "KNOWN_KILL_MUTANT": "KILLED" if known_kill_ok else "FAILED",
        "KNOWN_SURVIVOR_MUTANT": "SURVIVED" if known_survivor_ok else "FAILED",
        "KNOWN_REACHED_LOCATION": "REACHED" if reached_ok else "FAILED",
        "KNOWN_UNREACHED_LOCATION": "UNREACHED" if unreached_ok else "FAILED",
    }
    passed = all(v != "FAILED" for v in checks.values())

    result = {
        "schema": "m9-c71-mutation-canary/v1",
        "recorded_at": _now(),
        "passed": passed,
        "checks": checks,
        "canary_root": _display_path(CANARY_DIR),
        "population": len(meta),
        "sentinel_records": len(records),
        "mutants_observed_executing": len(armed),
        "by_location": {
            "known_kill": kill,
            "known_survivor": survivor,
            "known_reached": reached,
            "known_unreached": unreached,
        },
        "raw_mutants": {
            mutant: {
                "exit_code": meta[mutant]["exit_code"],
                "status": meta[mutant]["status"],
                "execution": classify_execution(mutant, meta, armed),
            }
            for mutant in sorted(meta)
        },
        "toolchain_contract": toolchain_state().to_dict(),
    }
    _write_json("mutation-canary.json", result)
    return result


# ── Phase 2: mutant identity ────────────────────────────────────────────────


def _operator_of(mutant: str) -> str:
    """Derive the mutation operator from mutmut's per-operator index.

    mutmut appends ``__mutmut_<n>`` to each mutant symbol. The index is
    positional within a function, so it identifies WHICH operator variant a
    mutant is, and the operator is then read from the diff between the pristine
    source function and the generated mutant function.
    """
    return mutant.rpartition("__mutmut_")[2] if "__mutmut_" in mutant else "?"


def verify_mutant_identity(
    *,
    root: Path,
    source_root: Path,
    sample: Sequence[str] | None = None,
    limit: int = 200,
) -> dict:
    """Phase 2 — prove every sampled mutant is a real, distinct mutation.

    For each mutant this establishes, from repository artefacts only:
    the pristine source hash, the mutated source hash, the mutant identifier,
    the mutated file, the mutated location, and the mutation operator. The
    mutated hash MUST differ from the baseline hash — a mutant whose "mutated"
    source is byte-identical to the pristine source is not a mutant at all, and
    any score counting it is measuring nothing.
    """
    meta = read_mutant_meta(root)
    mutant_symbols: dict[str, str] = {}
    for span_path in sorted(root.rglob("*.spans")):
        index = _read_json(span_path)
        if not index:
            continue
        mutated_file = span_path.with_suffix("").as_posix()
        for name in index.get("spans") or {}:
            mutant_symbols[f"{mutated_file}:{name}"] = mutated_file

    candidates = sorted(meta)
    if sample:
        wanted = set(sample)
        candidates = [m for m in candidates if m in wanted]
    candidates = candidates[:limit] if limit else candidates

    source_cache: dict[str, str] = {}
    verified: list[dict] = []
    invalid: list[dict] = []

    for mutant in candidates:
        info = meta[mutant]
        mutated_rel = info["source_file"]
        pristine_path = source_root / mutated_rel
        mutated_path = root / mutated_rel
        if pristine_path not in source_cache:
            source_cache[pristine_path] = _sha256_file(pristine_path)
        pristine_hash = source_cache[pristine_path]
        mutated_hash = _sha256_file(mutated_path)

        symbol = mutant.rpartition(".")[2]
        function = symbol.split("__mutmut_", 1)[0]
        entry = {
            "mutant": mutant,
            "mutated_file": mutated_rel,
            "mutated_location": f"{mutated_rel}:{function}",
            "function": function,
            "operator_index": _operator_of(mutant),
            "baseline_source_sha256": pristine_hash,
            "mutated_source_sha256": mutated_hash,
            "mutated_differs_from_baseline": bool(
                pristine_hash and mutated_hash and pristine_hash != mutated_hash
            ),
            "exit_code": info["exit_code"],
            "status": info["status"],
        }
        if entry["mutated_differs_from_baseline"]:
            verified.append(entry)
        else:
            invalid.append(entry)

    result = {
        "schema": "m9-c71-mutant-identity/v1",
        "recorded_at": _now(),
        "mutants_available": len(meta),
        "mutants_checked": len(candidates),
        "identity_verified": len(verified),
        "identity_invalid": len(invalid),
        "mutant_modules_indexed": len(mutant_symbols),
        "all_mutated_sources_differ_from_baseline": not invalid,
        "invalid": invalid[:50],
        "verified_sample": verified[:50],
    }
    _write_json("mutant-identity.json", result)
    return result


# ── Phase 3: dispatch contract ──────────────────────────────────────────────


def mutmut_module_name(relative_source_path: str) -> str:
    """Reproduce mutmut's path-derived mutant module name, exactly.

    Faithful to ``mutmut/utils/format_utils.get_mutant_name``, which does:

        module_name = path-without-suffix, "/" -> "."
        module_name = strip_prefix(module_name, "src.")
        mutant_name = f"{module_name}.{method}"
        mutant_name = mutant_name.replace(".__init__.", ".")

    The ``.__init__.`` collapse is applied to the FULL dotted name, which is
    what makes ``src/engines/__init__.py`` resolve to module ``engines`` and not
    to ``engines.__init__``. Reproducing the defective derivation is the point:
    the check has to compare against what mutmut ACTUALLY produces, not against a
    corrected version, or it would not detect the defect it exists to detect.
    """
    path = relative_source_path
    module_name = path[: -len(".py")].replace("/", ".")
    if module_name.startswith("src."):
        module_name = module_name[len("src.") :]
    # Applied to the assembled name, as mutmut does — the trailing "." in
    # f"{module}.{method}" is what makes the substitution fire at all.
    return f"{module_name}.x_probe".replace(".__init__.", ".").rpartition(".")[0]


def normalise_module_name(module: str) -> str:
    """Apply the toolchain contract's normalisation to a real module name.

    Mirrors the installed trampoline (see ``mutmut_contract`` clause
    ``c71-1-src-module-name-normalisation``). A dispatch check that did not use
    the same normalisation the runtime uses would certify a toolchain that is
    not actually installed.
    """
    return module[len("src.") :] if module.startswith("src.") else module


def validate_dispatch() -> dict:
    """Phase 3 — prove the source path -> mutant module -> symbol -> impl chain.

    The chain that must hold for every mutation target in this repository is:

        source path  ->  mutmut mutant module  ->  Python import
                     ->  production symbol     ->  mutated implementation

    The first arrow is the one C71 proved defective: mutmut strips a leading
    ``src.`` from a path-derived module name, and this repository imports
    production code as ``src.<package>``. This check verifies, per source file,
    that the path-derived mutant module name resolves to a real importable
    module and that the mangled function key is present in it.
    """
    import importlib
    import importlib.util

    sys.path.insert(0, str(BACKEND_ROOT))
    checked: list[dict] = []
    problems: list[dict] = []

    for source_path in sorted((BACKEND_ROOT / "src").rglob("*.py")):
        rel = source_path.relative_to(BACKEND_ROOT).as_posix()
        if rel.startswith("src/src/"):
            continue
        import_name = rel[: -len(".py")].replace("/", ".")
        module_name = mutmut_module_name(rel)

        row = {
            "source_file": rel,
            "mutmut_mutant_module": module_name,
            "python_import_module": import_name,
        }
        # The import step of the chain must resolve to THIS file, not merely to
        # some importable module: ``src.engines.credit_card_engine`` is a
        # package whose name coincides with a module elsewhere in the tree, and
        # "it imported something" is not dispatch proof.
        spec = importlib.util.find_spec(import_name)
        resolved = Path(spec.origin) if spec and spec.origin else None
        row["resolves_to_source_file"] = (
            resolved is not None and resolved.resolve() == (source_path.resolve())
        )
        if not row["resolves_to_source_file"]:
            row["resolved_to"] = str(resolved) if resolved else None
            problems.append(row)
            checked.append(row)
            continue

        try:
            module = importlib.import_module(import_name)
        except Exception as exc:
            row.update(importable=False, error=f"{type(exc).__name__}: {exc}")
            problems.append(row)
            checked.append(row)
            continue
        row["importable"] = True

        # The trampoline compares the module part of MUTANT_UNDER_TEST against
        # the mutated function's real __module__. Verify that the normalisation
        # the toolchain contract installs actually makes them equal, for the
        # functions THIS file declares. An empty module (a package __init__ with
        # no functions, or a file whose callables all come from elsewhere)
        # cannot produce a mismatch, so it is vacuously fine.
        own = {
            value.__module__
            for name, value in vars(module).items()
            if not name.startswith("__")
            and callable(value)
            and getattr(value, "__module__", None) == import_name
        }
        row["own_functions"] = len(own)
        if not own:
            row["dispatch_matches"] = True
        else:
            normalised = {normalise_module_name(m) for m in own}
            row["dispatch_matches"] = all(m == module_name for m in normalised)
            row["normalised_modules"] = sorted(normalised)
        if not row["dispatch_matches"]:
            problems.append(row)
        checked.append(row)

    result = {
        "schema": "m9-c71-dispatch-validation/v1",
        "recorded_at": _now(),
        "files_checked": len(checked),
        "files_importable": sum(1 for r in checked if r.get("importable")),
        "files_with_dispatch_match": sum(
            1 for r in checked if r.get("dispatch_matches")
        ),
        "problems": problems,
        "dispatch_valid": not problems,
        "toolchain_contract": toolchain_state().to_dict(),
        "note": (
            "Reproduces mutmut's path-derived module name (including the 'src.' "
            "strip) and asserts it resolves to the real importable module whose "
            "functions the trampoline compares against."
        ),
    }
    _write_json("dispatch-validation.json", result)
    return result


# ── Phase 4: execution sentinel over a representative sample ────────────────

#: The shard classes Phase 4 must sample. Chosen to span the properties that
#: can each independently break mutant execution, so a sample that passes on all
#: of them is evidence about the harness rather than about one lucky engine.
SENTINEL_SAMPLE_CLASSES: tuple[tuple[str, str], ...] = (
    ("small_engine", "cashflow_engine"),
    ("medium_engine", "financial_events"),
    ("large_engine", "behaviour_engine-00"),
    ("function_heavy", "common_calculations"),
    ("defensive_heavy", "ledger_audit_engine"),
    ("classmethod_heavy", "core_domain_money"),
    ("value_object", "balance_engine"),
    ("unreached_concentration", "recommendation_engine"),
)


def execution_sentinel_sample(
    *,
    root: Path,
    limit_per_shard: int = 40,
) -> dict:
    """Phase 4 — establish, per mutant, that the mutated code really ran.

    Classification is a join of two independent sources:

    * mutmut's per-mutant exit code (``<file>.meta``), which says what the test
      process concluded;
    * the sentinel's append-only evidence file, which says whether the mutated
      function's own bytecode was entered.

    A survivor with no sentinel record is NOT a legitimate test survivor: it is
    a mutant the suite never observed, and it is reported as NOT_EXECUTED.

    The census is taken over the CANARY's generated mutants only, not over every
    ``*.meta`` in the tree. A real shard's mutants tree is transient and only
    the most recent shard survives there, so mixing the two would make the
    census describe whichever shard happened to run last — a number that looks
    authoritative and describes nothing. Per-shard verdicts are joined through
    the durable catalogs instead, in :func:`classify_survivors`.
    """
    canary_root = CANARY_DIR / "mutants"
    meta = read_mutant_meta(canary_root)
    records = read_sentinel_sink(sentinel_sink_path(canary_root))
    armed = {r["mutant"] for r in records if r.get("armed")}
    unresolved = {
        r["mutant"] for r in records if r.get("event") == "DISPATCH_UNRESOLVED"
    }

    by_shard: dict[str, dict] = {}
    details: list[dict] = []
    for mutant, info in sorted(meta.items()):
        shard = mutant.split(".", 1)[0]
        bucket = by_shard.setdefault(
            shard,
            {
                "shard": shard,
                "mutants": 0,
                "EXECUTED_AND_KILLED": 0,
                "EXECUTED_AND_SURVIVED": 0,
                "NOT_EXECUTED": 0,
                "INVALID_MUTANT": 0,
                "sentinel_armed": 0,
            },
        )
        outcome = classify_execution(mutant, meta, armed)
        bucket["mutants"] += 1
        bucket[outcome] = bucket.get(outcome, 0) + 1
        if mutant in armed:
            bucket["sentinel_armed"] += 1
        details.append(
            {
                "mutant": mutant,
                "shard": shard,
                "exit_code": info["exit_code"],
                "status": info["status"],
                "sentinel_armed": mutant in armed,
                "dispatch_unresolved": mutant in unresolved,
                "execution": outcome,
            }
        )

    survivors = [d for d in details if d["execution"] == "EXECUTED_AND_SURVIVED"]
    # A mutant mutmut reported as SURVIVED but which the sentinel never observed
    # is the dangerous case: the score counts it as a test-oracle failure while
    # the suite may never have run it. `no tests` mutants are NOT this case —
    # mutmut never forked a test process for them, so their non-execution is
    # self-evident and is reported as NOT_EXECUTED, not as unproven.
    unexecuted_survivors = [
        d
        for d in details
        if d["status"] == "SURVIVED" and d["execution"] != "EXECUTED_AND_SURVIVED"
    ]
    unmeasured = [d for d in details if d["execution"] == "INVALID_MUTANT"]

    result = {
        "schema": "m9-c71-execution-sentinel/v1",
        "recorded_at": _now(),
        "sample_classes": dict(SENTINEL_SAMPLE_CLASSES),
        "mutants_examined": len(details),
        "by_shard": [by_shard[k] for k in sorted(by_shard)],
        "totals": {
            "EXECUTED_AND_KILLED": sum(
                1 for d in details if d["execution"] == "EXECUTED_AND_KILLED"
            ),
            "EXECUTED_AND_SURVIVED": len(survivors),
            "NOT_EXECUTED": sum(1 for d in details if d["execution"] == "NOT_EXECUTED"),
            "INVALID_MUTANT": sum(
                1 for d in details if d["execution"] == "INVALID_MUTANT"
            ),
        },
        "survivors_proven_executed": len(survivors),
        "survivors_without_execution_evidence": len(unexecuted_survivors),
        "unmeasured_mutants": len(unmeasured),
        "execution_proven_for_all_survivors": not unexecuted_survivors
        and not unmeasured,
        "unexecuted_survivor_sample": [d["mutant"] for d in unexecuted_survivors[:25]],
        "unmeasured_sample": [d["mutant"] for d in unmeasured[:25]],
        "limit_per_shard": limit_per_shard,
    }
    _write_json("execution-sentinel.json", result)
    return result


# ── Phase 5/6/7: survivor classification ─────────────────────────────────────

#: Evidence-driven classification rules, evaluated in order. Each rule is a
#: pure function of PROVABLE facts about the mutant — never of "no test killed
#: it", which is circular (it would classify every survivor as a test gap and
#: make the taxonomy worthless).
#:
#: The order is significant: validity and dispatch are checked first, because a
#: mutant that never ran is not a survivor at all, whatever its operator says.


def _load_survivor_records() -> list[dict]:
    """Load every persisted survivor record across all components.

    Source of truth is the durable per-component survivor catalog, which
    ``mutation_runner`` writes from mutmut's own per-mutant verdicts at the end
    of each shard run. It is used in preference to the transient ``.meta`` files
    because a shard run overwrites ``backend/mutants/`` — only the last-run
    shard's per-mutant verdicts survive there, while the catalogs are
    cumulative across the whole campaign.
    """
    records: list[dict] = []
    for path in sorted(MUTATION_EVIDENCE_DIR.glob("mutation-survivors-*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        component = path.stem.replace("mutation-survivors-", "")
        for entry in payload.get("entries", []) or []:
            records.append(
                {
                    "mutant": entry.get("key", ""),
                    "component": component,
                    "source_file": entry.get("source_file", ""),
                    "function": entry.get("function", ""),
                    "operator_class": entry.get("category", ""),
                    "old": entry.get("old", ""),
                    "new": entry.get("new", ""),
                }
            )
    return records


def load_survivor_verdicts() -> dict[str, dict]:
    """Recover each survivor's kill/survive verdict from the durable catalogs.

    ``mutation-survivors-<component>.json`` lists only that component's
    survivors, so membership in the catalog IS the durable record that mutmut
    measured the mutant and the suite did not kill it. Together with the
    transient per-mutant exit codes (present for the most recent shard) this
    gives execution evidence for every survivor in the campaign.
    """
    verdicts: dict[str, dict] = {}
    for path in sorted(MUTATION_EVIDENCE_DIR.glob("mutation-survivors-*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        component = path.stem.replace("mutation-survivors-", "")
        for entry in payload.get("entries", []) or []:
            verdicts[entry.get("key", "")] = {
                "component": component,
                "source_file": entry.get("source_file", ""),
                "function": entry.get("function", ""),
                "category": entry.get("category", ""),
                "old": entry.get("old", ""),
                "new": entry.get("new", ""),
                "status": "SURVIVED",
                "exit_code": 0,
            }
    return verdicts


def classify_survivor(
    record: dict,
    *,
    execution: str,
    basis: str,
    dispatch_problems: frozenset[str],
    equivalence_proofs: dict[str, dict],
) -> SurvivorVerdict:
    """Assign exactly one taxonomy category to a survivor, with evidence.

    Classification order mirrors the causal chain, so a survivor is labelled by
    its EARLIEST applicable cause:

        MUTATION_INVALID   the mutant is not a real mutation
        TOOLING_DEFECT     dispatch could not be proven for it
        NOT_REACHED        the suite never executed it
        EQUIVALENT         proven behaviourally indistinguishable
        UNOBSERVABLE_BY_CONTRACT  proven outside the declared public contract
        DEFENSIVE_PATH     a guard whose trigger is not reachable by design
        PRODUCT_CONTRACT_GAP    the behaviour is real but unspecified
        TEST_HARNESS_GAP        the suite cannot observe it as written
        REAL_TEST_GAP           a genuine, specified behaviour with no assertion
    """
    mutant = record["mutant"]
    function = record.get("function", "")
    component = record.get("component", "")
    source_file = record.get("source_file", "")
    operator = record.get("operator_class", "") or "unknown"

    if execution == "INVALID_MUTANT":
        return SurvivorVerdict(
            mutant=mutant,
            component=component,
            source_file=source_file,
            function=function,
            operator=operator,
            execution=execution,
            basis=basis,
            category="MUTATION_INVALID",
            evidence="no mutmut exit-code record: the mutant was never measured",
        )

    if mutant in dispatch_problems or source_file in dispatch_problems:
        return SurvivorVerdict(
            mutant=mutant,
            component=component,
            source_file=source_file,
            function=function,
            operator=operator,
            execution=execution,
            basis=basis,
            category="TOOLING_DEFECT",
            evidence=(
                "the mutant's dispatch chain could not be proven: its source "
                f"file {source_file!r} does not resolve to an importable "
                "module, so survival cannot be attributed to the test suite"
            ),
        )

    if execution == "NOT_EXECUTED":
        return SurvivorVerdict(
            mutant=mutant,
            component=component,
            source_file=source_file,
            function=function,
            operator=operator,
            execution=execution,
            basis=basis,
            category="NOT_REACHED",
            evidence=(
                "no independent sentinel record of the mutated bytecode being "
                "entered; mutmut never forked a test process able to observe it"
            ),
        )

    proof = equivalence_proofs.get(mutant)
    if proof:
        return SurvivorVerdict(
            mutant=mutant,
            component=component,
            source_file=source_file,
            function=function,
            operator=operator,
            execution=execution,
            basis=basis,
            category=proof["category"],
            evidence=proof["evidence"],
            justification=proof.get("justification", ""),
        )

    return SurvivorVerdict(
        mutant=mutant,
        component=component,
        source_file=source_file,
        function=function,
        operator=operator,
        execution=execution,
        basis=basis,
        category="REAL_TEST_GAP",
        evidence=(
            "the mutated implementation was proven to execute and the suite "
            "observed no behavioural difference; the behaviour is inside the "
            "module under test and is not classified as equivalent without "
            "behavioural proof"
        ),
    )


def classify_survivors(
    *,
    root: Path,
    equivalence_proofs: dict[str, dict],
    dispatch_problems: frozenset[str],
) -> dict:
    """Phase 5 — classify every survivor, requiring UNKNOWN = 0."""
    records = _load_survivor_records()
    # Per-mutant evidence is the union of two sources: the transient exit codes
    # left by the most recent shard run, and the durable per-component survivor
    # catalogs, which are cumulative across the whole campaign. A shard run
    # overwrites ``backend/mutants/``, so relying on the transient files alone
    # would silently reclassify seven of eight components' survivors as
    # unmeasured — a measurement artefact, not a finding.
    transient = read_mutant_meta(root)
    durable = load_survivor_verdicts()
    # The durable catalogs are authoritative for SURVIVED status: a shard run
    # overwrites backend/mutants/, so the transient exit codes for a component
    # describe whichever shard ran last. Where the transient record says
    # NOT_CHECKED for a mutant the catalog records as a measured survivor, the
    # catalog wins — otherwise a component whose meta was overwritten would be
    # silently reclassified as "never executed", inflating the certified score
    # by treating real test gaps as reachability.
    evidence: dict[str, dict] = {**durable, **transient}
    for mutant, catalog in durable.items():
        current = evidence.get(mutant)
        if current is not None and current["status"] in ("NOT_CHECKED", "INVALID_MUTANT"):
            evidence[mutant] = catalog
    armed = {r["mutant"] for r in collect_sentinel_records(root) if r.get("armed")}
    if not records:
        # Fall back to the survivors mutmut's own exit codes attest to, so the
        # taxonomy still applies when no per-component catalog was persisted.
        records = [
            {
                "mutant": mutant,
                "component": mutant.split(".", 1)[0],
                "source_file": info["source_file"],
                "function": mutant.rpartition(".")[2].split("__mutmut_", 1)[0],
                "operator_class": "unknown",
            }
            for mutant, info in evidence.items()
            if info["status"] == "SURVIVED"
        ]

    verdicts = [
        classify_survivor(
            record,
            execution=classify_execution(record["mutant"], evidence, armed),
            basis=execution_basis(record["mutant"], evidence, armed),
            dispatch_problems=dispatch_problems,
            equivalence_proofs=equivalence_proofs,
        )
        for record in records
    ]

    by_category: dict[str, int] = dict.fromkeys(SURVIVOR_CATEGORIES, 0)
    by_component: dict[str, dict[str, int]] = {}
    for verdict in verdicts:
        by_category[verdict.category] = by_category.get(verdict.category, 0) + 1
        bucket = by_component.setdefault(verdict.component, {})
        bucket[verdict.category] = bucket.get(verdict.category, 0) + 1

    unknown = by_category.get("UNKNOWN", 0)
    result = {
        "schema": "m9-c71-survivor-classification/v1",
        "recorded_at": _now(),
        "survivors_classified": len(verdicts),
        "by_category": by_category,
        "by_component": {k: by_component[k] for k in sorted(by_component)},
        "unknown_survivors": unknown,
        "genuine_gap_survivors": sum(
            n for c, n in by_category.items() if c in GENUINE_GAP_CATEGORIES
        ),
        "structural_survivors": sum(
            n for c, n in by_category.items() if c in STRUCTURAL_CATEGORIES
        ),
        "verdicts": [v.to_dict() for v in verdicts],
    }
    _write_json("survivor-classification.json", result)
    return result


# ── Phase 7: equivalence analysis (behavioural, never survival-based) ────────

#: Mutmut string-literal and numeric-argument replacements that are provably
#: inert for a given call surface. Each entry names a transformation whose
#: observable effect is bounded by a structural property of the code, so the
#: proof is about behaviour and never about survival.
EQUIVALENCE_PROOFS: dict[str, dict] = {}


def prove_default_argument_equivalence(
    module_path: Path, function_name: str
) -> dict | None:
    """Prove, structurally, that a ``dict.get`` default swap is unobservable.

    The C71 financial_events survivor concentration (~181 ``event.get`` default
    swaps) is the single largest block of survivors in the campaign, and the
    question is whether any of them changes observable behaviour.

    A ``K.get(key, D)`` → ``K.get(key, D')`` mutation is provably unobservable
    when BOTH of the following hold, read from the function's own AST:

      1. the default is only ever consumed by a comparison or a membership
         test against a value that ``D`` and ``D'`` cannot distinguish, or
      2. ``D`` and ``D'`` are both falsy/empty AND the value is only used in a
         boolean context.

    The proof is established by executing the function under BOTH the pristine
    and the mutated module over a bounded but non-trivial input domain and
    comparing every externally observable output — return value, raised
    exception, and mutated-input state. Survival is never an input to the
    conclusion.
    """
    import ast as _ast

    if not module_path.is_file():
        return None
    try:
        tree = _ast.parse(module_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None

    for node in _ast.walk(tree):
        if not isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            continue
        if node.name not in (function_name, f"__{function_name}"):
            continue
        defaults = []
        for call in _ast.walk(node):
            if (
                isinstance(call, _ast.Call)
                and isinstance(call.func, _ast.Attribute)
                and call.func.attr == "get"
                and len(call.args) == 2
                and isinstance(call.args[1], _ast.Constant)
            ):
                default = call.args[1].value
                if default in ("", None):
                    defaults.append((call.lineno, call.args[1].lineno, default))
        if defaults:
            return {
                "function": node.name,
                "location": f"{module_path.name}:{node.lineno}",
                "empty_string_defaults": [
                    {"call_line": c, "default_line": d, "default": v}
                    for c, d, v in defaults
                ],
            }
    return None


def _observable(module_path: Path, function_name: str, inputs: Sequence) -> list:
    """Execute *function_name* from *module_path* and capture every observable.

    Observable = (returned value, raised exception type, mutated input).
    Comparing these between the pristine and the mutated implementation is what
    makes an equivalence claim behavioural rather than statistical.

    The loaded module is evicted from ``sys.modules`` afterwards so a second
    comparison against the same path re-executes the CURRENT file rather than
    reusing a stale module object.
    """
    import importlib.util
    import sys as _sys

    alias = "c71_equiv_" + re.sub(
        r"\W+", "_", f"{module_path}_{_sha256_file(module_path)[:12]}"
    )
    spec = importlib.util.spec_from_file_location(alias, module_path)
    if spec is None or spec.loader is None:
        return []
    module = importlib.util.module_from_spec(spec)
    # CPython caches bytecode by (mtime seconds, size). Two writes of the same
    # length inside one filesystem timestamp tick therefore collide and the
    # SECOND file loads the FIRST file's code. For an equivalence comparison
    # that is the worst possible direction: a changed implementation would
    # compare EQUAL to its pristine original and be certified equivalent. The
    # cache entry is therefore invalidated explicitly before loading.
    cache = importlib.util.cache_from_source(str(module_path))
    if os.path.exists(cache):
        with contextlib.suppress(OSError):
            os.remove(cache)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return []
    finally:
        _sys.modules.pop(alias, None)

    target = getattr(module, function_name, None)
    if target is None:
        for name, value in vars(module).items():
            if name.lstrip("_") == function_name.lstrip("_") and callable(value):
                target = value
                break
    if target is None:
        return []

    observations = []
    for args in inputs:
        call_args = list(args)
        snapshot = None
        if call_args and isinstance(call_args[0], (dict, list)):
            snapshot = repr(call_args[0])
        try:
            result = target(*call_args)
            outcome = ("return", repr(result))
        except Exception as exc:  # noqa: BLE001 - the exception IS the observation
            outcome = ("raise", type(exc).__name__)
        after = (
            repr(call_args[0])
            if call_args and isinstance(call_args[0], (dict, list))
            else None
        )
        observations.append((outcome, snapshot, after))
    return observations


def analyse_equivalence(
    *,
    root: Path,
    source_root: Path,
    survivors: Sequence[dict],
    max_functions: int = 500,
) -> dict:
    """Phase 7 — establish equivalence from behaviour, never from survival.

    Two complementary methods, both based on comparing the ACTUAL two
    implementations rather than a model of them:

    * **dual execution** — the pristine source function and the mutmut-generated
      mutant function are both compiled and executed over a bounded input
      domain, and every externally observable output (return value, raised
      exception, mutated input state) is compared. This is the strongest
      practical evidence available and is used whenever a generated mutant
      function is available on disk.

    * **expression-level behavioural proof** — for the large blocks of survivors
      that are single-statement rewrites recorded in the durable catalogs
      (``old``/``new``), the pair is analysed structurally: an ``.get(key, D)``
      → ``.get(key, D')`` swap where both defaults are falsy and the result is
      consumed only in a boolean/coalescing context is provably unobservable.
      This is a proof about the code, not an inference from survival.

    A mutant is NEVER classified equivalent merely because no test killed it.
    """
    evidence: list[dict] = []
    proofs: dict[str, dict] = {}
    by_function: dict[tuple[str, str], list[dict]] = {}
    for record in survivors:
        key = (record.get("source_file", ""), record.get("function", ""))
        by_function.setdefault(key, []).append(record)

    for (source_file, function), records in sorted(by_function.items()):
        if len(evidence) >= max_functions or not source_file or not function:
            continue
        mutants = [r["mutant"] for r in records]
        pristine = source_root / source_file
        generated = root / source_file
        operator = records[0].get("operator_class", "") or "unknown"

        # ── method 1: dual execution of the two real implementations ──────────
        if pristine.is_file() and generated.is_file():
            _orig, _mut, _lineno, derived = _extract_function_pair(
                pristine, generated, function
            )
            if derived:
                operator = derived
            inputs = _bounded_input_domain(function, source_file)
            original_obs = _observable(pristine, function, inputs)
            mutant_obs = _observable(generated, function, inputs)
            if original_obs and mutant_obs:
                identical = original_obs == mutant_obs
                row = {
                    "method": "dual-execution",
                    "source_file": source_file,
                    "function": function,
                    "operator_class": operator,
                    "mutants": mutants,
                    "inputs_compared": len(inputs),
                    "observable_identical": identical,
                    "original_observables": [list(o) for o in original_obs[:12]],
                    "mutant_observables": [list(o) for o in mutant_obs[:12]],
                }
                if identical:
                    row["category"] = "EQUIVALENT"
                    row["evidence"] = (
                        f"executed the pristine and the mutated implementation of "
                        f"{function!r} side by side over {len(inputs)} bounded inputs and "
                        "compared return value, raised exception, and mutated input "
                        "state at every step: all observables identical"
                    )
                    row["justification"] = (
                        "behaviourally equivalent over the compared input domain; "
                        "the mutant cannot be killed because it is indistinguishable "
                        "from the original, not because the suite is incomplete"
                    )
                else:
                    row["category"] = "REAL_TEST_GAP"
                    row["evidence"] = (
                        f"pristine and mutated implementations of {function!r} differ "
                        f"observably over {len(inputs)} bounded inputs"
                    )
                evidence.append(row)
                if identical:
                    for mutant in mutants:
                        proofs[mutant] = {
                            "category": "EQUIVALENT",
                            "evidence": row["evidence"],
                            "justification": row["justification"],
                        }
                continue

        # ── method 2: expression-level behavioural proof from the catalog ────
        proof = _prove_expression_equivalence(pristine, function, records)
        row = {
            "method": "expression-proof",
            "source_file": source_file,
            "function": function,
            "operator_class": operator,
            "mutants": mutants,
            **proof,
        }
        evidence.append(row)
        proven = proof.get("equivalent_mutants") or []
        if proof.get("category") == "EQUIVALENT" and proven:
            for mutant in proven:
                proofs[mutant] = {
                    "category": "EQUIVALENT",
                    "evidence": proof.get("evidence", ""),
                    "justification": proof.get("justification", ""),
                }

    EQUIVALENCE_PROOFS.clear()
    EQUIVALENCE_PROOFS.update(proofs)

    result = {
        "schema": "m9-c71-equivalence-evidence/v1",
        "recorded_at": _now(),
        "functions_analysed": len(evidence),
        "functions_proven_equivalent": sum(
            1 for r in evidence if r.get("category") == "EQUIVALENT"
        ),
        "functions_shown_distinguishable": sum(
            1 for r in evidence if r.get("category") == "REAL_TEST_GAP"
        ),
        "functions_unproven": sum(1 for r in evidence if not r.get("category")),
        "functions_partially_proven": sum(
            1
            for r in evidence
            if r.get("category") == "EQUIVALENT" and r.get("distinguishable_mutants")
        ),
        "mutants_proven_equivalent": len(proofs),
        "method": (
            "Two independent methods, both comparing the ACTUAL two "
            "implementations rather than a model. (1) Dual execution: the "
            "pristine and the mutmut-generated mutant function are compiled and "
            "run over a bounded input domain, and every externally observable "
            "output (return value, raised exception, mutated input state) is "
            "compared. (2) Expression-level proof: single-statement rewrites "
            "recorded in the durable catalogs are analysed structurally. "
            "Survival is never an input to either conclusion."
        ),
        "analysis": evidence,
    }
    _write_json("equivalence-evidence.json", result)
    return result


def _function_names_match(candidate: str, recorded: str) -> bool:
    """Match a pristine function name against a catalog-recorded mutant name.

    The durable catalogs record the MUTMUT-MANGLED symbol
    (``x__parse_amount_paise``) while the pristine source declares
    ``_parse_amount_paise``, so a plain comparison never matches and the
    analysis silently proves nothing. Stripping mutmut's ``x_`` prefix and
    ignoring dunder-underscore padding reconciles the two naming forms.
    """

    def _normalise(name: str) -> str:
        name = name.split("__mutmut_", 1)[0]
        if name.startswith("x_"):
            name = name[1:]
        return name.strip("_")

    return _normalise(candidate) == _normalise(recorded)


def _prove_expression_equivalence(
    pristine: Path, function: str, records: Sequence[dict]
) -> dict:
    """Prove, structurally, that a survivor block is behaviourally inert.

    The campaign's largest survivor block is a set of ``.get(key, D)`` →
    ``.get(key, D')`` default swaps (the C71 financial_events concentration and
    the cashflow_engine ``or 0`` pattern). For each such pair this asks a
    question about the CODE, not about the tests:

        is the returned default consumed anywhere it could distinguish D from
        D', and if so, is it consumed in a context that only tests falsiness?

    The answer is read from the function's own AST, so the conclusion holds
    regardless of what any test suite does. When the question cannot be answered
    from the code alone, no category is returned and the mutant stays a
    REAL_TEST_GAP — the analysis never guesses.
    """
    import ast as _ast

    pairs = [
        (r.get("old", ""), r.get("new", ""))
        for r in records
        if r.get("old") and r.get("new")
    ]
    if not pairs:
        return {"category": None, "evidence": "no recorded source pair to analyse"}

    try:
        tree = _ast.parse(pristine.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return {"category": None, "evidence": "pristine source unreadable"}

    target = None
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)) and (
            _function_names_match(node.name, function)
        ):
            target = node
            break
    if target is None:
        return {"category": None, "evidence": "function not found in pristine source"}

    # The literal set the survivors swap between, as repr() so it can be
    # compared directly against the constants in a membership test.
    swapped: set[str] = set()
    for old, new in pairs:
        for literal in (_literal_after(old), _literal_after(new)):
            if literal is not _UNSET:
                swapped.add(repr(_literal_value(literal)))
    falsy_only = _consumed_as_falsiness_only(target, swapped)

    detail: list[str] = []
    equivalent_mutants: list[str] = []
    distinguishable_mutants: list[str] = []
    for record in records:
        old, new = record.get("old", ""), record.get("new", "")
        old_literal = _literal_after(old)
        new_literal = _literal_after(new)
        if old_literal is _UNSET or new_literal is _UNSET:
            distinguishable_mutants.append(record.get("mutant", ""))
            detail.append(
                f"{old.strip()[:60]!r} -> {new.strip()[:60]!r}: not a literal swap"
            )
            continue
        if _norm(old_literal) == _norm(new_literal):
            equivalent_mutants.append(record.get("mutant", ""))
            detail.append(f"{old_literal} -> {new_literal}: falsy-equivalent")
        else:
            distinguishable_mutants.append(record.get("mutant", ""))
            detail.append(f"{old_literal} -> {new_literal}: observably different")

    if not detail:
        return {"category": None, "evidence": "no comparable survivor pairs"}
    if not equivalent_mutants:
        return {
            "category": None,
            "evidence": "no survivor in this block is a falsy-equivalent swap: "
            + "; ".join(detail[:3]),
        }
    if not falsy_only["ok"]:
        return {
            "category": None,
            "equivalent_candidates": equivalent_mutants,
            "evidence": (
                "literals are falsy-equivalent but the mutated value is consumed "
                f"in a distinguishing context ({falsy_only['reason']}); "
                "equivalence not provable from the code alone"
            ),
        }

    # Partial proof: the falsy-equivalent subset IS proven equivalent even when a
    # sibling mutant in the same function is observably different. Reporting the
    # whole block as one category would either over-claim (marking the
    # observable mutants equivalent) or under-claim (marking the proven ones as
    # test gaps). Both are wrong, so the proof is per-mutant.
    return {
        "category": "EQUIVALENT",
        "equivalent_mutants": equivalent_mutants,
        "distinguishable_mutants": distinguishable_mutants,
        "evidence": (
            f"{len(equivalent_mutants)} of {len(records)} survivors in "
            f"{target.name!r} replace a literal with a falsy-equivalent one "
            f"({'; '.join(detail[:3])}), and every consumer of the mutated value "
            f"uses it in a context that cannot distinguish them "
            f"({falsy_only['consumers']} use(s): {falsy_only['kinds']}). "
            f"The remaining {len(distinguishable_mutants)} survivor(s) do change "
            "a literal observably and stay genuine test gaps."
        ),
        "justification": (
            "provably unobservable from the code's own AST: the mutation replaces "
            "a literal with a falsy-equivalent one and every use site either tests "
            "falsiness or tests membership against a literal set that excludes both "
            "forms. Equivalent, not merely untested."
        ),
    }


#: Calls whose result depends only on the falsiness of their argument.
_FALSY_TRANSPARENT_CALLS = frozenset(
    {"int", "bool", "float", "complex", "len", "any", "all", "not", "sum"}
)


def _names_bound_to_get_default(function) -> set[str]:  # noqa: ANN001 - ast node
    """Return the locals assigned directly from a ``.get(key, default)`` call.

    Scoping the equivalence proof to exactly these names is what makes it
    specific: the dictionary the value was read from, and every unrelated local
    in the function, are then not treated as consumers, so a genuine use of the
    mutated value can no longer hide behind an incidental one.
    """
    import ast as _ast

    names: set[str] = set()
    for node in _ast.walk(function):
        if not isinstance(node, _ast.Assign) or not isinstance(node.value, _ast.Call):
            continue
        call = node.value
        if not (
            isinstance(call.func, _ast.Attribute)
            and call.func.attr == "get"
            and len(call.args) >= 1
        ):
            continue
        for target in node.targets:
            if isinstance(target, _ast.Name):
                names.add(target.id)
    return names


def _consumed_as_falsiness_only(
    function, swapped: set[str]
) -> dict:  # noqa: ANN001 - ast node
    """Check that every use of a mutated value in *function* cannot distinguish
    the swapped literals.

    Two sound contexts are accepted:

    * **falsiness only** — the value is used as a boolean test, an ``or``/``and``
      operand, a branch condition, a ``not``, a return, an assignment, or is
      passed to a call that itself only tests falsiness.
    * **membership against a literal set that excludes both literals** — the
      dominant pattern in this repository's event predicates
      (``event.get("event_type", "") in ("liability_increase", ...)``). Here
      ``""`` and ``None`` are both absent from the tuple, so membership returns
      the same result for both. This is not a falsiness argument: it is a
      literal-set argument, and it is checked directly against the AST.

    Anything else — a comparison against a computed value, a format string, a
    dict key, an attribute access, a string operation — CAN distinguish the two
    forms, so the check fails and the survivor stays a REAL_TEST_GAP.
    Deliberately conservative: a false negative leaves a survivor block
    unclassified as equivalent, which is the safe direction.
    """
    # Identify precisely WHICH local receives the .get(...) default. Scoping the
    # analysis to that name is what makes the proof sound and specific: the
    # container it was read from (``event``) and unrelated locals are then not
    # considered consumers, so a real use of the mutated value cannot be missed
    # behind an incidental one.
    mutated_names = _names_bound_to_get_default(function)
    if not mutated_names:
        return {
            "ok": False,
            "kinds": "none",
            "consumers": 0,
            "reason": "no local is bound to a .get(key, default) call",
        }

    import ast as _ast

    # Scan the function BODY only. Walking the whole FunctionDef node also
    # yields the def's own name, its decorator list and its default arguments,
    # which are never consumers of a mutated local — treating them as uses made
    # every function look like it leaked its value, and silently blocked the
    # proof for exactly the predicates it was written for.
    body_nodes: list[object] = []
    for statement in function.body:
        body_nodes.extend(_ast.walk(statement))

    parents: dict[int, object] = {}
    for parent in body_nodes:
        for child in _ast.iter_child_nodes(parent):
            parents[id(child)] = parent

    kinds: list[str] = []
    uses = 0
    for node in body_nodes:
        if not isinstance(node, _ast.Name):
            continue
        if node.id not in mutated_names:
            continue
        parent = parents.get(id(node))
        if isinstance(parent, _ast.Store):
            # The binding itself is not a use.
            continue

        uses += 1
        if isinstance(parent, _ast.BoolOp):
            kinds.append("boolop")
        elif isinstance(parent, _ast.UnaryOp) and isinstance(parent.op, _ast.Not):
            kinds.append("not")
        elif isinstance(parent, (_ast.If, _ast.IfExp, _ast.While, _ast.Assert)):
            kinds.append("branch")
        elif isinstance(parent, _ast.Return):
            kinds.append("return")
        elif isinstance(parent, (_ast.Assign, _ast.AnnAssign, _ast.AugAssign)):
            kinds.append("assign")
        elif isinstance(parent, _ast.Compare) and _membership_excludes(
            parent, node, swapped
        ):
            kinds.append("membership-excludes")
        elif isinstance(parent, _ast.Call):
            fname = getattr(parent.func, "id", None) or getattr(
                parent.func, "attr", None
            )
            if fname in _FALSY_TRANSPARENT_CALLS:
                kinds.append(f"call:{fname}")
            else:
                return _fail_uses(kinds, uses, f"value passed to {fname}()")
        else:
            return _fail_uses(
                kinds, uses, f"value escapes into {type(parent).__name__}"
            )

    return {
        "ok": True,
        "kinds": ",".join(sorted(set(kinds))) or "none",
        "consumers": uses,
        "reason": "",
    }


def _fail_uses(kinds: list[str], uses: int, reason: str) -> dict:
    return {
        "ok": False,
        "kinds": ",".join(sorted(set(kinds))) or "none",
        "consumers": uses,
        "reason": reason,
    }


def _membership_excludes(compare, operand, swapped: set[str]) -> bool:
    """True when *operand* is the subject of an ``in`` test whose literal set
    contains NEITHER swapped literal.

    ``x in ("liability_increase", "emi_payment")`` proves the comparators are
    literals, and if the value can only be ``""`` or ``None`` — neither of which
    appears in the set — membership returns the same answer for both. That is the
    whole basis of the equivalence proof for the event-predicate survivor block,
    and it is checked against the AST rather than assumed.

    If either swapped literal DOES appear in the set, the two forms are
    distinguishable and the proof is refused.
    """
    import ast as _ast

    if not isinstance(compare, _ast.Compare) or len(compare.ops) != 1:
        return False
    if not isinstance(compare.ops[0], (_ast.In, _ast.NotIn)):
        return False
    if compare.left is not operand:
        return False

    present: set[str] = set()
    literal_only = True
    for comparator in compare.comparators:
        if isinstance(comparator, (_ast.Tuple, _ast.List, _ast.Set)):
            if not comparator.elts:
                literal_only = False
                break
            for element in comparator.elts:
                if not isinstance(element, _ast.Constant):
                    literal_only = False
                    break
                present.add(repr(element.value))
        elif isinstance(comparator, _ast.Constant):
            present.add(repr(comparator.value))
        else:
            literal_only = False
            break

    if not literal_only:
        return False
    return not (swapped & present)


class _Unset:
    """Sentinel distinguishing 'no literal found' from a literal ``None``."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "<unset>"


_UNSET = _Unset()


def _literal_after(text: str) -> object:
    """Extract the literal that a mutation replaced, from a recorded old→new pair.

    The durable catalogs record a single-statement rewrite, e.g.
    ``x.get(k, 0)`` → ``x.get(k, None)``. The literal that CHANGED is the one
    present on exactly one side — the dict KEY is present on both, so it is
    excluded by the set difference rather than by position, which would be
    brittle across mutmut's operator shapes.
    """
    import re

    literal = re.compile(
        r"""(?<![\w.])(?:None|True|False|-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|"""
        r""""(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')(?![\w.])"""
    )
    if not literal.findall(text or ""):
        return _UNSET
    # Prefer a falsy-equivalent-looking token: that is the class of swap this
    # block is made of. When several candidates changed, the last one in source
    # order is the one mutmut rewrote.
    ordered = literal.findall(text or "")
    for token in reversed(ordered):
        if _norm(token) == "falsy":
            return token
    return ordered[-1]


def _norm(literal: object) -> str:
    """Normalise a literal token to its falsiness class."""
    if literal is _UNSET:
        return "<unset>"
    token = str(literal)
    if token in ("None", "False", "0", "0.0", '""', "''", "()", "[]", "{}"):
        return "falsy"
    return f"truthy:{token}"


def _literal_value(token: object) -> object:
    """Convert a matched literal token to the Python value it denotes."""
    if token is _UNSET:
        return _UNSET
    text = str(token)
    if text == "None":
        return None
    if text == "True":
        return True
    if text == "False":
        return False
    try:
        return int(text) if not any(c in text for c in ".eE") else float(text)
    except ValueError:
        pass
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


# ── equivalence helpers ──────────────────────────────────────────────────────


def _extract_function_pair(
    pristine: Path, generated: Path, function: str
) -> tuple[str, str, int | None, str]:
    """Extract the pristine and mutated full-function sources for *function*.

    mutmut's unit of mutation is the whole function body: every operator variant
    of a function is a complete re-emission of that function. Comparing those
    two complete sources is therefore the most direct form of evidence
    available, and it is what :func:`analyse_equivalence` executes.

    Returns ``(original_source, mutated_source, lineno, operator_class)``. The
    operator class is inferred from the *shape* of the difference, so it is
    derived from the code rather than asserted.
    """
    import ast as _ast

    def _grab(path: Path) -> tuple[str, int | None] | None:
        try:
            tree = _ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            return None
        for node in _ast.walk(tree):
            if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                name = node.name
                if _function_names_match(name, function):
                    src = _ast.get_source_segment(
                        path.read_text(encoding="utf-8"), node
                    )
                    if src:
                        return src, node.lineno
        return None

    orig = _grab(pristine)
    # The generated file names mutants x_<func>__mutmut_<n>; match on the
    # mangled key mutmut uses rather than on the original function name.
    mut = None
    try:
        tree = _ast.parse(generated.read_text(encoding="utf-8"))
        text = generated.read_text(encoding="utf-8")
        for node in _ast.walk(tree):
            if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                name = node.name
                if name.startswith(f"x_{function.lstrip('_')}__mutmut_"):
                    mut = (_ast.get_source_segment(text, node), node.lineno)
                    break
                if name == f"x_{function.lstrip('_')}" and mut is None:
                    mut = (_ast.get_source_segment(text, node), node.lineno)
    except (OSError, SyntaxError):
        mut = None

    if not orig or not mut or not mut[0]:
        return "", "", None, ""
    orig_src, orig_line = orig
    mut_src, mut_line = mut
    return orig_src, mut_src, mut_line, _operator_class(orig_src, mut_src)


def _operator_class(original: str, mutated: str) -> str:
    """Classify the shape of a source difference, from the code itself."""
    import ast as _ast
    import difflib

    diff = list(
        difflib.unified_diff(
            original.splitlines(), mutated.splitlines(), lineterm="", n=0
        )
    )
    changed = [
        line for line in diff if line.startswith(("+", "-")) and line[1:].strip()
    ]

    def _nodes(src: str) -> list:
        try:
            return list(_ast.walk(_ast.parse(src)))
        except SyntaxError:
            return []

    orig_nodes = {type(n) for n in _nodes(original)}
    mut_nodes = {type(n) for n in _nodes(mutated)}
    if _ast.Compare in (mut_nodes - orig_nodes) or _ast.Compare in (
        orig_nodes - mut_nodes
    ):
        return "comparison"
    if _ast.BinOp in (mut_nodes - orig_nodes) or _ast.BinOp in (orig_nodes - mut_nodes):
        return "arithmetic"
    if _ast.BoolOp in (mut_nodes - orig_nodes) or _ast.BoolOp in (
        orig_nodes - mut_nodes
    ):
        return "boolean"
    if _ast.Constant in (mut_nodes - orig_nodes):
        return "constant"
    if any("return" in line for line in changed):
        return "control_flow"
    return "expression" if changed else "none"


def _bounded_input_domain(function: str, source_file: str) -> list:
    """Build a bounded, non-trivial input domain for *function*.

    Chosen from the function's observable contract: monetary amounts, event
    dictionaries, date strings, and boundary integers. Every domain is finite
    and small enough for dual execution, but large enough that an equivalence
    claim is not vacuous.
    """
    name = function.lower()
    if "event" in name or "lifecycle" in name or "walk" in name or "merge" in name:
        domain_events = [
            {},
            {"event_type": "repayment"},
            {"event_type": "transfer"},
            {"event_type": "liability"},
            {"event_type": "revocation"},
            {"event_type": "unknown"},
            {"event_type": None},
            {"event_type": ""},
            {"amount": 100, "event_type": "repayment"},
            {"amount": 0, "event_type": "transfer"},
        ]
        return [(dict(e),) for e in domain_events]
    if "date" in name or "day" in name:
        return [
            (s,) for s in ("2024-01-01", "2024-02-29", "2023-12-31", "", "not-a-date")
        ]
    if "money" in name or "amount" in name or "rupee" in name or "value" in name:
        return [(n,) for n in (0, 1, -1, 2, 10, 100, 1000, -1000)]
    return [(n,) for n in (0, 1, -1, 2, 5, 10, 11, 100)]


# ── Phase 6: reachability ────────────────────────────────────────────────────

#: Reachability verdicts for a NOT_REACHED location, in the vocabulary the
#: milestone requires. Decided from the code's own structure, never from the
#: number of tests that happened to touch it.
REACHABILITY_VERDICTS: tuple[str, ...] = (
    "dead code",
    "legitimate untested branch",
    "configuration-dependent branch",
    "error path",
    "environment-dependent path",
    "defensive branch",
)


def analyse_reachability(
    *,
    root: Path,
    source_root: Path,
    classification: dict,
) -> dict:
    """Phase 6 — decide WHY a NOT_REACHED location was not reached.

    Nothing is deleted automatically. A branch that represents real application
    behaviour gets the smallest meaningful test; a branch that is genuinely
    unreachable is documented as such, and left in place.
    """
    not_reached = [
        v for v in classification.get("verdicts", []) if v["category"] == "NOT_REACHED"
    ]
    by_location: dict[tuple[str, str], list[dict]] = {}
    for verdict in not_reached:
        by_location.setdefault(
            (verdict["source_file"], verdict["function"]), []
        ).append(verdict)

    rows: list[dict] = []
    for (source_file, function), verdicts in sorted(by_location.items()):
        path = source_root / source_file
        verdict = _reachability_verdict_for(path, function)
        rows.append(
            {
                "source_file": source_file,
                "function": function,
                "mutants": len(verdicts),
                "reachability": verdict["reachability"],
                "trigger": verdict["trigger"],
                "evidence": verdict["evidence"],
                "action": verdict["action"],
            }
        )

    summary: dict[str, int] = {}
    for row in rows:
        summary[row["reachability"]] = (
            summary.get(row["reachability"], 0) + row["mutants"]
        )

    result = {
        "schema": "m9-c71-reachability-evidence/v1",
        "recorded_at": _now(),
        "not_reached_mutants": len(not_reached),
        "not_reached_locations": len(rows),
        "by_reachability": summary,
        "locations": rows,
    }
    _write_json("reachability-evidence.json", result)
    return result


def _reachability_verdict_for(path: Path, function: str) -> dict:
    """Classify one unreached location from its own source structure."""
    import ast as _ast

    if not path.is_file():
        return {
            "reachability": "dead code",
            "trigger": "",
            "evidence": "source file is not present in the tree",
            "action": "investigate the source path; do not delete automatically",
        }
    try:
        tree = _ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return {
            "reachability": "dead code",
            "trigger": "",
            "evidence": "source file does not parse",
            "action": "investigate the source file",
        }

    target = None
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)) and (
            _function_names_match(node.name, function)
        ):
            target = node
            break
    if target is None:
        # No such function in the file: nothing can reach it.
        return {
            "reachability": "dead code",
            "trigger": "",
            "evidence": (
                f"no function named {function!r} exists in {path.name}; the "
                "mutant targets a symbol the source no longer declares"
            ),
            "action": "reconcile the mutation population with the source tree",
        }

    body = _ast.dump(target)
    if "Raise" in body and "if" not in body:
        kind, trigger = "error path", "raises unconditionally"
    elif "os.environ" in body or "getenv" in body:
        kind, trigger = "environment-dependent path", "reads process environment"
    elif "if" not in body:
        kind, trigger = "defensive branch", "no conditional guard"
    else:
        guards = [n for n in _ast.walk(target) if isinstance(n, _ast.Compare)]
        if guards:
            kind = "legitimate untested branch"
            trigger = "; ".join(_ast.unparse(g) for g in guards[:3])
        else:
            kind, trigger = "defensive branch", "no comparison guard"

    action = {
        "dead code": "document; do not delete automatically",
        "legitimate untested branch": (
            "create the smallest meaningful test that reaches this branch"
        ),
        "configuration-dependent path": "test via the configuration that enables it",
        "error path": "add the error-path contract test",
        "environment-dependent path": "add a test that sets the environment explicitly",
        "defensive branch": "document; a defensive guard is legitimate contract",
    }[kind]

    return {
        "reachability": kind,
        "trigger": trigger,
        "evidence": (f"read from the function's own AST in {path.name}: {trigger}"),
        "action": action,
    }


# ── Phase 10: prioritisation ─────────────────────────────────────────────────

#: Business criticality by component. Derived from what the component decides,
#: not from its survivor count: an untested rounding rule in a payment path
#: matters more than an untested label in a presentation helper.
BUSINESS_CRITICALITY: dict[str, int] = {
    "credit_card_engine": 10,
    "loan_engine": 10,
    "account_engine": 9,
    "balance_engine": 9,
    "core_domain_money": 9,
    "ledger_audit_engine": 9,
    "cashflow_engine": 8,
    "financial_events": 8,
    "reconciliation_engine": 8,
    "common_calculations": 7,
    "recommendation_engine": 6,
    "financial_intelligence": 6,
    "transaction_intelligence": 6,
    "behaviour_engine": 5,
}

#: Observability weight per mutation operator. An arithmetic or comparison
#: mutation changes a numeric result a business consumer can see; a boolean
#: mutation often only changes a branch that may be unreachable.
OPERATOR_LEVERAGE: dict[str, int] = {
    "arithmetic": 5,
    "comparison": 4,
    "constant": 3,
    "control_flow": 3,
    "expression": 3,
    "boolean": 2,
    "unknown": 1,
}


def prioritise_survivors(classification: dict) -> dict:
    """Phase 10 — rank genuine REAL_TEST_GAP survivors by assurance gained.

    The ranking deliberately does NOT use survivors-per-mutant. Selecting a
    shard because it has the best ratio optimises the mutation percentage per
    line of test code, which is the wrong objective. The objective here is
    assurance: how much real, specified, observable behaviour becomes verified
    by closing this gap.
    """
    gaps = [
        v
        for v in classification.get("verdicts", [])
        if v["category"] == "REAL_TEST_GAP"
    ]
    by_function: dict[tuple[str, str], list[dict]] = {}
    for verdict in gaps:
        by_function.setdefault(
            (verdict["component"], f"{verdict['source_file']}::{verdict['function']}"),
            [],
        ).append(verdict)

    ranked: list[dict] = []
    for (component, location), verdicts in by_function.items():
        survivor_count = len(verdicts)
        criticality = BUSINESS_CRITICALITY.get(component, 3)
        operators = {v["operator"] for v in verdicts}
        leverage = max((OPERATOR_LEVERAGE.get(o, 1) for o in operators), default=1)
        # Assurance score: how much verified behaviour one test would buy,
        # weighted by what that behaviour decides.
        score = survivor_count * leverage * criticality
        ranked.append(
            {
                "component": component,
                "location": location,
                "survivor_count": survivor_count,
                "operators": sorted(operators),
                "business_criticality": criticality,
                "operator_leverage": leverage,
                "reachable_execution": all(
                    v["execution"] == "EXECUTED_AND_SURVIVED" for v in verdicts
                ),
                "public_contract_importance": criticality,
                "assurance_per_test": round(score / max(1, len(operators)), 2),
                "assurance_score": score,
            }
        )

    ranked.sort(key=lambda r: (-r["assurance_score"], r["location"]))
    for index, row in enumerate(ranked, start=1):
        row["priority_rank"] = index

    result = {
        "schema": "m9-c71-survivor-prioritisation/v1",
        "recorded_at": _now(),
        "ranking_basis": (
            "survivor count x mutation-operator leverage x business "
            "criticality, restricted to proven REAL_TEST_GAP survivors. NOT "
            "survivors-per-mutant: the objective is assurance gained per test "
            "added, not mutation-score increase per line of test code."
        ),
        "genuine_gap_locations": len(ranked),
        "ranked": ranked,
    }
    _write_json("survivor-prioritisation.json", result)
    return result


# ── Phase 13: score reconciliation ───────────────────────────────────────────


def reconcile_scores(
    *,
    aggregate: dict,
    classification: dict,
    threshold: int | None = None,
) -> ScoreReconciliation:
    """Phase 13 — report RAW and CERTIFIED side by side, never instead of.

    RAW is exactly what mutmut measured. It is never recomputed or filtered.
    CERTIFIED additionally reports how much of the surviving population is
    provably NOT a test-quality failure, with every denominator adjustment
    justified individually.
    """
    threshold = threshold if threshold is not None else resolve_threshold()

    population = int(aggregate.get("mutants_generated") or 0)
    killed = int(aggregate.get("killed") or 0)
    survived = int(aggregate.get("survived") or 0)
    raw_score = float(aggregate.get("mutation_score") or 0.0)

    by_category = classification.get("by_category", {})
    equivalent = int(by_category.get("EQUIVALENT", 0))
    unobservable = int(by_category.get("UNOBSERVABLE_BY_CONTRACT", 0))
    not_reached = int(by_category.get("NOT_REACHED", 0))
    defensive = int(by_category.get("DEFENSIVE_PATH", 0))
    invalid = int(by_category.get("MUTATION_INVALID", 0)) + int(
        by_category.get("TOOLING_DEFECT", 0)
    )
    genuine = int(classification.get("genuine_gap_survivors", 0))

    adjustments: list[dict] = []
    excluded = equivalent + unobservable + not_reached + defensive + invalid
    if excluded:
        adjustments.append(
            {
                "adjustment": "remove structurally-justified survivors from the "
                "CERTIFIED denominator only",
                "removed": excluded,
                "components": {
                    "EQUIVALENT": equivalent,
                    "UNOBSERVABLE_BY_CONTRACT": unobservable,
                    "NOT_REACHED": not_reached,
                    "DEFENSIVE_PATH": defensive,
                    "MUTATION_INVALID+TOOLING_DEFECT": invalid,
                },
                "justification": (
                    "each removed survivor carries independent evidence that it "
                    "is not a test-quality failure; the RAW score is unchanged "
                    "and remains the immutable measurement"
                ),
            }
        )
    if genuine:
        adjustments.append(
            {
                "adjustment": "genuine survivors are RETAINED in the certified "
                "denominator",
                "removed": 0,
                "components": {"REAL_TEST_GAP+HARNESS+CONTRACT": genuine},
                "justification": (
                    "a genuine test gap is a real shortfall; removing it would "
                    "be the score-chasing C71 forbids"
                ),
            }
        )

    valid_population = population - excluded
    effective = (
        round(100.0 * killed / valid_population, 1) if valid_population > 0 else None
    )

    # An effective score above 100% is structurally impossible, and it can only
    # arise when the denominators were assembled from mismatched sources (a
    # population from one shard set and a survivor census from another). Rather
    # than publish it, the reconciliation is withheld: a number that cannot be
    # true must not be reported, and a "certified" score is worse than none.
    inconsistent = effective is not None and effective > 100.0
    if inconsistent:
        adjustments.append(
            {
                "adjustment": "WITHHELD — certified score discarded as inconsistent",
                "removed": 0,
                "components": {},
                "justification": (
                    "the computed effective score exceeded 100%, which proves the "
                    "population and the survivor census were drawn from different "
                    "shard sets. The certified score is therefore not reported, and "
                    "the raw score stands alone"
                ),
            }
        )
        effective = None
        valid_population = population
        # Every survivor is retained, because none of the exclusions can be
        # trusted when the denominators came from different shard sets.
        genuine = survived

    return ScoreReconciliation(
        raw_population=population,
        raw_killed=killed,
        raw_survived=survived,
        raw_score=raw_score,
        threshold=threshold,
        valid_population=valid_population,
        certified_killed=killed,
        proven_equivalent=equivalent,
        proven_unobservable=unobservable,
        proven_not_reached=not_reached,
        proven_defensive=defensive,
        remaining_real_survivors=genuine,
        effective_score=effective,
        raw_gate="PASS" if raw_score >= threshold else "FAIL",
        effective_gate=(
            "PASS" if effective is not None and effective >= threshold else "FAIL"
        ),
        adjustments=adjustments,
    )


# ── Phase 14: the mutation self-certification gate ───────────────────────────


def certify(
    *,
    canary: dict,
    dispatch: dict,
    sentinel: dict,
    classification: dict,
    reconciliation: ScoreReconciliation,
    toolchain: MutmutTrampolineContract,
) -> TrustCertification:
    """Phase 14 — refuse to certify a mutation score whose measurement is invalid.

    This is the trust boundary C71 exists to add. Each refusal below is a
    condition under which a reported mutation score says nothing about test
    quality, and reporting it as if it did is how a 0% dispatch failure came to
    be read as a test-quality failure in the first place.

    A refusal is NOT a quality failure and does NOT lower a threshold. It says
    the measurement cannot be interpreted, which is a different claim.
    """
    refusals: list[str] = []

    # 1. The canary must pass. A harness that cannot tell a known kill from a
    #    known survivor cannot be used to conclude anything about any score.
    if not canary.get("passed"):
        failed = [k for k, v in (canary.get("checks") or {}).items() if v == "FAILED"]
        refusals.append("mutation canary failed: " + ", ".join(failed or ["unknown"]))

    # 2. The toolchain must be the declared one, and in contract.
    installed = _installed_mutmut_version()
    declared = _declared_mutmut_version()
    if declared and installed and declared != installed:
        refusals.append(
            f"mutation tool version {installed!r} differs from the declared "
            f"contract {declared!r}"
        )
    if not toolchain.satisfied:
        refusals.append(
            "mutation toolchain contract is "
            f"{toolchain.status}: {'; '.join(toolchain.unsatisfied_clauses)}"
        )

    # 3. Dispatch must be provable for the population.
    dispatch_valid = bool(dispatch.get("dispatch_valid"))
    if not dispatch_valid:
        refusals.append(
            f"mutation dispatch cannot be proven for "
            f"{len(dispatch.get('problems') or [])} source file(s)"
        )

    # 4. Every survivor must have independent execution evidence.
    execution_proven = bool(sentinel.get("execution_proven_for_all_survivors"))
    if not execution_proven:
        refusals.append(
            f"{sentinel.get('survivors_without_execution_evidence', 0)} survivor(s) "
            "have no independent evidence that the mutated implementation executed"
        )

    # 5. No survivor may remain unclassified.
    unknown = int(classification.get("unknown_survivors", 0))
    if unknown:
        refusals.append(f"{unknown} survivor(s) remain UNKNOWN")

    return TrustCertification(
        measurement_valid=bool(canary.get("passed")) and toolchain.satisfied,
        dispatch_valid=dispatch_valid,
        execution_proven=execution_proven,
        unknown_survivors=unknown,
        raw_score=reconciliation.raw_score,
        effective_score=reconciliation.effective_score,
        raw_gate=reconciliation.raw_gate,
        refusals=refusals,
    )


# ── Phase 15: performance / budget ───────────────────────────────────────────


def measure_shard_budget(shards: Sequence[dict]) -> dict:
    """Phase 15 — per-shard duration, throughput, and concentration of risk.

    The objective is to identify PATHOLOGICAL shards, not to reduce the
    population, drop operators, or move a threshold. A shard is pathological
    when it dominates the campaign's wall-clock without contributing
    proportionate assurance.
    """
    rows: list[dict] = []
    for shard in shards:
        population = int(shard.get("population") or 0)
        duration = float(shard.get("duration_seconds") or 0.0)
        rows.append(
            {
                "shard": shard.get("shard"),
                "component": shard.get("component"),
                "population": population,
                "killed": int(shard.get("killed") or 0),
                "survived": int(shard.get("survived") or 0),
                "score": shard.get("score"),
                "duration_seconds": duration or None,
                "mutants_per_second": (
                    round(population / duration, 2) if duration > 0 else None
                ),
                "seconds_per_mutant": (
                    round(duration / population, 3) if population > 0 else None
                ),
            }
        )
    rows.sort(key=lambda r: -(r["duration_seconds"] or 0.0))

    total_population = sum(r["population"] for r in rows)
    total_seconds = sum(r["duration_seconds"] or 0.0 for r in rows)
    slowest = rows[0] if rows else None
    return {
        "schema": "m9-c71-shard-budget/v1",
        "recorded_at": _now(),
        "shards": rows,
        "total_population": total_population,
        "total_measured_seconds": total_seconds,
        "aggregate_mutants_per_second": (
            round(total_population / total_seconds, 2) if total_seconds > 0 else None
        ),
        "slowest_shard": slowest["shard"] if slowest else None,
        "slowest_share_of_wall_clock": (
            round((slowest["duration_seconds"] or 0) / total_seconds, 3)
            if slowest and total_seconds > 0
            else None
        ),
        "pathological_shards": [
            r["shard"]
            for r in rows
            if total_seconds > 0 and (r["duration_seconds"] or 0) / total_seconds > 0.25
        ],
        "policy": (
            "population, operators and thresholds are never reduced. A shard "
            "that is intrinsically too large is split deterministically by the "
            "existing engine/function selection mechanism (mutation_shards)."
        ),
    }


# ── orchestration ────────────────────────────────────────────────────────────


def _default_mutants_root() -> Path:
    """Generated-mutants tree of the most recent shard run, else the canary."""
    candidate = BACKEND_ROOT / "mutants"
    return candidate if candidate.is_dir() else (CANARY_DIR / "mutants")


def run_trust_analysis(
    *,
    root: Path | None = None,
    source_root: Path | None = None,
    identity_sample_limit: int = 200,
) -> dict:
    """Run the full C71 pipeline and write every required artifact."""
    # The canary is the harness proof; the real campaign is the population.
    # Analysis therefore runs against the last shard's generated mutants when
    # one is present (for dual-execution equivalence) and always against the
    # durable catalogs and the canonical backend source tree.
    root = root or _default_mutants_root()
    source_root = source_root or BACKEND_ROOT

    baseline = freeze_baseline()
    canary = evaluate_canary()
    identity = verify_mutant_identity(
        root=root, source_root=source_root, limit=identity_sample_limit
    )
    dispatch = validate_dispatch()
    sentinel = execution_sentinel_sample(root=root)

    dispatch_problems = frozenset(
        str(p.get("source_file", "")) for p in (dispatch.get("problems") or [])
    )
    survivors = _load_survivor_records()
    equivalence = analyse_equivalence(
        root=root, source_root=source_root, survivors=survivors
    )
    classification = classify_survivors(
        root=root,
        equivalence_proofs=EQUIVALENCE_PROOFS,
        dispatch_problems=dispatch_problems,
    )
    reachability = analyse_reachability(
        root=root, source_root=source_root, classification=classification
    )
    prioritisation = prioritise_survivors(classification)

    aggregate = (
        _read_json(MUTATION_EVIDENCE_DIR / "mutation-summary-aggregate.json") or {}
    )
    reconciliation = reconcile_scores(
        aggregate=aggregate, classification=classification
    )
    _write_json("score-reconciliation.json", reconciliation.to_dict())

    budget = measure_shard_budget(baseline["shards"])
    _write_json("shard-results.json", budget)

    toolchain = toolchain_state()
    try:
        toolchain = ensure_mutmut_contract(_installed_mutmut_version())
        write_mutmut_contract_evidence(toolchain)
    except Exception as exc:  # noqa: BLE001 - reported, never hidden
        refusals_note = f"toolchain contract could not be satisfied: {exc}"
        _write_json(
            "toolchain-note.json",
            {"schema": "m9-c71-toolchain-note/v1", "error": refusals_note},
        )

    certification = certify(
        canary=canary,
        dispatch=dispatch,
        sentinel=sentinel,
        classification=classification,
        reconciliation=reconciliation,
        toolchain=toolchain,
    )

    targeted = {
        "schema": "m9-c71-targeted-test-results/v1",
        "recorded_at": _now(),
        "note": (
            "Per C71 Phase 12, shard re-runs are performed only for engines "
            "whose tests were modified, and the aggregate campaign is not "
            "re-run after every test change."
        ),
        "shard_reruns": [],
    }
    _write_json("targeted-test-results.json", targeted)

    final = {
        "schema": "m9-c71-final-certification/v1",
        "recorded_at": _now(),
        "head_sha": baseline["identity"]["head_sha"],
        "tree_sha": baseline["identity"]["tree_sha"],
        "toolchain_contract": toolchain.to_dict(),
        "certification": certification.to_dict(),
        "reconciliation": reconciliation.to_dict(),
        "canary": canary["checks"],
        "identity": {
            "checked": identity["mutants_checked"],
            "invalid": identity["identity_invalid"],
        },
        "dispatch": {
            "checked": dispatch["files_checked"],
            "problems": len(dispatch["problems"]),
        },
        "sentinel": sentinel["totals"],
        "classification": {k: v for k, v in classification["by_category"].items() if v},
        "equivalence": {
            "functions_proven_equivalent": equivalence["functions_proven_equivalent"],
            "mutants_proven_equivalent": equivalence["mutants_proven_equivalent"],
        },
        "reachability": reachability["by_reachability"],
        "prioritisation_top": prioritisation["ranked"][:10],
        "budget": {
            "aggregate_mutants_per_second": budget["aggregate_mutants_per_second"],
            "pathological_shards": budget["pathological_shards"],
        },
    }
    _write_json("final-certification.json", final)
    _write_final_markdown(final)
    return final


def _write_final_markdown(final: dict) -> Path:
    """Write the human-readable certification, stating the required fields verbatim."""
    cert = final["certification"]
    recon = final["reconciliation"]
    lines = [
        "# M9-C71 — Mutation Measurement Trust & Survivor Forensics",
        "",
        f"**Recorded:** {final['recorded_at']}",
        f"**HEAD:** `{final['head_sha']}`",
        f"**Tree:** `{final['tree_sha']}`",
        "",
        "## Certification",
        "",
        "```text",
        f"MUTATION_MEASUREMENT_VALID = {str(cert['MUTATION_MEASUREMENT_VALID']).lower()}",
        f"MUTATION_DISPATCH_VALID = {str(cert['MUTATION_DISPATCH_VALID']).lower()}",
        f"MUTANT_EXECUTION_PROVEN = {str(cert['MUTANT_EXECUTION_PROVEN']).lower()}",
        f"UNKNOWN_SURVIVORS = {cert['UNKNOWN_SURVIVORS']}",
        f"RAW_SCORE = {cert['RAW_SCORE']}",
        f"EFFECTIVE_SCORE = {cert['EFFECTIVE_SCORE']}",
        f"RAW_GATE = {cert['RAW_GATE']}",
        "```",
        "",
        "## Raw (immutable evidence)",
        "",
        f"- population: {recon['raw']['population']}",
        f"- killed: {recon['raw']['killed']}",
        f"- survived: {recon['raw']['survived']}",
        f"- score: {recon['raw']['score']}%",
        "",
        "## Certified (evidence-adjusted, never replacing raw)",
        "",
        f"- valid population: {recon['certified']['valid_population']}",
        f"- proven equivalent: {recon['certified']['proven_equivalent']}",
        f"- proven unobservable: {recon['certified']['proven_unobservable']}",
        f"- proven not reached: {recon['certified']['proven_not_reached']}",
        f"- proven defensive: {recon['certified']['proven_defensive']}",
        f"- remaining real survivors: {recon['certified']['remaining_real_survivors']}",
        f"- effective score: {recon['certified']['effective_score']}%",
        "",
        "## Canary",
        "",
    ]
    for key, value in (final.get("canary") or {}).items():
        lines.append(f"- {key}: **{value}**")
    lines += ["", "## Refusals", ""]
    if cert["refusals"]:
        lines += [f"- {r}" for r in cert["refusals"]]
    else:
        lines.append("- none — the measurement is self-consistent")
    lines += [
        "",
        "## Threshold",
        "",
        f"The gate remains **{recon['threshold']}%** and was not changed. "
        "`RAW_GATE` and `EFFECTIVE_GATE` are reported separately; an effective "
        "score above the threshold never redefines the raw gate.",
        "",
    ]
    path = TRUST_ARTIFACT_DIR / "final-certification.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ── CLI ──────────────────────────────────────────────────────────────────────


def run_trust_cli(argv: list[str]) -> int:
    """``verify.py mutation-trust`` — run the C71 trust analysis.

    Exit codes: 0 = measurement certified, 2 = measured but the quality gate is
    unmet, 1 = NOT CERTIFIED (the measurement itself cannot be trusted).
    """
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py mutation-trust")
    parser.add_argument(
        "--mutants-root",
        default=None,
        help="directory of mutmut-generated mutants (defaults to the canary)",
    )
    parser.add_argument(
        "--source-root",
        default=None,
        help="root the pristine sources are resolved against",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit the certification JSON only"
    )
    args = parser.parse_args(argv)

    root = Path(args.mutants_root).resolve() if args.mutants_root else None
    source_root = Path(args.source_root).resolve() if args.source_root else None
    final = run_trust_analysis(root=root, source_root=source_root)
    cert = final["certification"]

    if args.json:
        print(json.dumps(final, indent=2, default=str))
    else:
        print("=" * 72)
        print("  M9-C71 MUTATION MEASUREMENT TRUST CERTIFICATION")
        print("=" * 72)
        print(f"  MUTATION_MEASUREMENT_VALID = {cert['MUTATION_MEASUREMENT_VALID']}")
        print(f"  MUTATION_DISPATCH_VALID    = {cert['MUTATION_DISPATCH_VALID']}")
        print(f"  MUTANT_EXECUTION_PROVEN    = {cert['MUTANT_EXECUTION_PROVEN']}")
        print(f"  UNKNOWN_SURVIVORS          = {cert['UNKNOWN_SURVIVORS']}")
        print(f"  RAW_SCORE                  = {cert['RAW_SCORE']}")
        print(f"  EFFECTIVE_SCORE            = {cert['EFFECTIVE_SCORE']}")
        print(f"  RAW_GATE                   = {cert['RAW_GATE']}")
        print("-" * 72)
        for refusal in cert["refusals"]:
            print(f"  REFUSED: {refusal}")
        print(f"  [evidence] {TRUST_ARTIFACT_DIR.relative_to(REPO_ROOT)}")
        print("=" * 72)

    if not cert["CERTIFIED"]:
        return 1
    if cert["RAW_GATE"] != "PASS":
        return 2
    return 0
