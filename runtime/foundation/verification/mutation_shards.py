# runtime/foundation/verification/mutation_shards.py
#
# M9-C71 — Sharded mutation campaign contract + aggregate gate.
#
# WHY THIS EXISTS
# ---------------
# The authoritative mutation campaign spans every component in
# ``ENGINE_SELECTION`` (14 components, several thousand mutants). Running it as
# a single mutmut process cannot finish inside any CI job window: the previous
# single-job full campaign hit the 5400 s (90 min) wall and was cancelled
# (GitHub run 36233136018). A cancelled campaign produces no evidence, so the
# gate is permanently unsatisfiable.
#
# The fix is to make the campaign *sharded by construction*: one bounded shard
# per certified component, each independently measured, plus ONE aggregate gate
# that requires
#   * every shard in the certified population to be present,
#   * every shard to have completed execution integrity (Gate A),
#   * every shard to have a non-empty measured population (Gate B),
#   * the combined population to meet the existing campaign threshold.
#
# Nothing here lowers a threshold or invents a score. A missing, empty, or
# failed shard is an explicit failure, never a silent exclusion — that is the
# population-accounting property the single-process run could not express.
#
# The shard plan is derived from ``ENGINE_SELECTION`` (the canonical selection
# contract), so adding a component to the campaign automatically adds a shard.
# No shard list is duplicated in YAML, bash, or a workflow.

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.config_loader import get_threshold
from runtime.foundation.verification.env import REPO_ROOT
from runtime.foundation.verification.mutation_contract import (
    ENGINE_SELECTION,
    MutationCounts,
    MutationResult,
    compute_score,
    reconcile_counts,
)

BACKEND_ROOT = REPO_ROOT / "backend"


class MutmutShardError(RuntimeError):
    """Raised when a requested shard does not exist in the certified plan."""


#: Campaign mode recorded on the aggregate result.
AGGREGATE_MODE = "aggregate"

#: Threshold key for the aggregate gate. Reuses the existing, unchanged
#: full-campaign threshold — this module never introduces a new limit.
THRESHOLD_KEY = "full_campaign"

#: Default threshold if verification.yaml is unavailable. Matches the
#: dataclass default used everywhere else in the mutation contract.
DEFAULT_THRESHOLD = 80

#: Bound on a single shard's source bytes.
#:
#: Component-level sharding alone is NOT bounded: behaviour_engine alone carries
#: ~7 200 mutants (measured 2026-09-26), which needs roughly four hours on one
#: runner — far outside any CI job window, which is exactly how the previous
#: single-process campaign died (run 36233136018, cancelled at 91m45s with no
#: result). Shards are therefore packed by source size.
#:
#: The 24 KiB bound is derived from the one calibrated data point we have:
#: balance_engine (11.6 KiB) yields 285 mutants and measures in ~13 minutes, so
#: ~24 KiB is roughly 600 mutants — comfortably inside a 90-minute job with room
#: for the slowest per-mutant test selection. A single file larger than the cap
#: gets a shard of its own rather than being split, because mutmut's unit of
#: mutation is the file; oversize shards are visible in the plan and fail
#: explicitly (never silently) if they exhaust their budget.
SHARD_BYTE_CAP = 24 * 1024

#: M9-C72 — per-shard job timeout bounds.
#:
#: The workflow hard-coded 90 minutes for every shard, which with the slowest
#: shard measured at 693 s was 12% utilised. A budget that cannot fail usefully
#: is not a guard rail: a pathological shard would hold a parallel slot for 90
#: minutes and then report an ambiguous timeout. The timeout is therefore
#: derived from measured p95 (see ``recommended_shard_timeout_minutes``), and
#: these are only the bounds used when no measurement exists yet.
DEFAULT_SHARD_TIMEOUT_MINUTES = 90
MIN_SHARD_TIMEOUT_MINUTES = 5


@dataclass(frozen=True, slots=True)
class MutationShard:
    """One bounded, independently measurable unit of the mutation campaign.

    A shard is (component, subset-of-component-source-files). Every shard keeps
    the component's test selection and also-copy contract, so the shards of a
    component partition that component's mutation population exactly once: the
    union of a component's shards IS the component.
    """

    shard_id: str
    component: str
    tier: str
    files: tuple[str, ...]
    byte_size: int
    also_copy: tuple[str, ...]
    test_selection: tuple[str, ...]

    @property
    def is_whole_component(self) -> bool:
        return "-" not in self.shard_id

    def to_dict(self) -> dict:
        return {
            "shard_id": self.shard_id,
            "component": self.component,
            "tier": self.tier,
            "files": list(self.files),
            "byte_size": self.byte_size,
            "also_copy": list(self.also_copy),
            "test_selection": list(self.test_selection),
        }


