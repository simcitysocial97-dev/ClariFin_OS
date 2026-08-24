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
    mutation_score: float | None = None
    # ── Meta ─────────────────────────────────────────────────────────────────
    mode: str = "full"  # full | smoke | target
    target: str | None = None
    duration_seconds: int = 0
    mutmut_rc: int | None = None
    error: str | None = None
    note: str = ""
    # ── Canonical selection provenance (C42.7) ───────────────────────────────
    selected_test_scope: str = ""  # engine-specific test paths actually used
    source_scope: str = ""  # source paths actually mutated
    selection_method: str = ""

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
            "selected_test_scope": self.selected_test_scope,
            "source_scope": self.source_scope,
            "selection_method": self.selection_method,
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


def reconcile_counts(counts: MutationCounts, generated: int | None = None) -> bool:
    """Arithmetic invariant: every generated mutant must be accounted for.

    generated == killed + survived + no_tests + timeout + suspicious + not_checked
    """
    if generated is not None and generated != counts.generated:
        return False
    return counts.generated >= 0


def compute_score(counts: MutationCounts) -> float | None:
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
) -> tuple[bool, bool, bool | None, str]:
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


# ─────────────────────────────────────────────────────────────────────────────
# M9-C42.7 — Canonical test-selection contract (single source of truth).
#
# One mapping defines, for every mutation target:
#   SOURCE MODULE(S)  -> the code under test
#   ENGINE            -> the logical engine name
#   TEST SELECTION    -> the engine-specific test directories / files
#   SELECTION METHOD  -> explicit pytest path selection (no silent full-suite
#                        fallback; mutmut 3.7.0 runs these via
#                        `pytest_add_cli_args_test_selection`).
#
# The mutation runner consumes ONLY this mapping to render the per-engine
# `[tool.mutmut]` configuration. Selection rules are never duplicated in bash,
# YAML, or ad-hoc commands.
# ─────────────────────────────────────────────────────────────────────────────

# P0 engines are ordered per M9-C42 decisions (credit_card first, then account).
P0_ENGINES = ("credit_card_engine", "account_engine")


@dataclass(frozen=True, slots=True)
class EngineSelection:
    """Canonical test-selection rule for one mutation target."""

    engine: str
    source_paths: tuple[str, ...]  # mutmut source_paths (relative to backend/)
    test_selection: tuple[str, ...]  # pytest path args (relative to backend/)
    also_copy: tuple[str, ...] = ("src",)  # mutmut also_copy (relative to backend/)
    tier: str = "P0"  # P0 | P1 | P2 — provenance only


# Single source of truth. Adding an engine == one entry here.
ENGINE_SELECTION: dict[str, EngineSelection] = {
    "credit_card_engine": EngineSelection(
        engine="credit_card_engine",
        source_paths=("src/engines/credit_card_engine",),
        test_selection=(
            "tests/unit/engines/credit_card",
            "tests/properties/credit_card_engine",
            "tests/capability/credit_cards",
        ),
        tier="P0",
    ),
    "account_engine": EngineSelection(
        engine="account_engine",
        source_paths=("src/engines/account_engine",),
        test_selection=(
            "tests/unit/engines/account",
            "tests/capability/account_management",
        ),
        tier="P0",
    ),
    "balance_engine": EngineSelection(
        engine="balance_engine",
        source_paths=("src/engines/balance_engine.py",),
        test_selection=("tests/unit/engines/balance_engine.py",),
        tier="P0",
    ),
    "ledger_audit_engine": EngineSelection(
        engine="ledger_audit_engine",
        source_paths=("src/engines/ledger_audit_engine.py",),
        test_selection=("tests/unit/engines/ledger_audit_engine.py",),
        tier="P0",
    ),
    "reconciliation_engine": EngineSelection(
        engine="reconciliation_engine",
        source_paths=("src/engines/reconciliation_engine.py",),
        test_selection=(
            "tests/unit/engines/reconciliation",
            "tests/properties/reconciliation",
            "tests/capability/reconciliation",
        ),
        also_copy=("src", "tests"),
        tier="P0",
    ),
    "loan_engine": EngineSelection(
        engine="loan_engine",
        source_paths=("src/engines/loan_engine",),
        test_selection=(
            "tests/unit/engines/loan",
            "tests/properties/loan_engine",
        ),
        tier="P1",
    ),
    "behaviour_engine": EngineSelection(
        engine="behaviour_engine",
        source_paths=("src/engines/behaviour_engine",),
        test_selection=(
            "tests/unit/engines/behaviour",
            "tests/properties/behaviour",
        ),
        tier="P1",
    ),
    # ── M9-C42.20 additions: eligible production logic previously outside the
    # pilot scope but certified for the full campaign (high-coverage, deterministic,
    # financially critical). transaction_intelligence / financial_intelligence are
    # deliberately WITHHELD until their test suites are strengthened (Phase 6 gate).
    "cashflow_engine": EngineSelection(
        engine="cashflow_engine",
        source_paths=("src/engines/cashflow_engine.py",),
        test_selection=("tests/properties/cashflow",),
        tier="P0",
    ),
    "financial_events": EngineSelection(
        engine="financial_events",
        source_paths=("src/engines/financial_events",),
        test_selection=(
            "tests/unit/engines/financial_events",
            "tests/properties/financial_events",
            "tests/capability/financial_events",
        ),
        tier="P1",
    ),
    "core_domain_money": EngineSelection(
        engine="core_domain_money",
        source_paths=("src/core/domain",),
        test_selection=(
            "tests/unit/test_money.py",
            "tests/properties/test_money_invariants.py",
            "tests/invariants/test_money.py",
        ),
        tier="P0",
    ),
    "common_calculations": EngineSelection(
        engine="common_calculations",
        source_paths=("src/common/calculations.py",),
        test_selection=("tests/unit/test_calculations.py",),
        tier="P0",
    ),
}

