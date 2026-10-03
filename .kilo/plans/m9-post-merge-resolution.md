# M9 — Post-Merge Resolution Plan

**Base:** `main` @ `75415c8e7c8264db80a20cdf537d2d1080f7aa5d` (clean tree)
**Scope:** every defect recorded in `progress.md` and the four audit reports, plus the two open items from the stabilization itself.

---

## 0. Standing constraints (unchanged from the stabilization mandate)

These bind every workstream below unless a workstream says otherwise:

- **No threshold may be weakened.** Coverage/mutation/regression thresholds, `--timeout` values and `max_diff_pixels` are out of scope as *fixes*. (Raising a *test-local execution budget* is permitted when the budget sits below the work the test must do — precedent: `platform-c67.2.spec.ts` M9-C71, `test_m9_c50_operational_lineage.py`.)
- **No test may be skipped, marked xfail, or have an assertion relaxed to go green.**
- **No verification gate may be suppressed, bypassed, or reclassified to make a failure disappear.**
- **Every unit of work lands as its own PR** and must leave `main` green on the four ruleset contexts (Backend Verification, Frontend Verification, Runtime Verification, Analyze) *and* on Verification Reconcile, which is not required but is the real gate.
- **Dead code is not removed on a hunch.** Analyse whether a thing is useless for the current setup first. (`run_api_contracts.sh` is a worked example of the right treatment — see W24.)

---

## 1. Correction to the audit record

The isolation audit stated `TypeScriptSymbolResolver` "reads its cache with no mtime validation at all". **That is wrong.** `typescript_symbol_resolver.py:271` reads `st_mtime` and `:280` compares it against the cached value. Its real defect — no pruning, no dirty flag, whole-cache re-serialisation on every extraction, 7.8 MB — was already fixed in `59e4e697`. **Do not schedule work against the stale claim.**

---

## 2. Tier 0 — Gate integrity (first, because everything after depends on trusting the gate)

### W0. The reconcile gate is inert for the entire runtime test tree

**Verified:** `verification.yaml` has 13 capability `modules:` lists; **none** contains `runtime`, `runtime/tests`, or a substring matching any `runtime/tests` path. Two capabilities declare `modules: []` (lines 430, 439). Running `CapabilityResolver._classify_change` over all 154 `runtime/tests` paths yields `source_change` → **0 capabilities resolved**, and the full `resolve()` path yields `unmapped_blast_capabilities == []` only because the planner/stem-suppression path happens to absorb them.

**Consequence:** a change to any runtime test resolves to no verification obligation. The gate neither constrains nor protects a runtime-test refactor — which is precisely the work this plan schedules.

**This is a decision, not a one-line fix, and must be settled before W19–W22 begin.** Three options:

| Option | Effect | Cost / risk |
|---|---|---|
| **A.** Add `runtime/tests` to `runtime-verification.modules` | Runtime tests map to the runtime obligation | Every runtime-test PR triggers `run_runtime_verification.sh` (~18 min). Changes Task-0 scope; the reconcile boundary would grow. |
| **B.** Add a dedicated `test-suite` capability scoped to `runtime/tests`, workflow `quality` | Precise ownership; cheap obligation | New capability = new architectural surface. The brief forbids inventing layers to make things pass, though this is not that — but it still needs a real owner. |
| **C.** Leave as-is and accept that the gate does not cover runtime tests | Zero cost | The gate cannot detect an unmapped runtime test. **Not acceptable if W19–W22 proceed.** |

**Recommendation: A**, scoped to `runtime/tests` only (not `runtime`, which would also capture the framework source). Validate by classifying all 154 paths after the change and confirming each resolves to exactly one capability with no collisions.

**Gate for W0:** decide and land before W19. If A, the first runtime-test PR after it lands must show a non-empty reconcile boundary.

### W1. A test rewrites the real `verification.yaml` in place — repo-integrity hazard