@dataclass(frozen=True, slots=True)
class ShardVerdict:
    """Per-shard reconciliation outcome used to explain the aggregate decision."""

    name: str
    present: bool
    execution_status: str
    classification_status: str
    evidence_complete: bool
    mutants_generated: int
    killed: int
    survived: int
    no_tests: int
    timeout: int
    suspicious: int
    not_checked: int
    score: float | None
    threshold: int
    problem: str = ""

    @property
    def ok(self) -> bool:
        return not self.problem

    def to_dict(self) -> dict:
        data = {
            "name": self.name,
            "present": self.present,
            "execution_status": self.execution_status,
            "classification_status": self.classification_status,
            "evidence_complete": self.evidence_complete,
            "mutants_generated": self.mutants_generated,
            "killed": self.killed,
            "survived": self.survived,
            "no_tests": self.no_tests,
            "timeout": self.timeout,
            "suspicious": self.suspicious,
            "not_checked": self.not_checked,
            "score": self.score,
            "threshold": self.threshold,
            "problem": self.problem,
        }
        return data


@dataclass(frozen=True, slots=True)
class AggregateOutcome:
    """Durable aggregate-gate result for a sharded mutation campaign."""

    campaign_id: str
    mode: str
    threshold_percent: int
    expected_shards: list[str] = field(default_factory=list)
    shards: list[ShardVerdict] = field(default_factory=list)
    killed: int = 0
    survived: int = 0
    no_tests: int = 0
    timeout: int = 0
    suspicious: int = 0
    not_checked: int = 0
    mutants_generated: int = 0
    mutation_score: float | None = None
    execution_status: str = "PASS"
    classification_status: str = "PASS"
    evidence_complete: bool = True
    verdict: str = "PASS"
    failures: list[str] = field(default_factory=list)
    recorded_at: str = ""

    def to_dict(self) -> dict:
        return {
            "campaign_id": self.campaign_id,
            "mode": self.mode,
            "threshold_percent": self.threshold_percent,
            "expected_shards": list(self.expected_shards),
            "shards": [s.to_dict() for s in self.shards],
            "killed": self.killed,
            "survived": self.survived,
            "no_tests": self.no_tests,
            "timeout": self.timeout,
            "suspicious": self.suspicious,
            "not_checked": self.not_checked,
            "mutants_generated": self.mutants_generated,
            "mutation_score": self.mutation_score,
            "execution_status": self.execution_status,
            "classification_status": self.classification_status,
            "evidence_complete": self.evidence_complete,
            "verdict": self.verdict,
            "failures": list(self.failures),
            "recorded_at": self.recorded_at,
        }


def component_files(component: str) -> list[str]:
    """Every mutable Python file of a component, as backend-relative paths.

    Derived from the repo tree so the population is deterministic and needs no
    mutmut internals. ``__init__.py`` is retained: it is real, importable code
    in this layout and excluding it would silently shrink the population.
    """
    if component not in ENGINE_SELECTION:
        raise MutmutShardError(
            f"unknown mutation component {component!r}; known components: "
            f"{', '.join(sorted(ENGINE_SELECTION))}"
        )
    sel = ENGINE_SELECTION[component]
    out: list[str] = []
    for sp in sel.source_paths:
        p = BACKEND_ROOT / sp
        if p.is_dir():
            out += [str(f.relative_to(BACKEND_ROOT)) for f in sorted(p.rglob("*.py"))]
        elif p.is_file():
            out.append(sp)
    if not out:
        raise MutmutShardError(
            f"component {component!r} resolves to no mutable source file "
            f"(source_paths={list(sel.source_paths)})"
        )
    return sorted(set(out))


def pack_shards(component: str, byte_cap: int = SHARD_BYTE_CAP) -> list[MutationShard]:
    """Pack a component's files into bounded, deterministic shards.

    First-fit packing over files sorted largest-first. A component that fits in
    one group yields a single shard whose id IS the component name, so the
    common case reads exactly like the pre-sharding campaign.
    """
    if component not in ENGINE_SELECTION:
        raise MutmutShardError(
            f"unknown mutation component {component!r}; known components: "
            f"{', '.join(sorted(ENGINE_SELECTION))}"
        )
    sel = ENGINE_SELECTION[component]
    files = component_files(component)
    sizes = {f: (BACKEND_ROOT / f).stat().st_size for f in files}

    bins: list[list[str]] = []
    bin_sizes: list[int] = []
    for path in sorted(files, key=lambda f: (-sizes[f], f)):
        placed = False
        for i, current in enumerate(bin_sizes):
            if current + sizes[path] <= byte_cap:
                bins[i].append(path)
                bin_sizes[i] += sizes[path]
                placed = True
                break
        if not placed:
            bins.append([path])
            bin_sizes.append(sizes[path])

    bins = [sorted(b) for b in bins]
    if len(bins) == 1:
        ids = [component]
    else:
        width = max(2, len(str(len(bins) - 1)))
        ids = [f"{component}-{i:0{width}d}" for i in range(len(bins))]

    return [
        MutationShard(
            shard_id=sid,
            component=component,
            tier=sel.tier,
            files=tuple(bin_files),
            byte_size=bin_sizes[i],
            also_copy=tuple(sel.also_copy),
            test_selection=tuple(sel.test_selection),
        )
        for i, (sid, bin_files) in enumerate(zip(ids, bins, strict=True))
    ]


