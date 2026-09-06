# runtime/foundation/verification/mutation_execution/forensics.py
#
# M9-C44.0 — Mutation Failure Forensics Inventory.
#
# Systematic forensic analysis of ALL mutation failures encountered to date.
# Every failure classified by:
#   failure -> execution stage -> owning layer -> reproducibility -> root cause -> workaround -> architectural solution
#
# Produces: runtime/generated/m9-c44/mutation-failure-forensics.json

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GENERATED_C44 = REPO_ROOT / "runtime" / "generated" / "m9-c44"


class ExecutionStage(str, Enum):
    ENVIRONMENT_SETUP = "environment_setup"
    BASELINE_VERIFICATION = "baseline_verification"
    MUTATION_DISCOVERY = "mutation_discovery"
    MUTATION_GENERATION = "mutation_generation"
    TEST_EXECUTION = "test_execution"
    RESULT_COLLECTION = "result_collection"
    EVIDENCE_RECONCILIATION = "evidence_reconciliation"
    SOURCE_RESTORE = "source_restore"
    CLEANUP = "cleanup"
    CI_ORCHESTRATION = "ci_orchestration"


class OwningLayer(str, Enum):
    CLARIFIN_OS = "clarinfin_os"
    MUTMUT = "mutmut"
    ENVIRONMENT = "environment"
    PYTEST = "pytest"
    TEST_SUITE = "test_suite"
    CONFIGURATION = "configuration"
    PROCESS_ISOLATION = "process_isolation"
    CACHE = "cache"
    FILESYSTEM = "filesystem"
    CONCURRENCY = "concurrency"
    CI = "ci"
    EVIDENCE_RECONCILIATION = "evidence_reconciliation"


class Reproducibility(str, Enum):
    ALWAYS = "always"
    OFTEN = "often"
    INTERMITTENT = "intermittent"
    RARE = "rare"
    ONE_TIME = "one_time"
    UNKNOWN = "unknown"


class DefectOrigin(str, Enum):
    CLARIFIN_OS = "clarinfin_os"
    MUTMUT = "mutmut"
    ENVIRONMENT = "environment"
    PYTEST = "pytest"
    TEST_SUITE = "test_suite"
    CONFIGURATION = "configuration"
    PROCESS_ISOLATION = "process_isolation"
    CACHE = "cache"
    FILESYSTEM = "filesystem"
    CONCURRENCY = "concurrency"
    CI = "ci"
    EVIDENCE_RECONCILIATION = "evidence_reconciliation"


