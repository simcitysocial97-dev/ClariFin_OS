# M10 Agent 1 — Test Taxonomy

**Baseline:** `main` @ `bfcf336b`
**Trees:** `runtime/tests` (156 `.py`, 154 `test_*.py`, flat) and `backend/tests` (323 `.py`, 203 `test_*.py`, 13 category directories).

## 1. The taxonomy that actually exists

The repository declares 11 markers in `pyproject.toml` `tool.pytest.ini_options.markers`.
**Two of them are used. Nine are not.**

| Marker | Declared | `runtime/tests` uses | `backend/tests` uses |
|---|---:|---:|---:|
| `contract` | yes | 0 | 161 |
| `slow` | yes | 2 | 0 |
| `unit` | yes | 0 | 0 |
| `integration` | yes | 0 | 0 |
| `property` | yes | 0 | 0 |
| `invariant` | yes | 0 | 0 |
| `golden` | yes | 0 | 0 |
| `meta` | yes | 0 | 0 |
| `mutation` | yes | 0 | 0 |
| `capability` | yes | 0 | 0 |
| `performance` | yes | 0 | 0 |

So the enforced taxonomy is **directory-based**, not marker-based. That is the convention to
build the policy on — the codebase already chose it, and adopting markers now would be
introducing a second vocabulary rather than consolidating one.

### Backend taxonomy (by directory, authoritative)

| Directory | `test_*.py` | Category | Notes |
|---|---:|---|---|
| `unit/` | 90 | unit | further nested by engine (`engines/loan/`, `engines/behaviour/`, …) |
| `properties/` | 28 | property / property-based | Hypothesis; own `conftest.py` with 8 strategies + `hypothesis_settings` |
| `contract/` | 27 | contract | includes the **tracked** `contract/generated/` (27 files) = committed API contract baseline |
| `capability/` | 13 | capability | own `conftest.py`, manifest loading + `pytest_configure` |
| `integration/` | 12 | integration | where the `platform_api_phase*` files live |
| `invariants/` | 10 | invariant | money-representation invariants |
| `mutation_infra/` | 7 | meta/tooling | mutation pipeline health; has its own `pyproject.toml` mutmut scope |
| `meta/` | 6 | meta | |
| `architecture/` | 5 | architecture | |
| `audits/` | 1 | audit | |
| `golden/` | 1 | golden | |
| `mutation_trust/` | 1 | meta | mutation-measurement trust |
| `probes/` | 1 | probe | **deliberately never collected** (`norecursedirs`) |
| *(root)* | 1 | — | `test_m9_c56_scenarios.py` |

Note the directory/marker **singular–plural mismatch**: directories are `properties/` and
`invariants/`, the markers are `property` and `invariant`. Since the directories are the
enforced taxonomy, the markers should follow them if markers are ever adopted.

### Runtime taxonomy (by prefix, implicit)

`runtime/tests` is **flat** — 154 `test_*.py` in one directory, no categories. The only
grouping signal is the filename prefix. Counting distinct prefixes shows a de-facto,
unofficial taxonomy:

| Prefix family | Files | Implied category |
|---|---:|---|
| `test_platform_api_phase*` | 9 | platform API contract (see §4) |
| `test_m9_c4*` / `test_m9_c5*` | 20 | per-milestone certification gates |
| `test_vea5_*` | 4 | VEA5 security/merge program |
| `test_m9c5*` / `test_m9c6*` / `test_m9c7*` | 14 | later milestones (note: no `_` after `m9`) |
| `test_mut*` | 6 | mutation subsystem |
| `test_*contract*` / `test_*invariant*` / `test_*evidence*` | ~20 | by subject |
| remainder | ~80 | by subject |

The prefix taxonomy is real but **undocumented, unenforced, and inconsistent**: `test_m9_c55.py`
(underscore) sits beside `test_m9c57_verification_self_contract.py` (no underscore) for the same
milestone, and `test_c37_certification_arithmetic.py` / `test_c43_test_generator.py` use bare `cNN`.

## 2. Collection and uncollected files

| Tree | `test_*.py` on disk | files yielding collected nodes | never collected |
|---|---:|---:|---:|
| `runtime/tests` | 154 | 153 | **1** |
| `backend/tests` | 203 | 201 | 2 |

