# runtime/foundation/verification/mutation_contract.py
#
# M9-C42.5 — Canonical mutation result contract.
#
# Single source of truth for:
#   * the machine-readable mutation result schema,
#   * the arithmetic reconciliation invariant,
#   * the three-gate classification (Execution / Evidence / Quality).
#
# Pure logic only — no subprocess, no filesystem. Importable by unit tests
# (see runtime/tests/test_mutation_infra.py) and the runner.

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


# Canonical mutmut 3.7.0 status vocabulary -> our bucket.
_STATUS_MAP = {
    "killed": "killed",
    "survived": "survived",
    "no tests": "no_tests",
    "no test": "no_tests",
    "timeout": "timeout",
    "suspicious": "suspicious",
    "not checked": "not_checked",
}

# Statuses that represent a mutant that was actually executed and decided.
SCORED_STATUSES = ("killed", "survived", "timeout")

# A result line looks like:  "engines.foo.x_bar__mutmut_3: survived"
_RESULT_LINE_RE = re.compile(r"^\s*(?P<name>\S+)\s*:\s*(?P<status>.+?)\s*$")


@dataclass(frozen=True, slots=True)
class MutationCounts:
    killed: int = 0
    survived: int = 0
    no_tests: int = 0
    timeout: int = 0
    suspicious: int = 0
    not_checked: int = 0

    @property
    def generated(self) -> int:
        return (
            self.killed
            + self.survived
            + self.no_tests
            + self.timeout
            + self.suspicious
            + self.not_checked
        )

    def as_dict(self) -> dict:
        return {
            "killed": self.killed,
            "survived": self.survived,
            "no_tests": self.no_tests,
            "timeout": self.timeout,
            "suspicious": self.suspicious,
            "not_checked": self.not_checked,
            "mutants_generated": self.generated,
        }


@dataclass(frozen=True, slots=True)
class MutationResult:
    # ── Provenance ──────────────────────────────────────────────────────────
    run_id: str
    repository_sha: str
    tree_sha: str
    python_version: str
    pytest_version: str
    mutmut_version: str
    config_hash: str
    # ── Counts ──────────────────────────────────────────────────────────────
    killed: int = 0
    survived: int = 0
    no_tests: int = 0
    timeout: int = 0
    suspicious: int = 0
    not_checked: int = 0
    # ── Policy ──────────────────────────────────────────────────────────────
    threshold_percent: int = 80
    # ── Status flags (gates) ─────────────────────────────────────────────────
    execution_status: str = "UNKNOWN"  # PASS | INFRASTRUCTURE_FAILURE
    classification_status: str = "UNKNOWN"  # PASS | FAIL
    evidence_complete: bool = False
    # ── Derived ──────────────────────────────────────────────────────────────
    mutation_score: Optional[float] = None
    # ── Meta ─────────────────────────────────────────────────────────────────
    mode: str = "full"  # full | smoke | target
    target: Optional[str] = None
    duration_seconds: int = 0
    mutmut_rc: Optional[int] = None
    error: Optional[str] = None
    note: str = ""

    @property
    def mutants_generated(self) -> int:
        return (
            self.killed
            + self.survived
            + self.no_tests
            + self.timeout
            + self.suspicious
            + self.not_checked
        )

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "repository_sha": self.repository_sha,
            "tree_sha": self.tree_sha,
            "python_version": self.python_version,
            "pytest_version": self.pytest_version,
            "mutmut_version": self.mutmut_version,
            "config_hash": self.config_hash,
            "killed": self.killed,
            "survived": self.survived,
            "no_tests": self.no_tests,
            "timeout": self.timeout,
            "suspicious": self.suspicious,
            "not_checked": self.not_checked,
            "mutants_generated": self.mutants_generated,
            "mutation_score": self.mutation_score,
            "threshold_percent": self.threshold_percent,
            "execution_status": self.execution_status,
            "classification_status": self.classification_status,
            "evidence_complete": self.evidence_complete,
            "mode": self.mode,
            "target": self.target,
            "duration_seconds": self.duration_seconds,
            "mutmut_rc": self.mutmut_rc,
            "error": self.error,
            "note": self.note,
        }