def shard_plan(byte_cap: int = SHARD_BYTE_CAP) -> list[MutationShard]:
    """The canonical campaign shard list, derived from ENGINE_SELECTions."""
    shards: list[MutationShard] = []
    for component in sorted(ENGINE_SELECTION):
        shards.extend(pack_shards(component, byte_cap))
    return shards


def shard_by_id(shard_id: str, byte_cap: int = SHARD_BYTE_CAP) -> MutationShard | None:
    for shard in shard_plan(byte_cap):
        if shard.shard_id == shard_id:
            return shard
    return None


def component_of(shard_id: str) -> str:
    """Component that owns a shard id (shard ids are component or component-NN)."""
    if shard_id in ENGINE_SELECTION:
        return shard_id
    head, _, tail = shard_id.rpartition("-")
    if head in ENGINE_SELECTION and tail.isdigit():
        return head
    raise MutmutShardError(f"unknown mutation shard id {shard_id!r}")


def shard_names(byte_cap: int = SHARD_BYTE_CAP) -> list[str]:
    return [s.shard_id for s in shard_plan(byte_cap)]


def resolve_threshold() -> int:
    return int(get_threshold("mutation_thresholds", THRESHOLD_KEY, DEFAULT_THRESHOLD))


def shard_summary_path(shard: str) -> Path:
    """Where a shard writes its own durable summary (relative to backend/)."""
    return (
        REPO_ROOT
        / "backend"
        / "tests"
        / "generated"
        / "mutation"
        / f"mutation-summary-{shard}.json"
    )


def shard_fingerprint(shard: MutationShard, mutmut_version: str = "") -> dict[str, str]:
    """The identity a shard's measurement depends on.

    A shard's verdict is reusable ONLY if everything it was measured against is
    unchanged: its source files, the tests that exercise it, the toolchain
    version, and the selection contract that decided what it contains.

    This is the difference between a cache that is provably valid and one that
    is merely trusted. A silent "assume it is still valid" fallback is exactly
    the C71 failure class — a number that looks authoritative and describes
    nothing.
    """
    return {
        "source_hash": _hash_paths([REPO_ROOT / "backend" / f for f in shard.files]),
        "test_hash": _hash_paths(
            [REPO_ROOT / "backend" / t for t in shard.test_selection]
        ),
        "mutmut_version": mutmut_version,
        "engine_selection_hash": _hash_paths(
            [REPO_ROOT / "runtime/foundation/verification/mutation_contract.py"]
        ),
    }


def _hash_paths(paths: Iterable[Path]) -> str:
    """Content hash over a set of files/directories, order-independent.

    Directories are walked recursively. A missing path contributes its name, so
    a deleted file changes the hash rather than being silently ignored.
    """
    digest = hashlib.sha256()
    for path in sorted(str(p) for p in paths):
        candidate = Path(path)
        digest.update(candidate.name.encode("utf-8"))
        if not candidate.exists():
            digest.update(b"<absent>")
            continue
        if candidate.is_dir():
            for child in sorted(candidate.rglob("*")):
                if child.is_file() and "__pycache__" not in child.parts:
                    digest.update(str(child.relative_to(candidate)).encode("utf-8"))
                    digest.update(hashlib.sha256(child.read_bytes()).digest())
        else:
            digest.update(hashlib.sha256(candidate.read_bytes()).digest())
    return "sha256:" + digest.hexdigest()


def evidence_registry_path() -> Path:
    """Where reusable per-shard evidence is persisted."""
    return REPO_ROOT / "backend" / "tests" / "generated" / "mutation" / "registry"


def read_cached_evidence(cache_dir: Path | None) -> tuple[dict[str, dict], list[str]]:
    """Load cached evidence for shards absent from this run, validating each.

    Returns ``(summaries, rejections)``. A cached entry whose fingerprint does
    NOT match current state is rejected and NAMED — the caller can then either
    re-measure it or fail loudly. It is never used, and never defaulted around.
    """
    if cache_dir is None:
        return {}, []
    try:
        version = _installed_mutmut_version()
    except Exception:
        version = ""

    plan = {s.shard_id: s for s in shard_plan()}
    summaries: dict[str, dict] = {}
    rejections: list[str] = []
    for path in sorted(Path(cache_dir).glob("mutation-summary-*.json")):
        shard = path.stem.removeprefix("mutation-summary-")
        if shard == AGGREGATE_MODE or shard not in plan:
            continue
        payload = _load_summary(path)
        if payload is None:
            rejections.append(f"{shard}: cached evidence is unreadable")
            continue
        stored = payload.get("fingerprint") or {}
        if not stored:
            rejections.append(
                f"{shard}: cached evidence carries no fingerprint, so its "
                "validity cannot be proven"
            )
            continue
        current = shard_fingerprint(plan[shard], version)
        differing = [k for k, v in current.items() if stored.get(k) != v]
        if differing:
            rejections.append(
                f"{shard}: cached evidence is stale ({', '.join(differing)} changed)"
            )
            continue
        summaries[shard] = payload
    return summaries, rejections