Method: `pytest <tree> --collect-only -q`, map each node id back to its file, diff against
`rglob("test_*.py")`.

### The one runtime file that never runs — and is a proven duplicate

`runtime/tests/test_m9_c50_stop_gate9_failure_modes.py` (48,690 B, 1,263 lines) contains
**zero test functions**:

```
$ grep -cE "def test" runtime/tests/test_m9_c50_stop_gate9_failure_modes.py
0
```

It is a standalone audit harness (`main() -> int`, functions `a1_execution_architecture` …
`a13_failure_injection`, writing to `runtime/generated/m9-c50/final-freeze/`). Because it is
named `test_*.py`, every glob, CI path filter and coverage report lists it as a test file while
pytest collects nothing from it.

It is a **byte-clone of `runtime/tests/audit_final_freeze.py`** — 1,262 vs 1,263 lines,
`diff` output is exactly one added line:

```
$ diff -u runtime/tests/audit_final_freeze.py runtime/tests/test_m9_c50_stop_gate9_failure_modes.py
@@ -14,6 +14,7 @@
 REPO_ROOT = Path(__file__).resolve().parent.parent.parent
+sys.path.insert(0, str(REPO_ROOT))
```

`audit_final_freeze.py` is the correctly-named twin: same `OUT_DIR`, same
`m9-c50/final-freeze/*@1` schema strings, same a1–a13 functions, and — because it has no
`test_` prefix — correctly outside pytest's collection.

Deleted the misnamed clone. Evidence and reasoning in `m10-agent1-cleanup-ledger.md`.

> **Correction to the record.** `progress.md:7786` (item D) states that
> `audit_final_freeze.py` "is not collected by pytest (no `test_` prefix), so it is a 1,262-line
> mirror that no fix to the collected copy will ever reach." That reasoning is inverted:
> **neither** file is collected, because neither defines a test. The consequence is the same
> (1,262 dead lines) but the reason is different — it is a misfiled *tool*, not an unreached
> mirror of a live test.

### The two uncollected backend files — both intentional

| File | Why uncollected | Verdict |
|---|---|---|
| `backend/tests/probes/test_m4_exit_probe.py` | `probes` is in `norecursedirs` | Intentional. Body is 2 lines: `def test_m4_probe(): raise AssertionError("M4 exit probe: intentionally failing")` — a deliberately-failing probe kept out of every run. KEEP. |
| `backend/tests/mutation_infra/mutants/test_probe.py` | `mutation_infra/mutants` is in `norecursedirs` | Intentional. It is a mutmut scratch copy, regenerated by `runtime verify mutation --smoke`. Tracked by mistake; see cleanup ledger. |

## 3. Hermeticity defects (fixed)

Two modules operated on the real repository instead of isolated fixtures. Both were
**destructive**, and both are fixed with no change to any assertion.

| Module | What it did | Fix |
|---|---|---|
| `test_evidence_cleanup_stress.py` | `EvidenceRetention().cleanup(dry_run=False)` ×2 against the real `runtime/generated/`, which really `shutil.rmtree`s. 1,541 of 2,149 tracked evidence files (71.7%) sit in directories the retention regexes classify as expirable. | Pass the `generated_dir` constructor argument the class already supports (`evidence_retention.py:86-93`); build a `tmp_path` tree. `dry_run=False` retained. |
| `test_f006_configuration_divergence.py` | Rewrote the tracked production `verification.yaml` with `coverage_threshold: 999`, restoring in a `finally` that does not run on SIGKILL/OOM/timeout. | `shutil.copy2` to `tmp_path`, redirect `config_loader.DEFAULT_YAML_PATH` via `monkeypatch` (auto-restored even on interrupt). `reload_config()` exists for this — its docstring says "useful in tests that patch the yaml file". |

`monkeypatch` is what makes the second fix strictly safer than the original: teardown is
pytest's, not the test's.

## 4. Naming: the `platform_api_phase*` family

12 files, 487 tests, named for a milestone phase rather than a capability — and the numbering
has visible accretion damage: phases 1, 2, 3, 4, 6, 7, 8, 9, **10_12**, 13, 14, **15_21**.
Phase 5 is absent, and two files are merged phase ranges.