def parse_mutmut_results(text: str) -> MutationCounts:
    """Parse `mutmut results --all true` output into buckets.

    Each relevant line: `<mutant_name>: <status>`.
    Unknown statuses are counted as `not_checked` (never silently dropped).
    """
    buckets = {
        "killed": 0,
        "survived": 0,
        "no_tests": 0,
        "timeout": 0,
        "suspicious": 0,
        "not_checked": 0,
    }
    for line in text.splitlines():
        m = _RESULT_LINE_RE.match(line)
        if not m:
            continue
        raw = m.group("status").strip().lower()
        bucket = _STATUS_MAP.get(raw)
        if bucket is None:
            bucket = "not_checked"
        buckets[bucket] += 1
    return MutationCounts(
        killed=buckets["killed"],
        survived=buckets["survived"],
        no_tests=buckets["no_tests"],
        timeout=buckets["timeout"],
        suspicious=buckets["suspicious"],
        not_checked=buckets["not_checked"],
    )


def reconcile_counts(counts: MutationCounts, generated: Optional[int] = None) -> bool:
    """Arithmetic invariant: every generated mutant must be accounted for.

    generated == killed + survived + no_tests + timeout + suspicious + not_checked
    """
    if generated is not None and generated != counts.generated:
        return False
    return counts.generated >= 0


def compute_score(counts: MutationCounts) -> Optional[float]:
    """Mutation score = killed / (killed + survived + timeout).

    Denominator excludes no_tests (no relevant test) and not_checked/suspicious
    (not evaluated). This matches the C42 baseline computation
    (4418 / (4418 + 4315 + 38) ≈ 50.6%).

    Returns None when no mutant was scored (cannot claim a score).
    """
    denominator = counts.killed + counts.survived + counts.timeout
    if denominator == 0:
        return None
    return round(counts.killed * 100.0 / denominator, 1)


def classify_gates(
    result: MutationResult,
) -> tuple[bool, bool, Optional[bool], str]:
    """Three-gate classification.

    Returns (gate_a_pass, gate_b_pass, gate_c_pass_or_none, quality_verdict).

    Gate A — Execution Integrity: did mutation testing actually execute?
    Gate B — Evidence Integrity: are all classifications accounted for?
    Gate C — Quality Threshold: only evaluated if A and B pass.

    On infrastructure failure (Gate A FAIL), Gate C is NOT evaluated and the
    returned quality verdict is explicit: "NOT EVALUABLE".
    """
    gate_a = result.execution_status == "PASS"
    gate_b = result.classification_status == "PASS" and result.evidence_complete

    if not gate_a:
        return False, gate_b, None, "NOT EVALUABLE (execution failure)"

    if not gate_b:
        return True, False, None, "NOT EVALUABLE (evidence incomplete)"

    score = result.mutation_score
    if score is None:
        return True, True, None, "NOT EVALUABLE (no scored mutants)"

    gate_c = score >= result.threshold_percent
    verdict = "PASS" if gate_c else "QUALITY FAIL"
    return True, True, gate_c, verdict


def build_infrastructure_failure(
    *,
    run_id: str,
    repository_sha: str,
    tree_sha: str,
    python_version: str,
    pytest_version: str,
    mutmut_version: str,
    config_hash: str,
    error: str,
    mutmut_rc: Optional[int] = None,
    mode: str = "full",
    target: Optional[str] = None,
) -> MutationResult:
    """Construct a result that NEVER pretends to have a mutation score."""
    return MutationResult(
        run_id=run_id,
        repository_sha=repository_sha,
        tree_sha=tree_sha,
        python_version=python_version,
        pytest_version=pytest_version,
        mutmut_version=mutmut_version,
        config_hash=config_hash,
        execution_status="INFRASTRUCTURE_FAILURE",
        classification_status="FAIL",
        evidence_complete=False,
        mutation_score=None,
        mode=mode,
        target=target,
        mutmut_rc=mutmut_rc,
        error=error,
        note="Mutation testing was not evaluated because mutation execution failed.",
    )