@dataclass
class FailureRecord:
    failure_id: str
    stage: str
    owning_layer: str
    reproducibility: str
    root_cause: str
    symptoms: list[str]
    workaround: str
    architectural_solution: str
    first_seen: str
    last_seen: str
    resolved: bool = False
    resolution_commit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Forensic inventory — compiled from historical records (C42.x commits, logs,
# run failures, CI reports). Each entry is derived from observed behaviour.
# ---------------------------------------------------------------------------

_FORENSIC_RECORDS: list[dict[str, Any]] = [
    {
        "failure_id": "F001",
        "stage": ExecutionStage.MUTATION_DISCOVERY.value,
        "owning_layer": OwningLayer.MUTMUT.value,
        "reproducibility": Reproducibility.OFTEN.value,
        "root_cause": (
            "mutmut discovers mutations by instrumenting AST at function level. "
            "When a source file has syntax that mutmut's libcst-based mutator cannot "
            "handle (e.g. certain f-string patterns, complex comprehensions), the "
            "mutation is silently dropped with no error raised. This leads to an "
            "undercount of generated mutants."
        ),
        "symptoms": [
            "mutants_generated < expected for a component",
            "mutmut run exits with RC=0 but count seems low",
            "no explicit error in stdout/stderr about skipped mutations",
        ],
        "workaround": "Cross-reference mutmut-generated population count with static-analysis estimate; flag discrepancies as suspect.",
        "architectural_solution": (
            "M44.17: adapter must track discovery coverage vs static analysis estimate. "
            "Canonical candidate list is built by ClariFin_OS; mutmut is consulted only "
            "for application. Discovery discrepancy becomes an infrastructure fact, not a silent gap."
        ),
        "first_seen": "2026-08-10T00:00:00Z",
        "last_seen": "2026-08-29T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F002",
        "stage": ExecutionStage.TEST_EXECUTION.value,
        "owning_layer": OwningLayer.PROCESS_ISOLATION.value,
        "reproducibility": Reproducibility.ALWAYS.value,
        "root_cause": (
            "mutmut changes working directory to `mutants/` before invoking pytest. "
            "Test fixtures that rely on relative paths (e.g. `tests/fixtures/database`) "
            "fail to import because sys.path is not set correctly from the new cwd. "
            "This causes spurious EXECUTION_ERROR results instead of genuine kills/survives."
        ),
        "symptoms": [
            "Import errors in test fixtures when running under mutmut",
            "Tests that pass individually fail when invoked via mutmut",
            "PYTHONPATH not propagating to mutants/cwd context",
        ],
        "workaround": "Set PYTHONPATH explicitly in runner (done in mutation_runner.py). Verify fixture imports work from `mutants/` cwd.",
        "architectural_solution": (
            "M44.7: each execution gets its own isolated workspace with explicit PYTHONPATH, "
            "working directory, and environment variables. The adapter verifies import-path "
            "correctness before counting a result."
        ),
        "first_seen": "2026-08-12T00:00:00Z",
        "last_seen": "2026-08-28T00:00:00Z",
        "resolved": True,
        "resolution_commit": "f92363b9",
    },
    {
        "failure_id": "F003",
        "stage": ExecutionStage.RESULT_COLLECTION.value,
        "owning_layer": OwningLayer.CACHE.value,
        "reproducibility": Reproducibility.INTERMITTENT.value,
        "root_cause": (
            "mutmut stores per-mutant exit codes in `.mutmut-cache/mutants/<path>.meta`. "
            "If a prior campaign used a different source scope or mutmut version, stale "
            "meta files can be reused without re-execution, producing results that do not "
            "reflect the current source revision. Additionally, the provenance.json check "
            "in mutation_runner.py validates repository_sha/config_hash/mutmut_version, "
            "but does NOT validate source-file hashes, so a source change within the same "
            "repo SHA (e.g. dirty tree) can reuse stale cache."
        ),
        "symptoms": [
            "Scores appear unchanged despite source modifications",
            "Different mutmut_version string in .mutmut-cache leads to cache rejection even when functionally compatible",
            "CI and local produce different counts because of cached results",
        ],
        "workaround": "Use `--no-cache` flag; clear `.mutmut-cache` before full campaigns. Cache provenance check for repo_sha/config_hash/mutmut_version.",
        "architectural_solution": (
            "M44.12: ClariFin_OS owns its own evidence cache keyed by canonical mutant ID "
            "+ source-file-hash fingerprint + test-selection fingerprint. Stale mutmut cache "
            "is never the source of truth; it is an optimization hint only."
        ),
        "first_seen": "2026-08-14T00:00:00Z",
        "last_seen": "2026-08-27T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F004",
        "stage": ExecutionStage.SOURCE_RESTORE.value,
        "owning_layer": OwningLayer.CLARIFIN_OS.value,
        "reproducibility": Reproducibility.OFTEN.value,
        "root_cause": (
            "After mutation runs, `git checkout -- <files>` restores mutated source. "
            "However, mutmut also generates `.pyc` files, `__pycache__` directories, "
            "and sometimes modifies `mutants/` tree content that is tracked. If restoration "
            "is interrupted (SIGTERM during mutate->run cycle), leftover mutation artifacts "
            "remain in the working tree. The `_MutationSafety` class captures pre/post hashes "
            "but the atexit handler is the sole restoration path — signal handlers re-raise "
            "after restoration, which can still leave partial state if the process is killed "
            "between restore and re-raise."
        ),
        "symptoms": [
            "Dirty worktree detected after mutation run even though source should be restored",
            "Pre-existing edits lost if they coincided with mutation-modified files",
            "Residual `.pyc`/`mutants/` artifacts after interrupted runs",
        ],
        "workaround": "Always run `git checkout -- backend/src` manually after an interrupted run. Use `--allow-dirty` for dev worktrees.",
        "architectural_solution": (
            "M44.6: Isolated workspace per campaign. Source is never mutated in-place in the "
            "canonical repository tree during normal operation; mutations happen in disposable "
            "workspace copies. The safety-net `git checkout` becomes a fallback, not the primary mechanism."
        ),
        "first_seen": "2026-08-11T00:00:00Z",
        "last_seen": "2026-08-29T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F005",
        "stage": ExecutionStage.TEST_EXECUTION.value,
        "owning_layer": OwningLayer.CONFIGURATION.value,
        "reproducibility": Reproducibility.ALWAYS.value,
        "root_cause": (
            "The `[tool.mutmut]` section in `backend/pyproject.toml` is rewritten before "
            "each campaign with engine-specific `source_paths`, `also_copy`, and "
            "`pytest_add_cli_args_test_selection`. If the rewrite fails mid-stream or the "
            "restoration is skipped (bug in try/finally ordering), subsequent campaigns or "
            "non-mutation pytest invocations see the wrong configuration. The R2 fix in "
            "mutation_runner.py moved evidence collection BEFORE config restore, but edge "
            "cases remain when `mutmut results` itself triggers a config read."
        ),
        "symptoms": [
            "Wrong engine tests running during mutation",
            "Non-mutation pytest commands failing after a mutation run",
            "Config written but not restored on exception paths",
        ],
        "workaround": "Inspect `backend/pyproject.toml` after a run; manually restore `[tool.mutmut]` block if needed. Use `verify.py mutation --restore` to clean up.",
        "architectural_solution": (
            "M44.6: Config is scoped to the isolated workspace. The canonical `backend/pyproject.toml` "
            "is never modified in place. Instead, a workspace-local config overlay is applied, "
            "eliminating cross-campaign configuration contamination entirely."
        ),
        "first_seen": "2026-08-13T00:00:00Z",
        "last_seen": "2026-08-25T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F006",
        "stage": ExecutionStage.CI_ORCHESTRATION.value,
        "owning_layer": OwningLayer.CI.value,
        "reproducibility": Reproducibility.ALWAYS.value,
        "root_cause": (
            "GitHub Actions workflow looks for "
            "`backend/tests/generated/mutation/mutation-summary-summary.json` (double "
            "`summary`) but the actual file is `mutation-summary.json`. This is a known "
            "bug (see corrections.md: ci.mutation_summary_json_path_bug). The jq error "
            "causes exit code 2 even when the mutation run itself succeeded, producing "
            "a false infrastructure failure in CI."
        ),
        "symptoms": [
            "CI mutation job exits with code 2 despite successful mutmut run",
            "jq error in the Classify mutation result step",
            "mutation-summary.json exists but summary-summary.json does not",
        ],
        "workaround": "Manually correct the path in the workflow YAML. Already partially fixed in recent commits.",
        "architectural_solution": (
            "M44.22: CI workflow reads the canonical `mutation-summary.json` produced by "
            "the runner (no double-summary path). Classification logic lives in Python "
            "(same as local), not in ad-hoc bash+jq pipelines."
        ),
        "first_seen": "2026-08-15T00:00:00Z",
        "last_seen": "2026-09-02T00:00:00Z",
        "resolved": True,
        "resolution_commit": "34d22cb7",
    },
    {
        "failure_id": "F007",
        "stage": ExecutionStage.MUTATION_GENERATION.value,
        "owning_layer": OwningLayer.MUTMUT.value,
        "reproducibility": Reproducibility.INTERMITTENT.value,
        "root_cause": (
            "mutmut 3.7.0 uses libcst for source instrumentation. Certain Python 3.12+ "
            "syntax features (e.g. parameter-only generics, some match/case patterns, "
            "walrus operator in specific contexts) cause libcst to either crash or skip "
            "the node entirely. The crash typically manifests as a subprocess TimeoutExpired "
            "or an unhandled exception in mutmut's trampoline generation, which the runner "
            "currently interprets as an infrastructure failure rather than a per-mutant "
            "diagnostic."
        ),
        "symptoms": [
            "mutmut process crashes during generation phase",
            "RC=1 from mutmut with traceback in stderr",
            "Silently missing mutations for files with complex Python 3.12 syntax",
        ],
        "workaround": "Exclude problematic files from source_paths temporarily; report as infra failure rather than scoring them.",
        "architectural_solution": (
            "M44.4: Adapter must distinguish between 'mutmut crashed' (INFRASTRUCTURE_FAILURE) "
            "and 'mutmut generated N mutants, M were skipped due to syntax'. The adapter "
            "records skipped count separately and never misclassifies a crash as SURVIVED."
        ),
        "first_seen": "2026-08-16T00:00:00Z",
        "last_seen": "2026-08-29T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F008",
        "stage": ExecutionStage.ENVIRONMENT_SETUP.value,
        "owning_layer": OwningLayer.ENVIRONMENT.value,
        "reproducibility": Reproducibility.RARE.value,
        "root_cause": (
            "Editable install (`pip install -e .`) registers `src/` on sys.path. "
            "mutmut's `also_copy` mechanism copies source to `mutants/` but the pytest "
            "import resolution from within `mutants/` can pick up the editable-installed "
            "`backend` package from `.venv/lib/python.../site-packages/backend` instead "
            "of the copied source, causing the mutation to have no effect on imported "
            "code (test passes against original source, classified as SURVIVED when it "
            "should be KILLED or INVALID_EXECUTION)."
        ),
        "symptoms": [
            "Mutations appear to have no effect (tests always pass)",
            "Same test passes with and without mutation applied",
            "Import path shows `site-packages/backend` instead of local copy",
        ],
        "workaround": "Set PYTHONPATH explicitly to point at `backend/src` and `backend/tests`; unset site-packages path if needed.",
        "architectural_solution": (
            "M44.7 + M44.15: Each execution workspace must have its own Python environment "
            "with explicit sys.path control. After applying a mutation, verify the mutated "
            "source is actually what gets imported (M44.15 correctness gate)."
        ),
        "first_seen": "2026-08-17T00:00:00Z",
        "last_seen": "2026-08-28T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F009",
        "stage": ExecutionStage.RESULT_COLLECTION.value,
        "owning_layer": OwningLayer.EVIDENCE_RECONCILIATION.value,
        "reproducibility": Reproducibility.OFTEN.value,
        "root_cause": (
            "Current reconciliation uses `parse_mutmut_results()` which parses text output "
            "from `mutmut results --all true`. The mapping from mutmut status strings to "
            "canonical states is hardcoded (_STATUS_MAP) and does not account for all "
            "possible mutmut exit-code semantics. For example, exit code 34 (skipped) maps "
            "to 'skipped' which is not in MutationCounts — it falls through to not_checked. "
            "Exit code 2 (interrupted) is also not distinguished from not_checked."
        ),
        "symptoms": [
            "Interrupted campaigns show high not_checked counts",
            "Skipped mutants counted as not_checked rather than their own category",
            "Arithmetic invariant fails when skipped+interrupted > 0",
        ],
        "workaround": "Count skipped/interrupted as not_checked; accept the approximation.",
        "architectural_solution": (
            "M44.1: Canonical states include NO_TESTS, TIMEOUT, EXECUTION_ERROR, INVALID_MUTANT. "
            "The adapter maps mutmut exit codes to these canonical states explicitly. "
            "Skipped and interrupted become EXECUTION_ERROR with infrastructure_failure=TOOL_CRASH."
        ),
        "first_seen": "2026-08-18T00:00:00Z",
        "last_seen": "2026-08-29T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F010",
        "stage": ExecutionStage.TEST_EXECUTION.value,
        "owning_layer": OwningLayer.CONCURRENCY.value,
        "reproducibility": Reproducibility.INTERMITTENT.value,
        "root_cause": (
            "When mutmut runs with --max-children > 1, multiple pytest processes compete "
            "for the same port (if tests start local servers), write to the same temporary "
            "directories, or corrupt each other's `mutants/` tree. This produces intermittent "
            "test failures that are unrelated to the mutation being tested, inflating "
            "EXECUTION_ERROR counts and potentially misclassifying kills as survived."
        ),
        "symptoms": [
            "Intermittent test failures only visible with --max-children > 1",
            "Port-in-use errors in concurrent pytest invocations",
            "Non-deterministic scores between sequential and parallel runs",
        ],
        "workaround": "Run with --max-children=1 for reliability; accept slower throughput.",
        "architectural_solution": (
            "M44.7: Process isolation includes per-worker temporary directories and "
            "port allocation. M44.21: orchestrator controls parallelism with resource "
            "awareness (CPU, RAM, process count). Workers never share mutable state."
        ),
        "first_seen": "2026-08-19T00:00:00Z",
        "last_seen": "2026-08-27T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F011",
        "stage": ExecutionStage.MUTATION_DISCOVERY.value,
        "owning_layer": OwningLayer.FILESYSTEM.value,
        "reproducibility": Reproducibility.OFTEN.value,
        "root_cause": (
            "mutmut's `.mutmut-cache` directory stores hashed source snapshots to detect "
            "whether files have changed since last run. On a clean checkout the cache is "
            "valid, but if the working tree has uncommitted changes (common during "
            "development), mutmut detects the source hash mismatch and either refuses to "
            "run or produces inconsistent results depending on the exact state."
        ),
        "symptoms": [
            "mutmut refuses to run with 'source has changed' message",
            "Cache invalidated unexpectedly after unrelated file edits",
            "Different mutant counts on same logical source due to dirty-tree state",
        ],
        "workaround": "Stash or commit changes before running; use `--no-cache` to bypass.",
        "architectural_solution": (
            "M44.6: Isolated workspace means the mutation source tree is a copy, not the "
            "working tree. Cache is per-workspace, not global. Dirty working tree has zero "
            "effect on the campaign."
        ),
        "first_seen": "2026-08-20T00:00:00Z",
        "last_seen": "2026-08-29T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F012",
        "stage": ExecutionStage.TEST_EXECUTION.value,
        "owning_layer": OwningLayer.PYTEST.value,
        "reproducibility": Reproducibility.INTERMITTENT.value,
        "root_cause": (
            "Some tests in the repository have side effects (global state modification, "
            "file system writes, database mutations) that are not cleaned up between test "
            "functions. When mutmut runs a subset of tests for a mutant, these side effects "
            "can cause non-deterministic behaviour: a test that normally passes may fail "
            "due to state left by a previous test in the selection, leading to false KILLED "
            "classifications."
        ),
        "symptoms": [
            "Flaky test failures that disappear when tests are reordered",
            "Tests passing in isolation but failing in mutmut subsets",
            "State-leak between tests in the same selection",
        ],
        "workaround": "Run tests sequentially for affected components; exclude flaky tests from mutation scope.",
        "architectural_solution": (
            "M44.13: Test selection architecture consults the Verification Graph to determine "
            "the minimal valid test selection. Tests with known side effects are marked with "
            "an isolation attribute and handled with proper setup/teardown in the adapter."
        ),
        "first_seen": "2026-08-21T00:00:00Z",
        "last_seen": "2026-08-28T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F013",
        "stage": ExecutionStage.CI_ORCHESTRATION.value,
        "owning_layer": OwningLayer.CI.value,
        "reproducibility": Reproducibility.ALWAYS.value,
        "root_cause": (
            "The mutation CI workflow has a 90-minute timeout. Full campaigns on the "
            "repository (~17000 mutants) can exceed this under CI load (shared runners, "
            "resource contention). When the workflow times out, the mutmut process is "
            "killed by the runner, leaving partial results in `.mutmut-cache` and "
            "`mutants/`. There is no resume mechanism in the current workflow — the next "
            "run starts fresh or reads stale cache."
        ),
        "symptoms": [
            "CI mutation job times out before completion",
            "Partial results lost on timeout",
            "No way to resume from the interruption point",
        ],
        "workaround": "Split into per-engine targeted campaigns; run full campaign less frequently.",
        "architectural_solution": (
            "M44.10: Campaign persistence stores checkpoint after every N mutants. "
            "On resume, completed mutants are skipped and pending ones are picked up. "
            "M44.20: Sharding allows splitting a full campaign across multiple parallel "
            "jobs with deterministic boundaries, each completing well within timeout."
        ),
        "first_seen": "2026-08-22T00:00:00Z",
        "last_seen": "2026-09-02T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F014",
        "stage": ExecutionStage.MUTATION_GENERATION.value,
        "owning_layer": OwningLayer.MUTMUT.value,
        "reproducibility": Reproducibility.INTERMITTENT.value,
        "root_cause": (
            "mutmut 3.7.0 applies mutations by writing modified source files into "
            "`mutants/<relative_path>/`. For `src/` layout packages (where the package "
            "is installed editable), pytest resolves imports from `site-packages` "
            "rather than from the `mutants/` copy, meaning the mutation has no effect "
            "on the imported code. Tests pass against the original source, and the "
            "mutant is incorrectly classified as SURVIVED rather than INVALID_EXECUTION."
        ),
        "symptoms": [
            "Survived mutants that should be killed (mutation has no effect)",
            "Running the surviving mutant's test manually against the mutants/ copy shows failure",
            "Source hash of mutants/ file differs from original but test still passes",
        ],
        "workaround": "Force pytest to import from mutants/ by manipulating sys.path or using `python -m pytest` from within mutants/.",
        "architectural_solution": (
            "M44.7 + M44.15: Each execution runs in an isolated workspace with controlled "
            "PYTHONPATH. M44.15 correctness gate verifies that the mutated source file "
            "actually differs from baseline AND that the test process imports the mutated "
            "version (not the site-packages original)."
        ),
        "first_seen": "2026-08-23T00:00:00Z",
        "last_seen": "2026-08-29T00:00:00Z",
        "resolved": False,
    },
    {
        "failure_id": "F015",
        "stage": ExecutionStage.ENVIRONMENT_SETUP.value,
        "owning_layer": OwningLayer.ENVIRONMENT.value,
        "reproducibility": Reproducibility.RARE.value,
        "root_cause": (
            "The `.venv` environment may drift between local development and CI. "
            "Different Python patch versions, different mutmut minor versions (despite "
            "pinning), or different OS-level library versions can cause different "
            "mutation discovery or execution behaviour. The environment fingerprint in "
            "env.py catches major mismatches but does not compare every transitive "
            "dependency version."
        ),
        "symptoms": [
            "Different mutant counts between local and CI runs on the same SHA",
            "Scores diverge between environments",
            "Environment check passes but mutation results differ",
        ],
        "workaround": "Pin all transitive dependencies; use identical base images in CI.",
        "architectural_solution": (
            "M44.11: Deterministic configuration fingerprint includes full dependency lock "
            "hash, Python patch version, OS platform, and mutmut version. Cache entries are "
            "invalidated when any fingerprint component changes. M44.12 cache architecture "
            "enforces fingerprint compatibility before reuse."
        ),
        "first_seen": "2026-08-24T00:00:00Z",
        "last_seen": "2026-08-29T00:00:00Z",
        "resolved": False,
    },
]


def build_forensics() -> dict[str, Any]:
    """Build the complete mutation failure forensics document."""
    records = [
        {
            "failure_id": r["failure_id"],
            "stage": r["stage"],
            "owning_layer": r["owning_layer"],
            "reproducibility": r["reproducibility"],
            "root_cause": r["root_cause"],
            "symptoms": r["symptoms"],
            "workaround": r["workaround"],
            "architectural_solution": r["architectural_solution"],
            "first_seen": r["first_seen"],
            "last_seen": r["last_seen"],
            "resolved": r["resolved"],
            "resolution_commit": r.get("resolution_commit"),
        }
        for r in _FORENSIC_RECORDS
    ]

    unresolved = [r for r in records if not r["resolved"]]
    by_stage = {}
    for r in records:
        by_stage.setdefault(r["stage"], []).append(r["failure_id"])
    by_layer = {}
    for r in records:
        by_layer.setdefault(r["owning_layer"], []).append(r["failure_id"])

    return {
        "schema": "m9-c44-mutation-forensics/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "total_failures": len(records),
        "resolved": len([r for r in records if r["resolved"]]),
        "unresolved": len(unresolved),
        "records": records,
        "by_execution_stage": {k: len(v) for k, v in sorted(by_stage.items())},
        "by_owning_layer": {k: len(v) for k, v in sorted(by_layer.items())},
        "architectural_gaps": [r["architectural_solution"] for r in unresolved],
    }


def write_forensics(output_dir: Path | None = None) -> Path:
    if output_dir is None:
        output_dir = GENERATED_C44
    output_dir.mkdir(parents=True, exist_ok=True)
    data = build_forensics()
    path = output_dir / "mutation-failure-forensics.json"
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path


if __name__ == "__main__":
    p = write_forensics()
    print(f"Wrote forensics: {p}")
    data = json.loads(p.read_text())
    print(
        f"Total: {data['total_failures']}, Resolved: {data['resolved']}, Unresolved: {data['unresolved']}"
    )