Each file's own docstring already states the capability, so the better name is not a guess:

| File(s) | Docstring capability | Tests |
|---|---|---:|
| `runtime/tests/test_platform_api_phase1.py` | Platform Contract Foundation | 91 |
| `runtime/tests/test_platform_api_phase2.py` | Platform Service Aggregators | 48 |
| `backend/tests/integration/test_platform_api_phase3.py` | FastAPI Platform Mount | 46 |
| `backend/tests/integration/test_platform_api_phase4.py` | Platform Snapshot & Read-Path Performance | 33 |
| `backend/tests/integration/test_platform_api_phase6.py` | Verification Center | 12 |
| `runtime/tests/test_platform_api_phase7.py` | Execution, Evidence and Live State | 25 |
| `runtime/tests/test_platform_api_phase8.py` | History + Evidence + Comparison | 29 |
| `runtime/tests/test_platform_api_phase9.py` | Error Observatory + Architecture + Capability Explorer | 43 |
| `runtime/tests/test_platform_api_phase10_12.py` | Diagnostic Platform | 33 |
| `runtime/tests/test_platform_api_phase13.py` | AI Control Layer Foundation | 44 |
| `runtime/tests/test_platform_api_phase14.py` | Context Engine | 41 |
| `runtime/tests/test_platform_api_phase15_21.py` | AI Control Layer (governance/safety gates) | 42 |

**Recommendation: rename, but not in this pass.** Renaming is blocked on reference surfaces I
do not own:

- `runtime/generated/**` — frozen milestone evidence references these filenames in at least
  `m9-c64-runtime-framework-final-convergence/residual-ledger.json` (3 node ids) and
  `m9-c64-r-runtime-pipeline-forensic-validation/pipeline-traces/*` (dozens). Evidence is
  immutable by policy.
- `BASELINE.md` and `docs/audits/m9-c57-runtime-framework/*` — not my ownership.
- `repomix-output.xml` — generated, not my ownership.
- `runtime/tests/test_changed_file_parsing.py:158` — a live test that uses
  `"backend/tests/integration/test_platform_api_phase3.py"` as a **string literal** in a
  `parametrize` list. It never opens the file (it only feeds `is_generated_or_artifact_path`),
  so it would not fail, but it would become a reference to a path that no longer exists.

`.github/` was checked and contains **zero** references, so CI is not the blocker. The blocker
is exclusively frozen evidence plus non-owned docs — which is exactly the condition the M10
brief names as disqualifying ("references are safely updatable"). The mapping is recorded in
`m10-agent1-naming-policy.md` so a single owner can execute it atomically.

All 12 files also cite `IMPLEMENTATION_ROADMAP.md`, which **does not exist at the repo root** —
it lives at `runtime/generated/m9-c57-platform-ai-design/IMPLEMENTATION_ROADMAP.md`. The
reference is stale-relocated, not dangling. 30+ source and test files cite it the same way,
across `backend/src/routers/platform.py:6`, `runtime/platform/__init__.py:22`, and
`frontend/types/api-generated.ts:3413` — a repository-wide doc-rotation issue, not mine.

## 5. Duplication measured, and where I declined to fix it

### Declined: collapsing repeated `verify doctor` / `plan` spawns

`runtime/tests/test_m9c66_repeatability.py` spawns `runtime.verify` 7 times
(`_run_doctor` ×2 in `test_doctor_consistent_across_runs`, ×3 in
`test_no_forbidden_nondeterminism`, `_run_plan` ×2 in `test_plan_fingerprint_stable`) at ~10.5 s
each, ≈73 s. `progress.md` item C proposes "a session-scoped fixture for `doctor`/`plan`
collapses 9 spawns to 3."

**That fix would reduce meaningful coverage, so I did not apply it.** These tests exist to
prove the commands are *idempotent*: `test_doctor_consistent_across_runs` compares two runs,
`test_plan_fingerprint_stable` compares two plan ids, `test_no_forbidden_nondeterminism`
requires three. Memoising the subprocess result makes a repeatability test assert nothing. The
file's own docstring (lines 70-85) records that the *timeout* was already raised to 180 s
precisely because one doctor run costs ~11 s — i.e. the repetition is the contract.

