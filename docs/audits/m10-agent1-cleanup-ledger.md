# M10 Agent 1 — Cleanup Ledger

**Baseline:** `main` @ `bfcf336b`

Every removal below is justified by one of the six permitted reasons — **unused**, **obsolete**,
**duplicate**, **replaced**, **generated**, **demonstrably unreachable** — and the evidence is
reproducible. Nothing was removed for being old, and nothing was removed outside
`runtime/tests/**` or `backend/tests/**`.

---

## Deletions

### 1. `runtime/tests/test_m9_c50_stop_gate9_failure_modes.py`

| Field | Value |
|---|---|
| **Reason** | **duplicate** + **misfiled tool** (contributes zero tests) |
| Size removed | 48,690 B / 1,263 lines |
| Git | `git rm`, staged as a deletion |

**Evidence 1 — it contains no tests.** The `test_` prefix makes it look like a test module; it
is not one.

```
$ grep -cE "def test" runtime/tests/test_m9_c50_stop_gate9_failure_modes.py
0
$ grep -nE "^(class |def )" ... 
55:def write_json(...)      68:def a1_execution_architecture()  169:def a2_adapter_semantic_audit()
255:def a3_execution_authenticity()  354:def a4_lineage_invariants()  514:def a5_decision_authority()
579:def a6_cache_semantics()  741:def a7_ci_parity()  789:def a8_self_verification()
820:def a9_runtime_health()  952:def a10_governance_invariants()  1020:def a11_repository_boundary()
1057:def a12_reproducibility()  1123:def a13_failure_injection()  1173:def main() -> int
```

It is a standalone audit harness with a `main()`, writing to
`runtime/generated/m9-c50/final-freeze/`.

**Evidence 2 — it is a byte-clone of a file that already exists.**

```
$ wc -l runtime/tests/audit_final_freeze.py runtime/tests/test_m9_c50_stop_gate9_failure_modes.py
 1262 audit_final_freeze.py
 1263 test_m9_c50_stop_gate9_failure_modes.py

$ diff -u runtime/tests/audit_final_freeze.py runtime/tests/test_m9_c50_stop_gate9_failure_modes.py
@@ -14,6 +14,7 @@
 REPO_ROOT = Path(__file__).resolve().parent.parent.parent
+sys.path.insert(0, str(REPO_ROOT))
```

The entire diff is **one added line**. Both files share the same `OUT_DIR`, the same
`m9-c50/final-freeze/<name>@1` schema strings, and the same a1–a13 functions.

**Evidence 3 — pytest collected nothing from it.** Full-tree collection maps 153 of 154
`test_*.py` files to at least one collected node; this is the one that does not. It was listed
among "154 tests" while contributing 0.

**Evidence 4 — zero references.** `grep -rn "stop_gate9_failure_modes"` over `*.py`, `*.sh`,
`*.yml`, `*.yaml`, `*.toml`, `*.ts`, `*.json` returns nothing outside `runtime/generated/` and
`repomix-output.xml`, neither of which names this file. `.github/` is clean.

**Why the correctly-named twin survives.** `audit_final_freeze.py` is the same harness without
the misleading `test_` prefix, so it is correctly outside collection. Deleting the misnamed copy
preserves 100% of the tool's behaviour and removes the false coverage signal.

**Impact on collection: zero.** `runtime/tests` collected **2,564 tests before and 2,564 after**
— empirical confirmation that the file never contributed a test.

**Correction to the existing record.** `progress.md:7786` (item D) states
`audit_final_freeze.py` "is not collected by pytest (no `test_` prefix), so it is a 1,262-line
mirror that no fix to the collected copy will ever reach." The conclusion (1,262 dead lines) is
right; the mechanism is inverted. **Neither** file is collected, because **neither defines a
test**. It is a misfiled tool, not an unreached mirror of a live test.

---

### 2. `backend/tests/mutation_infra/mutants/` — 6 tracked files untracked (`git rm --cached`)

| File | Reason | Evidence |
|---|---|---|
| `probe.py` | **generated** | mutmut trampoline output |
| `probe.py.meta` | **generated** | mutmut internal cache |
| `probe.py.spans` | **generated** | mutmut internal cache |
| `mutmut-stats.json` | **generated** | per-run mutmut statistics |
| `pyproject.toml` | **generated** + **duplicate** | byte-identical to parent |
| `test_probe.py` | **generated** + **duplicate** | byte-identical to parent |

**Evidence 1 — they are mutmut's own output.** `probe.py` differs from the source
`backend/tests/mutation_infra/probe.py` by the mutmut trampoline
(`from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict`),
five `x_mutation_probe__mutmut_N` variants, and inline comments reading
`# type: ignore # mutmut generated`. `probe.py.meta` / `probe.py.spans` are mutmut's own
per-function caches.

**Evidence 2 — the runner designates the directory a write target.**
`runtime/foundation/verification/mutation_runner.py:124`:

> `# For smoke mode, mutation runs in mutation_infra/ which is expected to change`
> `# (mutants, cache), so we don't hash it`

**Evidence 3 — they were rewritten by test runs during this session.** mtimes moved from the
checkout time `09-29 19:53` to `10-02 07:50` and `08:20` while I was running the suite.

**Evidence 4 — two are exact duplicates of the parent.**

```
$ diff -q backend/tests/mutation_infra/pyproject.toml backend/tests/mutation_infra/mutants/pyproject.toml  → identical
$ diff -q backend/tests/mutation_infra/test_probe.py  backend/tests/mutation_infra/mutants/test_probe.py    → identical
```

**Evidence 5 — the repository already declares them ignorable.**

```
$ git check-ignore -v --no-index backend/tests/mutation_infra/mutants/probe.py
.gitignore:120:mutants/	backend/tests/mutation_infra/mutants/probe.py
```

All 6 are matched by `.gitignore:120 mutants/`. They were tracked regardless, which is how they
appear in the "83 tracked files that are also gitignored" set. `pyproject.toml`
`norecursedirs` also excludes `backend/tests/mutation_infra/mutants`, so pytest never collects
from there.

**Untracked, not deleted** (`git rm --cached`) — the files stay on disk so the working tree and
the mutation smoke are unaffected, and the directory is recreated by mutmut on the next smoke.
This also removes a **latent intermittent failure**: `_check_dirty_worktree()`
(`mutation_runner.py:164-187`) scopes the smoke's git check to
`backend/tests/mutation_infra` (line 170) and aborts on any ` M`/`D `/`??` entry, while the
*hash* check for the same directory deliberately ignores it. The two halves of one safety guard
disagree. I hit the abort directly:

```
RuntimeError: Dirty worktree detected in mutation scope. Unexpected tracked changes:
['backend/tests/mutation_infra/mutants/mutmut-stats.json', ...] Use --allow-dirty to override.
```

`mutmut-stats.json` embeds wall-clock values (`duration_by_test`, `stats_time`), so it is
non-deterministic whenever mutmut re-runs the tests. In this session it happened to be stable
across two consecutive smokes (identical floats), which is exactly why this is *intermittent*
and would present as a flake rather than a hard failure. The guard itself is in
`runtime/foundation/`, outside my ownership — **reported, not patched**; the untracking removes
the exposure from the repository side.

**Note:** I reverted this untracking while investigating (the staged deletion itself tripped the
guard) and re-applied it only after establishing the evidence above. The committed end state is
the untracking.

---

## Modified (not deleted) — hermeticity repairs

No assertion, threshold, gate, marker or expected value was changed. Both changes make a test
operate on an isolated copy instead of the real repository.

| File | Change | Reason category |
|---|---|---|
| `runtime/tests/test_evidence_cleanup_stress.py` | Pass `EvidenceRetention(generated_dir=<tmp_path tree>)` in all 4 tests; keep `dry_run=False` | **destructive-on-real-repo defect** |
| `runtime/tests/test_f006_configuration_divergence.py` | `shutil.copy2` the real config to `tmp_path`, redirect `config_loader.DEFAULT_YAML_PATH` via `monkeypatch` | **destructive-on-real-repo defect** |
| `backend/tests/invariants/test_reconciliation_properties.py` | `test_edge_cases_property` now calls `_fresh_reconciliation_db(_pristine_db_template)`, matching its 4 siblings in the same file | **inconsistent-with-siblings (latent flake)** |

### 1 — `test_evidence_cleanup_stress.py`: could delete 1,541 tracked files

`EvidenceRetention()` defaulted to the real `runtime/generated/`, and
`cleanup(dry_run=False)` really `shutil.rmtree`s (`evidence_retention.py:203-214`). Classifying
the actual tree:

| category | window | directories matched |
|---|---:|---:|
| `milestones` (`^m9-c\d+(?:\.\d+)?/?$`) | 90 d | 27 (`m9-c42.21` … `m9-c59`) |
| `evidence` (`^evidence/?$`) | 60 d | `evidence/` |
| `ai-runs` (`^ai-runs/?$`) | 30 d | `ai-runs/` |
| `metrics` (`^metrics/?$`) | 90 d | `metrics/` |

```
$ git ls-files <those 29 dirs> | wc -l
1541
$ git ls-files runtime/generated | wc -l
2149
```

**1,541 of 2,149 tracked files (71.7%)** sit in directories the policy classifies as expirable.
All currently read 0–2 days old — an artifact of *when the worktree was checked out*, since git
sets a checked-out file's mtime to checkout time. On a working copy older than 30–90 days, one
run of this module deletes 1,541 tracked files **and every assertion still passes**, because the
tests' own synthetic dirs (`m9-c99-test`, `m9-c99-preserve`, …) do not match any retention
regex, so nothing they assert is ever affected by collateral damage.