# Selection method is fixed and deterministic for the whole contract.
SELECTION_METHOD = "explicit-pytest-path (mutmut pytest_add_cli_args_test_selection)"

# The full authoritative scope = every engine's source + every engine's tests.
# Used only by the CI full campaign; never reduced and never a silent full-suite
# fallback (every path below is enumerated from ENGINE_SELECTION).
_FULL_SOURCE_PATHS = sorted(
    {p for s in ENGINE_SELECTION.values() for p in s.source_paths}
)
_FULL_TEST_SELECTION = sorted(
    {p for s in ENGINE_SELECTION.values() for p in s.test_selection}
)


def engine_names() -> list[str]:
    return sorted(ENGINE_SELECTION.keys())


def is_valid_engine(engine: str | None) -> bool:
    return engine in ENGINE_SELECTION


def render_mutmut_config_block(engine: str | None) -> str:
    """Render the `[tool.mutmut]` TOML block from the canonical mapping.

    `engine` is one key of ENGINE_SELECTION (per-engine bounded campaign) or
    None/"all"/"full" (authoritative full scope). The result is explicit and
    engine-aware: mutmut runs ONLY the listed test paths for the listed source
    paths — it can never silently fall back to the entire test suite.
    """
    if engine in (None, "all", "full"):
        source_paths = _FULL_SOURCE_PATHS
        test_selection = _FULL_TEST_SELECTION
        also_copy = ["src"]
        scope = "full (all engines)"
    else:
        sel = ENGINE_SELECTION[engine]
        source_paths = list(sel.source_paths)
        test_selection = list(sel.test_selection)
        also_copy = list(sel.also_copy)
        scope = engine

    src = ", ".join(f'"{p}"' for p in source_paths)
    tests = ",\n    ".join(f'"{p}"' for p in test_selection)
    copy = ", ".join(f'"{p}"' for p in also_copy)
    return (
        "# Rendered from canonical ENGINE_SELECTION (mutation_contract.py) — "
        "single source of truth.\n"
        f"# Scope: {scope}\n"
        f"# Selection method: {SELECTION_METHOD}\n"
        "[tool.mutmut]\n"
        f"source_paths = [{src}]\n"
        f"also_copy = [{copy}]\n"
        'runner = "python3 -m pytest"\n'
        "pytest_add_cli_args_test_selection = [\n"
        f"    {tests}\n"
        "]\n"
        "no_progress = true\n"
    )


def write_backend_mutmut_config(engine: str | None, backend_pyproject: Path) -> str:
    """Install the canonical per-engine/full `[tool.mutmut]` config into
    backend/pyproject.toml, preserving all other sections.

    Returns the original `[tool.mutmut]` block text so the caller can restore it.
    """
    import re

    text = backend_pyproject.read_text()
    block = render_mutmut_config_block(engine)
    # Match the [tool.mutmut] section up to the next top-level [section] or EOF.
    pattern = re.compile(r"\[tool\.mutmut\].*?(?=\n\[[^\s]|\Z)", re.S)
    if not pattern.search(text):
        raise RuntimeError("backend/pyproject.toml has no [tool.mutmut] section")
    new_text = pattern.sub(block.rstrip("\n") + "\n", text, count=1)
    backend_pyproject.write_text(new_text)
    return text


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
    mutmut_rc: int | None = None,
    mode: str = "full",
    target: str | None = None,
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