def record_evidence_fingerprint(payload: dict) -> dict:
    """Attach this shard's fingerprint to its own summary, if it can be derived.

    Called by the shard after it measures, so a later incremental run can prove
    the cached verdict still describes the same code. Returns the payload
    unchanged when the shard is unknown, so an unrecognised summary is still
    usable for reporting — it simply cannot be cached.
    """
    shard = payload.get("shard") or payload.get("name") or ""
    plan = {s.shard_id: s for s in shard_plan()}
    if shard not in plan:
        return payload
    try:
        version = _installed_mutmut_version()
    except Exception:
        version = ""
    payload["fingerprint"] = shard_fingerprint(plan[shard], version)
    return payload


def _installed_mutmut_version() -> str:
    import importlib.metadata as md

    return md.version("mutmut")


def aggregate_summary_path() -> Path:
    return (
        REPO_ROOT
        / "backend"
        / "tests"
        / "generated"
        / "mutation"
        / "mutation-summary-aggregate.json"
    )


def _display_path(path: Path) -> str:
    """Repo-relative path when possible, absolute otherwise.

    Evidence pointers must never raise just because the artifact landed outside
    the repository tree (relocated evidence directory, ad-hoc reconciliation
    scratch space).
    """
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _load_summary(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def collect_shard_summaries(
    shards: list[str],
    search_roots: list[Path] | None = None,
) -> dict[str, dict]:
    """Load every shard summary from *search_roots* (CI: downloaded artifacts).

    Search is recursive so a download layout change (per-artifact subdirectories
    instead of a flat merge) cannot silently turn into "no evidence found" — the
    aggregate gate would then fail for the wrong reason. A shard may appear in
    more than one artifact directory; the first readable copy wins.

    The result maps shard name -> summary payload and is intentionally allowed to
    be INCOMPLETE: the aggregate gate is what turns a gap into a failure.
    """
    roots = list(search_roots or [shard_summary_path("").parent])
    found: dict[str, dict] = {}
    wanted = set(shards)
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("mutation-summary-*.json")):
            name = path.stem.removeprefix("mutation-summary-")
            if name not in wanted or name in found or name == AGGREGATE_MODE:
                continue
            payload = _load_summary(path)
            if payload is not None:
                found[name] = payload
    return found


def _verdict_for(name: str, payload: dict | None, threshold: int) -> ShardVerdict:
    if payload is None:
        return ShardVerdict(
            name=name,
            present=False,
            execution_status="MISSING",
            classification_status="FAIL",
            evidence_complete=False,
            mutants_generated=0,
            killed=0,
            survived=0,
            no_tests=0,
            timeout=0,
            suspicious=0,
            not_checked=0,
            score=None,
            threshold=threshold,
            problem="shard produced no mutation summary — evidence missing",
        )

    counts = MutationCounts(
        killed=int(payload.get("killed") or 0),
        survived=int(payload.get("survived") or 0),
        no_tests=int(payload.get("no_tests") or 0),
        timeout=int(payload.get("timeout") or 0),
        suspicious=int(payload.get("suspicious") or 0),
        not_checked=int(payload.get("not_checked") or 0),
    )
    generated = counts.generated
    exec_status = str(payload.get("execution_status") or "UNKNOWN")
    class_status = str(payload.get("classification_status") or "UNKNOWN")
    evidence_complete = bool(payload.get("evidence_complete"))

    problem = ""
    if exec_status != "PASS":
        problem = (
            f"execution integrity failed ({exec_status}): "
            f"{payload.get('error') or 'no error detail recorded'}"
        )
    elif not reconcile_counts(counts):
        problem = "arithmetic reconciliation invariant failed"
    elif generated == 0:
        problem = "shard measured an empty mutation population"
    elif not evidence_complete:
        problem = "shard evidence incomplete"
    elif class_status != "PASS":
        problem = f"classification integrity failed ({class_status})"

    return ShardVerdict(
        name=name,
        present=True,
        execution_status=exec_status,
        classification_status=class_status,
        evidence_complete=evidence_complete,
        mutants_generated=generated,
        killed=counts.killed,
        survived=counts.survived,
        no_tests=counts.no_tests,
        timeout=counts.timeout,
        suspicious=counts.suspicious,
        not_checked=counts.not_checked,
        score=compute_score(counts),
        threshold=threshold,
        problem=problem,
    )