The only legitimate saving here is a shared helper for the `run_verify` wrapper, which does not
remove a single spawn. Not worth churn.

### Declined: caching the four identical coverage runs

`runtime/tests/test_coverage_path_authority.py` calls
`_coverage_run(scope="tests/unit/engines/credit_card", max_runtime=60)` **four separate times**
(lines 53, 64, 132, 140), each hitting the full 60 s cap — 240 s for four identical calls.
Three of the four assert byte-identical properties (`line_percent is not None`,
`"not found" not in tail`).

But the test *names* promise four different invocation contexts — `..._from_backend_cwd`,
`..._from_subdirectory`, `..._clean_environment`, `..._ci_like_environment` — and **none of the
four bodies chdir or patch `os.environ`.** So the module either

- is 240 s of pure duplicated work, or
- is a genuine coverage gap: it was *meant* to vary cwd/env and does not.

A module-scoped cache fixture would silently pick the first reading and entrench whichever of
those two is true, converting a visible cost into invisible missing coverage. Adding the
missing context variation is the opposite trade. Neither is a safe unilateral call, so this is
reported rather than changed. It is the single largest safe-looking saving in the runtime suite
and it needs an intent decision from the owner.

### Declined: recursive nested pytest

`progress.md` item A measures 386.66 s (34% of a ~1,800 s run) re-executing modules the outer
run already ran. Confirmed at 11 spawn sites across 6 files:

| File | Lines | Re-executes |
|---|---|---|
| `test_m9_c55.py` | 129, 503, 517, 956 | incl. `test_m9_c52/53/54.py` wholesale (956) |
| `test_m9_c53.py` | 679, 703, 727 | |
| `test_m9_c50_operational_lineage.py` | 292, 345 | |
| `test_m9_c54.py` | 803 | |
| `test_backend_evidence.py`, `test_m9_c42_28.py` | 1 each | |

The proposed fix ("assert the gate functions in-process instead of re-running whole modules")
is a behavioural rewrite of certification-gate assertions. Given the standing constraint not to
weaken test assertions and not to alter verification thresholds, this is not a safe
consolidation to perform blind. Reported with exact locations.

## 6. A finding that makes runtime failure counts in this worktree untrustworthy

**36 call sites across 15 `runtime/tests` files hardcode `.venv/bin/python`** (or
`../.venv/bin/python`, `.venv/bin/coverage`) instead of resolving the interpreter the way
`AGENTS.md` and `runtime/foundation/verification/env.py` require (`.venv/bin` first, then
`PATH`). Examples: `test_m9_c55.py:127,501`, `test_m9_c72_incremental_mutation.py:222,430`,
`test_coverage_path_authority.py:75,88`, `test_m9_c54.py` ×4, `test_m9_c49.py` ×3,
`test_vea5_m8r_cli_reconcile.py:1`, plus 10 more in `audit_final_freeze.py`.

A git worktree has no `.venv`, so in this worktree every one of those call sites fails with
`FileNotFoundError`. **`AGENTS.md` prescribes exactly this setup** — a root `.venv` that a
worktree does not contain — so hardcoding `.venv/bin/python` makes these tests structurally
unable to run in the prescribed configuration. That is a real robustness defect, and it is why
I report the failures observed here as *environment-affected* rather than as baseline defects.

`test_m9_c55.py:951` is the clearest case: it runs `".venv/bin/python"` with `cwd=REPO_ROOT`,
which in this worktree resolves to a non-existent path.

## 7. Taxonomy recommendation

1. **Directories are the taxonomy.** Keep `backend/tests/<category>/`; do not introduce marker
   vocabulary to parallel it.
2. **Adopt `slow` where it is already declared.** Exactly 2 uses exist across 6,708 tests. The
   mutation-smoke and nested-pytest tests are the natural population, and `-m "not slow"` is
   already supported by the existing declaration. Bounded verification runs need this.
3. **Align marker names to directory names** if markers are ever adopted: `properties` →
   `property` is currently a silent trap.
4. **Either remove the 9 unused markers or adopt them.** A marker list that advertises
   `-m integration` / `-m property` selections which match nothing is a false affordance; CI
   and humans will write selectors that silently deselect the entire suite.