Fix: `EvidenceRetention.__init__` already accepts `generated_dir`
(`evidence_retention.py:86-93`) — the tests simply were not using it. `dry_run=False` retained,
so the real deletion path is still exercised; manual teardown blocks removed because `tmp_path`
is pytest-managed.

### 2 — `test_f006_configuration_divergence.py`: could corrupt the production config

The two divergence tests rewrote the tracked
`runtime/foundation/verification/verification.yaml` with `coverage_threshold: 999`, restoring it
in a `finally`. A `finally` does not execute on SIGKILL/OOM/timeout, so an interrupted run left
the production verification config corrupted; the path was also CWD-relative, so the write only
landed when pytest started from the repository root. `progress.md:7786` had already flagged this
as "the only finding that can permanently damage the repo".

Fix uses the mechanism the loader documents for this purpose — `reload_config()`: *"Clear the
YAML cache — useful in tests that patch the yaml file."* `monkeypatch` restores
`DEFAULT_YAML_PATH` even on an interrupt, which is strictly safer than the original `finally`.

Verified after both fixes: `git diff --quiet runtime/foundation/verification/verification.yaml`
→ unchanged; `git status runtime/generated` → 0 entries.

### 3 — `test_reconciliation_properties.py`: latent Hypothesis/DB flake

Four of the five property tests in this file already called
`_fresh_reconciliation_db(_pristine_db_template)` (lines 112, 155, 208, 249);
`test_edge_cases_property` did not. That helper's docstring explains the failure it prevents:
Hypothesis reuses one function-scoped fixture across all examples, so rows accumulate in the
append-only `transactions` table — whose `StatementRepository` trigger refuses `DELETE`, which is
correct for a financial ledger and not something a test should route around — and a later
example collides on `UNIQUE (statement_id, date, description, amount_paise, sequence_num)`. The
sibling file `test_reconciliation_determinism.py` already had the fix; this was a missed
application of the file's own established pattern. `max_examples` deliberately left unchanged.

---

## Considered and deliberately **not** removed

Recorded because "we looked and left it" is a result, and because each of these looks removable
at a glance.

| Item | Why it looks removable | Why it stays |
|---|---|---|
| `backend/tests/probes/test_m4_exit_probe.py` | Deliberately always-failing, never collected | Intentional probe, 2 lines, explicitly excluded by `norecursedirs`. Deleting it removes a deliberate artefact. |
| `runtime/tests/audit_final_freeze.py` | 1,262 lines, no tests, "old" | It is the **surviving** copy of the deleted pair. Removing it would delete the tool. |
| `repomix-output.xml` | 8.0 MB generated blob, tracked | Genuinely `generated`, but repo root is outside my ownership. **Flagged to `main`.** |
| `_probe_emi_up.py` | 32-line scratchpad at repo root, no callers | Misplaced `TOOLING` (imports `src.engines.*`, prints "EMI UP" cases, has no `main()`). Outside my ownership. **Flagged to `main`.** |
| `runtime/generated/**` 2,149 tracked files | Looks like stale output | Mixed by policy: milestone evidence and hand-written scripts that tests read as *inputs*. `*.diff`/`*.log`/caches are already filtered. Not cleanable. |
| 30 tracked `runtime/generated/**` logs matched by `.gitignore` | Ignorable yet tracked | Outside my ownership; a sound cleanup candidate for the owner. |
| `test_coverage_path_authority.py`'s 4 identical 60 s calls | Pure duplication | Either 240 s of waste **or** a coverage gap — its names promise 4 invocation contexts no body establishes. Caching would entrench the ambiguity. Needs an intent decision. |
| `test_reconciliation_properties.py` / `…_determinism.py` | 311 shared identical lines | The 5 shared property tests **differ** (`max_examples` 10 vs 5; one lacks the isolation fix). Deleting either reduces the statistical strength of a money-representation property test. |
| 11 nested-pytest spawn sites (386.66 s, 34% of a run) | Massive duplicated work | Fixing it means rewriting certification-gate assertions. Explicitly out of bounds. Reported with exact locations. |
| 9 unused pytest markers | Dead configuration | Removing them is a public-interface change to `pyproject.toml` selection syntax, and CI may reference them. Reported; the safer fix is adoption, which is a code change across both trees. |
| `dependency-reports/`, `memory-bank/`, `test-results/`, `servers/`, `activeContext.md` | Tracked yet gitignored | Outside my ownership. Contradiction documented in the inventory for the owner. |
| `/tmp/kilo/wt3` worktree (`f9d8777e`, marked prunable) | Stale git worktree | Repository-level git state, not a file. Flagged to `main`. |

## Nothing generated or cached was committed

`.hypothesis/` (386 files), 131 `__pycache__` dirs, and the nested
`backend/tests/mutation_infra/mutants/{__pycache__,.pytest_cache,.hypothesis}` trees are all
untracked and stayed that way. `git status` was checked before every commit.