def aggregate(
    summaries: dict[str, dict],
    shards: list[str] | None = None,
    extra_failures: Sequence[str] | None = None,
) -> AggregateOutcome:
    """Reconcile shard evidence into one authoritative aggregate gate decision.

    ``extra_failures`` carries problems found OUTSIDE the shard summaries —
    today, cached evidence that could not be proven current. They are folded
    into the same failure list as a missing shard, because they are the same
    class of problem: the campaign is not evaluable, and saying so is the only
    honest outcome. A stale cache must never quietly pass the gate.
    """
    expected = list(shards if shards is not None else shard_names())
    threshold = resolve_threshold()

    verdicts = [_verdict_for(name, summaries.get(name), threshold) for name in expected]
    failures = [f"{v.name}: {v.problem}" for v in verdicts if v.problem]
    failures.extend(extra_failures or [])

    # Only shards that produced a *measured* population contribute to the score.
    # A failed shard is a failure of the campaign, not a silent exclusion.
    measured = [v for v in verdicts if v.ok]
    counts = MutationCounts(
        killed=sum(v.killed for v in measured),
        survived=sum(v.survived for v in measured),
        no_tests=sum(v.no_tests for v in measured),
        timeout=sum(v.timeout for v in measured),
        suspicious=sum(v.suspicious for v in measured),
        not_checked=sum(v.not_checked for v in measured),
    )
    invariant_ok = reconcile_counts(counts)
    score = compute_score(counts) if invariant_ok else None

    if not invariant_ok:
        execution_status = "INFRASTRUCTURE_FAILURE"
        verdict = "NOT EVALUABLE (aggregate arithmetic invariant failed)"
    elif failures:
        execution_status = "PASS"
        verdict = "NOT EVALUABLE (shard evidence incomplete)"
    elif score is None:
        execution_status = "PASS"
        verdict = "NOT EVALUABLE (no scored mutants)"
    elif score >= threshold:
        execution_status = "PASS"
        verdict = "PASS"
    else:
        execution_status = "PASS"
        verdict = "QUALITY FAIL"

    if execution_status != "PASS":
        failures.append("aggregate arithmetic invariant failed")

    return AggregateOutcome(
        campaign_id=f"mutation-campaign-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
        mode=AGGREGATE_MODE,
        threshold_percent=threshold,
        expected_shards=expected,
        shards=verdicts,
        killed=counts.killed,
        survived=counts.survived,
        no_tests=counts.no_tests,
        timeout=counts.timeout,
        suspicious=counts.suspicious,
        not_checked=counts.not_checked,
        mutants_generated=counts.generated,
        mutation_score=score,
        execution_status=execution_status,
        classification_status="PASS" if not failures else "FAIL",
        evidence_complete=not failures and counts.generated > 0,
        verdict=verdict,
        failures=failures,
        recorded_at=datetime.now(UTC).isoformat(),
    )


def as_mutation_result(outcome: AggregateOutcome) -> MutationResult:
    """Project the aggregate outcome onto the canonical MutationResult contract."""
    return MutationResult(
        run_id=outcome.campaign_id,
        repository_sha="",
        tree_sha="",
        python_version="",
        pytest_version="",
        mutmut_version="",
        config_hash="",
        killed=outcome.killed,
        survived=outcome.survived,
        no_tests=outcome.no_tests,
        timeout=outcome.timeout,
        suspicious=outcome.suspicious,
        not_checked=outcome.not_checked,
        threshold_percent=outcome.threshold_percent,
        execution_status=outcome.execution_status,
        classification_status=outcome.classification_status,
        evidence_complete=outcome.evidence_complete,
        mutation_score=outcome.mutation_score,
        mode=AGGREGATE_MODE,
        target=None,
        note=(
            f"Aggregated {len(outcome.shards)} shard(s) across the certified "
            f"component population; verdict={outcome.verdict}"
        ),
        selection_method="sharded-aggregate (one bounded shard per certified component)",
        affected_engines=outcome.expected_shards,
        toolchain_contract="sharded-aggregate",
    )