`runtime/tests/test_f006_configuration_divergence.py:29` and `:58` open `Path("runtime/foundation/verification/verification.yaml")` — CWD-relative, resolving to the **tracked production config** — write `coverage_threshold: 999`, and restore in a `finally`. A process kill inside that window (the suite's documented 30 s per-test failure mode) leaves the production config permanently corrupt. It also calls `reload_config()`, whose LRU is process-wide, so an unrelated reader observes 999 for the rest of the session.

**Fix:** copy the file to `tmp_path`, point `config_loader.DEFAULT_YAML_PATH` at the copy for the duration, restore the patch in a fixture with `try/finally` + `monkeypatch` (auto-undo even on failure). The real file is never opened for writing.
**Validation:** `pytest runtime/tests/test_f006_configuration_divergence.py runtime/tests/test_config_divergence.py`, then assert `git diff --exit-code runtime/foundation/verification/verification.yaml` is clean afterwards.
**Risk:** low.

### W2. A test's cleanup pass is pointed at the real `runtime/generated/`

`evidence_retention.py:91` — `self._generated_dir = generated_dir or GENERATED_DIR`, where `GENERATED_DIR = REPO_ROOT/runtime/generated` (line 29-30), **ignoring CWD**. `test_evidence_cleanup_stress.py:67,92` call `cleanup(dry_run=False)` against it. Today 0 artifacts are expired so nothing is deleted; the instant any `m9-cXX` directory crosses 90 days, running the test `rmtree`s real certification evidence.

Compounding: the test's fixtures are named `m9-c99-test`, `m9-c99-preserve`, `m9-c99-locked`, `m9-c99-corrupt`, `test_milestone_99`, none of which match `_RE_MILESTONE_DIR = ^m9-c\d+(\.\d+)?/?$` — so the retention semantics are **never exercised**. Destructive *and* vacuous.

**Fix:** `EvidenceRetention(generated_dir=tmp_path)` in the test; rename the fixtures so they match the policy regex so the test actually tests the policy; add an assertion that the scan target is inside `tmp_path`.
**Validation:** single-module run, then confirm no file under `runtime/generated` changes mtime.
**Risk:** low.

### W3. Tests assert on CWD-relative leftover artifacts

**Verified reproduction:** `test_m9_c50_operational_validation.py:677-680,698-701` read `Path("runtime/generated/…")`. From the repo root the two tests **pass with zero scenarios recorded** (they read a committed artifact containing 1 run); from any other CWD the same two tests **fail** with `FileNotFoundError`. A false green, which is worse than a flake.

**Fix:** assert on the in-memory `recorder.runs`, not a file; where a file is genuinely under test, anchor it to `tmp_path`. Add a repo-root fixture to `runtime/tests/conftest.py` (it already has a `repo_root` fixture, but it returns `tmp_path` — a synthetic root, not the real one).
**Validation:** run the module from `/tmp` as well as the repo root; both must pass.
**Risk:** low.

---

## 3. Tier 1 — Performance (measured wins, low risk)

### W4. Memoise `ExecutionOrchestrator.build_execution_plan` — ~85–100 s

**Verified:** 23 call sites in `runtime/tests` across 5 files (`test_m9_c49.py`, `test_m9_c50.py`, `test_m9_c51.py`, `test_m9_c50_operational_lineage.py`, `test_m9c57_verification_self_contract.py`). Measured **3.30–4.44 s per call with no warm-up benefit** — a fresh orchestrator per call does not help because nothing is memoised.

**Fix:** a single memo on the *plan* keyed by `(repo_fingerprint, frozenset(changed_files), frozenset(command_overrides))`. The third element is required: tests pass different `command_overrides`, and the plan depends on them. Invalidate on repo-fingerprint change.
**Validation:** the 5 affected modules green; assert the second call is <0.1 s; assert two different override sets do not share a memo entry.
**Risk:** low. **Highest ratio of saving to diff size in the whole audit.**

### W5. Eliminate recursive nested pytest — 386.66 s, 34% of the suite

**Verified call sites:** `test_m9_c55.py:125, 240, 499, 513, 952` and `test_m9_c53.py:675, 699, 723`. These re-execute whole modules (`test_m9_c54.py` ×3, `test_m9_c50.py`, `test_m9_c52.py`/`c53`/`c54`) through subprocesses while the outer run is *already executing those modules*. `test_m9_c55.py:499`+`:513` runs `test_m9_c54.py` twice for a reproducibility experiment.

**Fix:** assert the gate **functions** in-process instead of re-running modules. For the reproducibility experiment, call the function twice rather than the module twice via subprocess. Keep every assertion; only the *mechanism* by which the contract is checked changes.
**Validation:** each affected module green; the full runtime suite must drop from ~1800 s to ~1400 s; no assertion removed (diff the assert count before/after).
**Risk:** **medium** — these are the "prior milestone's tests still pass" gates, which encode real CI-history intent. Do this with the assert-count check as an explicit gate.

### W6. Session-scoped `doctor`/`plan` fixtures — ~139 s from 9 spawns

**Verified:** `test_m9c66_repeatability.py` spawns `runtime.verify doctor` ×5 and `plan` ×2 (≈10.5 s each); `test_m9c57_verification_self_contract.py` adds an `npx eslint --version` cold start (13 s) and a `doctor` run. `resolve_environment()` memoisation (landed in `59e4e697`) has already cut this from ~19 spawns.

**Fix:** one `session`-scoped fixture computing `doctor` and `plan` once, shared by both files; the 2×/3× repeatability assertions consume the cached outputs — a repeatability claim about a *deterministic read-only command* is about determinism, not about re-spawning the interpreter.
**Caveat:** keep one live spawn per command as the authority so the memo is not the only thing exercised.
**Risk:** low.

### W7. Delete the 1,262-line uncollected byte-clone

**Verified:** `diff runtime/tests/audit_final_freeze.py runtime/tests/test_m9_c50_stop_gate9_failure_modes.py` → **2 lines** (one added `sys.path.insert`). `audit_final_freeze.py` has no `test_` prefix, so pytest never collects it (root `pyproject.toml` `testpaths` + default `python_files`). It is a mirror no fix to the collected copy will ever reach.

**Fix:** reconcile the one-line delta, then delete the uncollected file. **But** see W17 — the surviving file's `startswith` prefix filter must be fixed in the same PR, because the filter currently spans both copies.
**Validation:** `--collect-only` item count unchanged before/after; the surviving harness still runs and still audits 13 files (assert the count).
**Risk:** low, but do not land before W17.

---

## 4. Tier 2 — Remaining correctness defects

### W8. `config_loader` serves stale config — reproduced

`config_loader.py:28` is `@functools.lru_cache(maxsize=1)`. Measured: after rewriting the YAML, a second read still returns the old value. `maxsize=1` also means any call with a different path **evicts** the no-arg entry that `get_threshold`/`get_config`/`check_configuration_divergence` rely on.

**Fix:** key the cache on `(path, mtime, size)`, or drop it. Prefer dropping it if profiling after W4/W6 shows the load is no longer hot.
**Validation:** a test that writes, re-reads, and observes the new value; plus the W1 rewrite no longer needs `reload_config()` as a correctness crutch.
**Risk:** low.

### W9. Symbol cache lost update — reproduced

`SymbolExtractor.__init__` takes a private snapshot; `_save_cache` rewrites the whole snapshot. Two extractors built before either extracts → the first entry is lost (reproduced: `a.py` gone after `b.py` is cached). Bounded in a strictly sequential run, unsafe under `xdist` or any extractor held across a boundary.

**Fix:** reload-and-merge under a file lock at save time, or a single in-process writer. Prefer a small `fcntl.flock` on a sidecar lock file — no new dependency.
**Validation:** the two-extractor reproduction becomes a regression test.
**Risk:** low.

### W10. `_classify_change` route matching over-matches

`capability_resolver.py` route branch matches with `feature in cap_id`, where `feature` is the first path segment. For `frontend/app/platform/…`, `"platform"` is a substring of all 23 `frontend:route:frontend-platform:*` ids. One changed page claims all 23 routes, inflating the blast radius and scheduling obligations the change does not touch.

Note this is **not** the fabricated cashflow owner fixed during stabilization — that one named a *wrong* capability; this one names the *right* capability in an over-broad set, so it only over-schedules.

**Fix:** match on path segments (`route_path in cap_id` already does this) and drop the substring test.
**Validation:** classify one `frontend/app/platform/**` path → exactly one route capability, not 23; the unmapped set stays empty; reconcile boundary for a platform-page change is unchanged in *capability* terms.
**Risk:** medium — this is planner matching logic and the brief reserved planner redesign. Scope it strictly to the substring test; do not restructure `_classify_change` in the same PR.

---

## 5. Tier 3 — Parameter consolidation (23 groups)

### W11. Credit-card rate bound has **already** diverged — needs a human decision first

**Verified:**
```
backend/tests/properties/credit_card_engine/test_emi_properties.py:16
    MAX_INTEREST_RATE_BPS = 3600  # 36% annual
backend/tests/properties/credit_card_engine/test_interest_properties.py:21
    MAX_INTEREST_RATE_BPS = 4800  # 48% annual (max for credit cards)
```

Same engine, same constant name, two values, no reconciliation. `backend/src` has **no** domain-limit constants, so the engine does not validate these bounds — there is no authority to defer to.

**This is a decision, not a refactor.** Someone must choose 3600 or 4800 (or scope them per-test), because the choice changes which inputs the property tests exercise and may surface or hide real engine defects. `backend/src` validation is a 30-minute grep and should be done before the choice.
**Validation:** after the decision, the full `backend/tests/properties` suite green.
**Risk:** medium — this one can legitimately turn up a real bug. That is the point.

### W12. Loan bounds and strategies → one home

**Verified:** 6 files each declare 2 of the loan bound constants (12 sites), plus `loan_parameters` duplicated 5× (byte-identical, ~15 lines each), plus two disjoint date windows (`date(2000,1,1)`–`date(2030,12,31)` in the files vs 2020–2030 in `properties/conftest.py:79`).

**Fix:** move the bounds, `loan_parameters` and the date window into `backend/tests/properties/conftest.py`, which already hosts 9 reusable strategies. Import them. **Safe only because the values are presently equal** — assert equality across the 6 files in the PR description before landing.
**Risk:** low.

### W13. `max_examples` — hoist now, profile later (two PRs)

**Verified:** **217** `max_examples=` occurrences across 24 files — 95× `20`, 37× `50`, 35× `30`, 26× `10`, 23× `5`, 1× `25`. `backend/tests/fixtures/hypothesis.py` registers profiles (ci 500 / dev 50 / fast 20 / normal 150 / deep 1000) and `properties/conftest.py` has a **second, divergent** table — same `HYPOTHESIS_PROFILE` env var, two answers, and the hard-coded values bypass both.

- **PR 1 (safe, behaviour-preserving):** hoist to named constants holding today's exact values in `fixtures/hypothesis.py`. Do **not** normalise the 20/30/50/5/10 spread — that would change coverage.
- **PR 2 (behavioural, needs explicit approval):** switch to profile resolution. This makes `HYPOTHESIS_PROFILE=deep|ci` actually change example counts, which alters runtime *and* the strength of every property claim. Separate PR, explicit sign-off, and delete the duplicate table in `properties/conftest.py`.

**Risk:** PR 1 low; PR 2 high — flag it, don't fold it in.

### W14. Replace 28 hand-computed `parents[n]` repo roots

**Verified: 28 files** compute the repo root as `resolve().parent.parent` (or `parents[n]`). Two use `parents[1]` for a *different* intent and must be read individually, not bulk-edited:
- `test_engineering_intelligence.py:393` — `parents[1]` is deliberately `runtime/`, then `/foundation/intelligence/platform/ci.py`. **Wants the package dir, not the repo root.**
- `test_m9_c67_1_platform_api.py:509` — `parents[1]/".."/"backend/…/platform.py` inside `if router_path.exists(): … pass`. **A dead no-op branch.**
- `test_ai_orchestrator_run_id_containment.py:24` uses `parents[3]` = the **parent of the repo root**. Currently harmless (editable install), and it stays harmless — but any "fix" must not assume the current value is correct.

**Fix:** import `REPO_ROOT`/`VENV_BIN` from `runtime/foundation/verification/env.py` (already the established anchor, used by 18 production modules). Handle the three special cases by hand.
**Risk:** low, but it is a **prerequisite for W19** and must land before any directory move.

### W15. Consolidate the 5 `run_verify` wrappers

`test_m9c66_stale_evidence.py:22`, `test_m9c66_repeatability.py:20` (byte-identical), `test_m9c66_adversarial.py:18` (**default timeout 60, not 30**), `test_m9_c49_canonical_cli.py:23` (`sys.executable runtime/verify.py`), `test_cli_contract.py:17` (class method, omits `cwd=REPO_ROOT`).

**Fix:** one module-level `run_verify()` in `runtime/tests/conftest.py` (a plain function, not a fixture — it is a subprocess helper). Keep the 60 s default in the adversarial file explicit at the call site so the difference stays visible rather than being silently normalised. `cwd=REPO_ROOT` everywhere, which also removes the `runtime.platform` stdlib-shadowing fragility.
**Risk:** low.

### W16. Adopt `child_process_env()` in 4 test files — behavioural

`test_backend_evidence.py:183`, `test_changed_file_parsing.py:230`, `test_repository_identity_resolution.py:42`, `test_cross_layer_planner.py:459` pass raw `os.environ` to children, omitting `TZ=UTC`, `LC_ALL=C.UTF-8`, `LANG=C.UTF-8` and the venv-first `PATH` that `env.child_process_env()` provides and 3 production modules already use.

**This changes behaviour on any non-UTC machine** (date formatting, `PATH`-dependent tool resolution). It is a correctness improvement, but it is its own commit with a per-module verification run.
**Risk:** medium — do not bundle with W15.

---

## 6. Tier 4 — Naming and regroup (largest, riskiest; strictly sequenced)

**Context:** `pyproject.toml` already registers 11 verification-kind markers and `backend/tests` already encodes kind in the directory. `runtime/tests` encodes *milestone* in the filename and 150 of 152 files use no registered marker. Six milestone dialects coexist (`m9_cNN`, `m9cNN`, `m9_c42_NN`, `vea5_mN`, `vea5`, bare `cNN`/`fNN`/`eN`/`oN`).

**The reconcile gate will not protect any of this.** All 154 `runtime/tests` paths resolve to zero capabilities before *and* after any rename, so the gate is inert in both directions. The real checklist is §7 below. **This is why W0 must be settled first.**

### W17. Freeze the prefix filter — before anything else
**Verified:** `audit_final_freeze.py:1035` and `test_m9_c50_stop_gate9_failure_modes.py:1036` both use `path.startswith("runtime/tests/test_m9_c50")`. After a rename that matches **1** file instead of 13, the harness still exits 0 auditing almost nothing, and **no test asserts the scope count**. The most dangerous item in the whole plan, and it produces no error.
**Fix:** convert to an explicit sorted path list and **assert the expected count**, so a future regression is loud. Land before any rename.

### W18. Land W14 before any directory move
21 of the 28 files sit at depth 2; `parents[2]` there is the repo root, and inside a subdirectory it silently becomes `runtime/`. Loud (`ImportError`) unlike W17, but still avoidable. W14 makes the locator depth-independent.

### W19. R4 wave — in-place renames only, no directory moves
Retire the leading `m9`/`m9c`/`vea5` tokens in place, flat. Zero depth risk, zero filter risk, and it kills 5 of the 6 dialects on its own. Highest value per unit of risk in this tier.

### W20. Create the 14 category directories and move files in
**One directory per PR.** A depth bug is then isolated to a small blast radius. Keep `conftest.py` at `runtime/tests/` root — it is the session hook and the progress tracker; moving it changes collection behaviour repo-wide. Basenames must stay globally unique (`runtime/tests` has no `__init__.py`).

### W21. Reconcile the harness pair
Then move it to `runtime/harness/` and drop the `test_` prefix (it collects zero tests). Do it with W7.

### W22. The 8 hard blockers — last
`test_m9_c50/51/52/53/54/55.py`, `test_m9_c49.py`, `test_m9_c44_mutation_architecture.py` — **30 hard reference sites** including `regression.py`/`certification.py` `_run_tests()` invocations, the `G25` gate's `.exists()` checks in `workflow_convergence.py:2283-2286`, a node-id in `route_authority.py:164`, and self-assertions in `test_m9_c54.py:611` / `test_m9_c55.py:958`. These are simultaneously the most misleading names (§5.9 of the audit) and the most dangerous. **One rename per PR**, each updating all referencing sites in the same commit.

---

## 7. Tier 4 checklist (the gate will not do this for you)

- [ ] 8 hard-blocker files, 30 reference sites — including a fail-closed `.exists()` gate
- [ ] 28 `parents[n]` sites, 3 of which use a different intent deliberately
- [ ] `startswith("runtime/tests/test_m9_c50")` — scope 13 → 1, silently
- [ ] `.github/actions/download-runtime/action.yml:49` references a test filename in a comment
- [ ] 36 `m9_c48_*`/`m9_c50_*` files carry a self-referential `# runtime/tests/<self>.py` header
- [ ] 12 `platform_api` phase files are split across two roots (phases 3/4/6 in `backend/tests/integration/`, the rest in `runtime/tests/`); **phase 5 has no tests at all**
- [ ] Pre-existing dead refs: `certification.py:98-123` names `test_m9_c42.py` and `test_m9_c48.py`, neither of which exists (guarded by `if …exists()`, so inert)

---

## 8. Tier 5 — Remaining Playwright flake surface

### W23. `networkidle` — 77 occurrences across 11 specs
The largest remaining flake surface in the E2E suite. Fixed only in the two bundle-size tests so far, where `load` was both sufficient and correct. The other 75 are not byte measurements and were left alone for lack of evidence.
**Do not** blanket-replace. Per spec, establish whether each site actually needs total network quiet; replace with the specific state the assertion depends on (`load`, `domcontentloaded`, a named selector, or an explicit API-response wait). One spec file per PR, each with the full suite green after.

---

## 9. Open items from the stabilization itself

### W24. `run_api_contracts.sh` is unreferenced by live config
**Verified: 0 references** in `verification.yaml` or any workflow. `api-contracts.yml:65` calls `.venv/bin/python -m runtime.verify contracts` directly, and the capability is registered in the workflow registry under that profile. Only historical `runtime/generated/**` artifacts mention it.
**Per the dead-code policy, analyse before declaring dead:** confirm `verify.py contracts` covers the script's full scope (structural, generated-code reproducibility, drift-proofing) before removing. If it does not, the *script* is the thing that should be wired back in. **Do not delete on the observation that it is unreferenced.**

### W25. Diagnose `exec-0009`
The non-mandatory whole-repo coverage measurement (`verify.py measurement coverage .`) fails on CI with `completion_status: INFRASTRUCTURE_FAILURE` after ~200 s. The system behaved correctly — `is_authoritative: false`, `may_certification_consume: false`, so incomplete evidence was refused and certification proceeded. The underlying cause is **undiagnosed**.
Now diagnosable: the reconcile workflow uploads `m9-c49/logs/` and `verification-progress/` (landed in `460df5bd`). Reproduce by downloading the artifacts from a failing run and reading `exec-0009-stderr.log`.

---

## 10. Sequencing

| PR | Work | Depends on | Risk |
|---|---|---|---|
| 1 | W0 — decide and register `runtime/tests` coverage | — | decision |
| 2 | W1 + W2 + W3 — test isolation and repo-integrity | — | low |
| 3 | W4 — memoise `build_execution_plan` | — | low |
| 4 | W6 — session `doctor`/`plan` fixtures | W4 | low |
| 5 | W7 + W17 — delete the clone, freeze the prefix filter | — | low |
| 6 | W5 — remove recursive nested pytest | W4, W6 | **medium** |
| 7 | W8 + W9 — config cache, symbol-cache locking | — | low |
| 8 | W11 — credit-card bound decision (**human sign-off**) | — | medium |
| 9 | W12 + W13(PR1) — loan bounds, `max_examples` hoist | W8 | low |
| 10 | W14 + W15 — `REPO_ROOT`, `run_verify` | — | low |
| 11 | W16 — `child_process_env()` | W15 | medium |
| 12 | W10 — route matching over-match | — | medium |
| 13 | W19 — in-place renames | W0, W17 | medium |
| 14+ | W20 — directory moves, one per PR | W14, W19 | medium |
| n | W21, W22 — harness, then hard blockers | W20 | **high** |
| — | W23 — `networkidle`, one spec per PR | — | medium |
| — | W24, W25 — analyse before acting | — | low |

**Waves 1–5 are independent of the refactor and can start immediately.** W13(PR2) is deliberately excluded from this table — it needs its own approval.

---

## 11. What this plan does not do

- **No threshold changes.** No coverage, mutation or regression threshold; no `--timeout`; no `max_diff_pixels`. The only budget changes permitted are test-local execution budgets proven to sit below the work the test must do, each with a measured justification in its own commit.
- **No skips, xfails, or relaxed assertions.** W5's assert-count gate exists to prove this.
- **No gate suppression.** The reconcile unmapped gate, the four ruleset contexts, and the coverage/mutation authority rules all stay exactly as they are.
- **No planner or capability-registry redesign.** W0 and W10 are the narrowest changes that make existing behaviour correct and the gate honest.
- **No mass rename in one PR.** The rename wave is 20+ single-purpose PRs by design; the string references and `parents[N]` depth are not gate-enforced and a bulk change would be unreviewable.