def write_aggregate(outcome: AggregateOutcome) -> Path:
    out = aggregate_summary_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(outcome.to_dict(), indent=2) + "\n", encoding="utf-8")
    result_path = aggregate_summary_path().with_name(
        "mutation-summary-aggregate-result.json"
    )
    result_path.write_text(
        json.dumps(as_mutation_result(outcome).to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    return out


def format_report(outcome: AggregateOutcome) -> str:
    lines = [
        "=" * 72,
        "  M9-C71 SHARDED MUTATION AGGREGATE GATE",
        "=" * 72,
        f"  Campaign         : {outcome.campaign_id}",
        f"  Shards expected  : {len(outcome.expected_shards)}",
        f"  Shards measured  : {sum(1 for s in outcome.shards if s.ok)}",
        "-" * 72,
    ]
    for v in outcome.shards:
        score = "N/A" if v.score is None else f"{v.score}%"
        flag = "OK " if v.ok else "FAIL"
        lines.append(
            f"  [{flag}] {v.name:<28} gen={v.mutants_generated:<5} "
            f"killed={v.killed:<5} survived={v.survived:<5} score={score}"
        )
    lines += [
        "-" * 72,
        f"  Combined killed  : {outcome.killed}",
        f"  Combined survived: {outcome.survived}",
        f"  Total generated  : {outcome.mutants_generated}",
        f"  Aggregate score  : {outcome.mutation_score}",
        f"  Threshold        : {outcome.threshold_percent}%",
        f"  Verdict          : {outcome.verdict}",
        "=" * 72,
    ]
    if outcome.failures:
        lines.append("  Failures:")
        for failure in outcome.failures:
            lines.append(f"    - {failure}")
    return "\n".join(lines)


def _expected_from_env() -> list[str] | None:
    """Resolve the expected shard set from the campaign scope environment.

    ``MUTATION_COMPONENT`` mirrors the workflow dispatch input: empty/"all"
    means the full certified population; a component name means a targeted
    campaign whose single shard is still gated at the full-campaign threshold.
    """
    import os

    requested = os.environ.get("MUTATION_COMPONENT", "").strip()
    if requested in ("", "all"):
        return None
    # A targeted campaign is the full shard set of that one component, and every
    # one of those shards is still gated at the full-campaign threshold.
    return [s.shard_id for s in pack_shards(requested)]


def _dirname_prefix(path: str) -> str:
    """The directory containing *path*, as a prefix ending in ``/``.

    Used to widen affected-shard matching from exact files to the files'
    directories, so a new, deleted or renamed file still selects the shard that
    would own it. Matching exact paths alone turns all three into a silent
    no-op.
    """
    head, sep, _tail = path.rpartition("/")
    return head + sep if sep else ""


def normalise_repo_path(path: str) -> str:
    """Convert a repo-relative git path into the backend-relative form shards use.

    Shard file and test-selection paths are backend-relative
    (``src/engines/loan_engine/x.py``) because that is how mutmut and pytest
    are invoked, while ``git diff`` reports repo-relative paths
    (``backend/src/engines/loan_engine/x.py``).

    Comparing the two forms directly matches nothing, which would make every
    diff look empty and an incremental gate would silently measure nothing at
    all — a far worse failure than measuring too much, because it looks like a
    successful no-op.
    """
    normalised = path.replace("\\", "/").lstrip("./")
    if normalised.startswith("backend/"):
        normalised = normalised[len("backend/") :]
    return normalised


def recommended_shard_timeout_minutes(shards: list[MutationShard] | None = None) -> int:
    """Derive a per-shard job timeout from measured durations.

    The workflow previously hard-coded ``timeout-minutes: 90`` for every shard.
    With the slowest shard measured at 693 s that budget was 12% utilised, so
    the setting could not fail usefully: a genuinely pathological shard held a
    parallel slot for 90 minutes and then reported an ambiguous timeout rather
    than a fast, legible failure.

    A timeout should be a bound on *observed* behaviour plus headroom, so a
    shard that suddenly takes 5x its normal time fails visibly and promptly.
    Measured p95 x 2, floored at 5 minutes, is that bound. If no measurements
    exist yet the flat default is returned unchanged, so a first run behaves
    exactly as before.
    """
    from runtime.foundation.verification.mutation_trust import (
        MUTATION_EVIDENCE_DIR,
    )

    durations: list[float] = []
    for path in sorted(MUTATION_EVIDENCE_DIR.glob("mutation-summary-*.json")):
        payload = _load_summary(path)
        if not payload:
            continue
        value = payload.get("duration_seconds")
        if isinstance(value, (int, float)) and value > 0:
            durations.append(float(value))

    if not durations:
        return DEFAULT_SHARD_TIMEOUT_MINUTES

    durations.sort()
    # Nearest-rank p95, which needs no interpolation and is well defined for
    # the small sample a fresh campaign produces.
    index = max(0, min(len(durations) - 1, int(0.95 * len(durations)) - 1))
    p95 = durations[index]
    minutes = math.ceil(p95 * 2 / 60)
    return max(MIN_SHARD_TIMEOUT_MINUTES, minutes)


def affected_shards(
    changed_paths: Iterable[str],
    shards: list[MutationShard] | None = None,
) -> tuple[list[MutationShard], dict[str, list[str]]]:
    """Return the shards a set of changed paths can possibly affect.

    Two independent reasons a shard must be re-measured, and conflating them is
    how an incremental gate silently stops killing mutants:

    1. **Its source changed.** A mutation lives in a source file, so a changed
       source file can only change mutants in shards that own it.
    2. **Its tests changed.** A new or edited test can kill a mutant in ANY
       shard, not only the one matching the edited test's directory. Scoping
       test changes by source file would let a new test in
       ``tests/unit/engines/loan_engine`` pass CI while the mutants it was
       written to kill were never re-measured.

    Therefore ANY change under a shard's ``test_selection`` re-measures that
    shard, and a change to a source file re-measures the shards owning it.

    Returns ``(affected, reasons)`` where ``reasons`` maps shard id to the
    changed paths that selected it, so the workflow summary can explain *why*
    each shard ran rather than presenting an opaque list.
    """
    plan = shards if shards is not None else shard_plan()
    # A directory is safe to widen to only when it belongs to ONE component.
    # Several single-file shards (balance_engine, cashflow_engine,
    # ledger_audit_engine, reconciliation_engine) live directly in
    # `src/engines/`, so widening unconditionally made a change to one engine
    # select all of them.
    owners: dict[str, set[str]] = {}
    for shard in plan:
        for f in shard.files:
            owners.setdefault(_dirname_prefix(f), set()).add(shard.component)
    exclusive_dirs = {
        prefix for prefix, components in owners.items() if len(components) == 1
    }

    reasons: dict[str, list[str]] = {}
    raw_paths = [p.replace("\\", "/").lstrip("./") for p in changed_paths]
    pairs = list(
        zip(raw_paths, (normalise_repo_path(p) for p in changed_paths), strict=True)
    )
    for shard in plan:
        exact = set(shard.files)
        widened = {
            _dirname_prefix(f)
            for f in shard.files
            if _dirname_prefix(f) in exclusive_dirs
        }
        matched = [
            raw
            for raw, norm in pairs
            if norm in exact
            or any(norm.startswith(prefix) for prefix in widened if prefix)
            or any(
                norm == t.rstrip("/") or norm.startswith(t.rstrip("/") + "/")
                for t in shard.test_selection
            )
        ]
        if matched:
            reasons[shard.shard_id] = sorted(set(matched))

    affected = [s for s in plan if s.shard_id in reasons]
    return affected, reasons


def changed_paths_between(base: str, head: str = "HEAD") -> list[str]:
    """List files changed between two revisions, repo-relative.

    Uses a three-dot diff so the comparison is against the merge base rather
    than the raw base tip, which is what a pull request actually means by
    "what changed". Returns an empty list when git cannot answer (shallow
    clone, bad ref), which callers must treat as "assume everything changed"
    rather than "assume nothing changed".
    """
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...{head}"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if out.returncode != 0:
        return []
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def run_plan_cli(argv: list[str]) -> int:
    """``verify.py mutation-plan`` — emit the campaign shard matrix as JSON.

    The GitHub Actions job graph cannot read Python, so the matrix is generated
    once from ENGINE_SELECTION by this entrypoint and consumed via
    ``fromJson(needs.<job>.outputs.matrix)``. The shard list therefore has a
    single source of truth and can never drift from the selection contract.

    ``--component`` (or the ``MUTATION_COMPONENT`` environment variable used by
    the workflow dispatch input) restricts the campaign to one component, which
    is how a targeted, single-engine campaign is requested.

    ``--affected-from <ref>`` emits only the shards a diff can affect, which is
    how a pull request avoids re-measuring all 26 shards. It also emits
    ``--changed`` / ``--reasons`` so the job summary can explain why each shard
    was selected, and ``--safe`` so a caller can tell an empty affected set
    (genuinely nothing to measure) apart from a failed diff lookup (measure
    everything). A diff that cannot be computed must never be read as "no
    changes", because that would silently skip the entire campaign.
    """
    import argparse
    import os

    parser = argparse.ArgumentParser(prog="verify.py mutation-plan")
    parser.add_argument(
        "--affected-from",
        default="",
        help="emit only shards affected by the diff against this ref",
    )
    parser.add_argument(
        "--always",
        action="append",
        default=[],
        help="shard id to always include, regardless of the diff "
        "(repeatable; use for cross-cutting changes)",
    )
    parser.add_argument(
        "--timeout-minutes-per-shard",
        type=int,
        default=0,
        help="override the per-shard job timeout emitted for the matrix",
    )
    args = parser.parse_args(argv)

    requested = os.environ.get("MUTATION_COMPONENT", "").strip()
    if requested in ("", "all"):
        shards = shard_plan()
    else:
        if requested not in ENGINE_SELECTION:
            print(
                f"unknown mutation component {requested!r}; "
                f"known components: {', '.join(sorted(ENGINE_SELECTION))}",
                file=sys.stderr,
            )
            return 1
        shards = pack_shards(requested)

    reasons: dict[str, list[str]] = {}
    safe = True
    if args.affected_from:
        changed = changed_paths_between(args.affected_from)
        if not changed:
            # A failed diff lookup is indistinguishable from an empty diff, and
            # the safe reading is "everything may have changed".
            safe = False
            reasons = {
                s.shard_id: ["<diff unavailable: measuring all>"] for s in shards
            }
            shards = list(shards)
        else:
            affected, reasons = affected_shards(changed, shards)
            forced = {sid: reasons.get(sid, ["<forced>"]) for sid in args.always}
            reasons.update(forced)
            shards = affected + [s for s in shards if s.shard_id in forced]

    timeout = args.timeout_minutes_per_shard or recommended_shard_timeout_minutes(
        shards
    )

    matrix = plan_payload(shards, reasons=reasons, diff_safe=safe, timeout=timeout)
    print(json.dumps(matrix, indent=2))
    return 0


def plan_payload(
    shards: list[MutationShard] | None = None,
    *,
    reasons: dict[str, list[str]] | None = None,
    diff_safe: bool = True,
    timeout: int = 0,
) -> dict[str, Any]:
    """Build the campaign plan document ``verify.py mutation-plan`` prints.

    The document is richer than a GitHub matrix on purpose: ``shard_count``,
    ``total_shards``, ``diff_safe`` and ``recommended_timeout_minutes`` are what
    the run summary reports, and the workflow reads all of them with ``jq``.

    It is NOT matrix-shaped, and that distinction is load-bearing. GitHub reads
    every top-level key of a ``strategy.matrix`` other than ``include``/
    ``exclude`` as a dimension whose value must be a list, so handing this
    document to ``fromJson`` verbatim is rejected before a runner is ever
    involved. The workflow narrows it to ``include`` (mutation.yml, the
    ``MATRIX_JSON`` assignment) and reads the rest from this same document.
    """
    reasons = reasons or {}
    shards = shard_plan() if shards is None else shards
    return {
        "include": [
            {
                "shard": s.shard_id,
                "component": s.component,
                "tier": s.tier,
                "byte_size": s.byte_size,
                "file_count": len(s.files),
                "source_paths": " ".join(s.files),
                # M10-R3 (L8): a SCALAR, joined for the same reason `source_paths`
                # is. A GitHub Actions matrix cell must be a scalar — a list here is
                # rejected or silently stringified depending on the runner path, and
                # which one you got is not something to discover in production.
                #
                # This was a live runtime defect, invisible until the hand-written
                # workflow projection was removed: the projection happened to drop
                # `reasons`, so no matrix ever carried it. `test_m9_c71_mutation_
                # campaign::test_the_published_matrix_carries_nothing_but_include`
                # asserts the scalar invariant and caught it the moment the duplication
                # stopped masking it.
                "reasons": ", ".join(reasons.get(s.shard_id, [])),
            }
            for s in shards
        ],
        "shard_count": len(shards),
        "total_shards": len(shard_plan()),
        "diff_safe": diff_safe,
        "recommended_timeout_minutes": timeout
        or recommended_shard_timeout_minutes(shards),
    }


def run_aggregate_cli(argv: list[str]) -> int:
    """``verify.py mutation-aggregate`` entrypoint.

    Exit codes: 0 = gate satisfied, 2 = measured but below threshold,
    1 = not evaluable (missing/empty/failed shard or invariant failure).
    """
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py mutation-aggregate")
    parser.add_argument(
        "--shards-dir",
        action="append",
        default=[],
        help="directory containing mutation-summary-<shard>.json files "
        "(repeatable; defaults to the canonical generated directory)",
    )
    parser.add_argument(
        "--shard",
        action="append",
        default=[],
        help="restrict/define the expected shard set (repeatable; "
        "defaults to every certified component)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    parser.add_argument(
        "--cache-dir",
        default="",
        help="directory of previously recorded per-shard evidence; entries "
        "whose fingerprint no longer matches current state are rejected and "
        "named, never used",
    )
    args = parser.parse_args(argv)

    roots = [Path(d).resolve() for d in args.shards_dir]
    # The expected population is the SAME population the plan emitted, so a
    # shard can never be quietly dropped between planning and aggregation.
    expected = args.shard or _expected_from_env()
    if not expected:
        expected = shard_names()

    summaries = collect_shard_summaries(expected, roots or None)

    # M9-C72: an incremental run measures only some shards, so the rest are
    # supplied from a validated cache. A cache entry that cannot be proven
    # current is reported as a reconciliation failure, so a stale cache makes
    # the gate FAIL rather than quietly pass on evidence that no longer
    # describes the code.
    rejections: list[str] = []
    if args.cache_dir:
        cached, rejections = read_cached_evidence(Path(args.cache_dir).resolve())
        reused: list[str] = []
        for shard, payload in cached.items():
            if shard in summaries:
                continue
            summaries[shard] = payload
            reused.append(shard)
        if reused:
            print(
                f"  reused {len(reused)} cached shard verdict(s): "
                f"{', '.join(sorted(reused))}",
                file=sys.stderr,
            )

    outcome = aggregate(summaries, expected, extra_failures=rejections)
    write_aggregate(outcome)

    if args.json:
        print(json.dumps(outcome.to_dict(), indent=2))
    else:
        print(format_report(outcome))
        print()
        print(f"  [evidence] {_display_path(aggregate_summary_path())}")

    if outcome.execution_status != "PASS" or not outcome.evidence_complete:
        return 1
    if (
        outcome.mutation_score is None
        or outcome.mutation_score < outcome.threshold_percent
    ):
        return 2
    return 0
