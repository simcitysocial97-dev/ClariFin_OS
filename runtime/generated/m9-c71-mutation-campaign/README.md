# M9-C71 — Mutation Campaign: Measurement-Integrity Root Cause + Sharded Campaign

**Status:** `TOOLCHAIN_CONTRACT_DEFECT_RESOLVED_CAMPAIGN_SHARDED`
**Scope:** reconcile the two open items from `m9-c70-workflow-convergence`
(the authoritative mutation campaign and the full Playwright green state)
without lowering a threshold, suppressing a test, or reclassifying a failure
as a success.

---

## 1. The 0.0% mutation score was a measurement artefact, not a test-quality gap

### What C70 recorded

> targeted `balance_engine` run `36238247482` produced `0.0%` with `285`
> survivors and correctly failed the `80%` gate

C70 classified this as a genuine mutation-detection quality gap: the tests fail
to kill mutants.

### What it actually was

mutmut 3.7.0 derives a mutant's module name from its **file path**:

```python
# mutmut/utils/format_utils.py
def get_mutant_name(relative_source_path, mutant_method_name):
    module_name = str(relative_source_path)[: -len(relative_source_path.suffix)].replace(os.sep, ".")
    module_name = strip_prefix(module_name, prefix="src.")   # <-- strips "src."
    ...
```

ClariFin_OS is not a setuptools "src layout": `backend/src` is a real top-level
package and production code is imported as `from src.engines...`. The mutated
module's trampoline dispatches each mutant by comparing mutmut's stripped,
path-derived name against the function's real module name:

```python
# mutmut/mutation/trampoline.py (pristine 3.7.0)
module, _, mutant_name = mutant_under_test.rpartition(".")
if module != decorated_func.__module__:
    # mutant of another module is active -> call original function
    return orig_func(*args, **kwargs)
```

`module` is `engines.balance_engine`; `decorated_func.__module__` is
`src.engines.balance_engine`. They never match, so **every mutant is dispatched
to the original function**. The test suite exercises unmutated code, passes for
every mutant, and the campaign reports a structurally impossible `0.0%` with
all mutants "survived". Gate A/B (execution and evidence integrity) pass — the
campaign is perfectly healthy; it is simply measuring nothing.

### The divergence that hid it

The local `.venv` happened to carry a hand-applied edit to
`site-packages/mutmut/mutation/trampoline.py` (plus a stray `trampoline.py.bak`),
so local runs reported real kill counts while a fresh
`pip install -e ".[all]"` environment — i.e. **every CI runner** — reported
`0.0%`. The declared dependency contract and the working toolchain had silently
diverged, and the divergence presented itself as a test-quality failure.

### Controlled proof

| Toolchain | Population | Killed | Survived | Score |
|---|---|---|---|---|
| pristine mutmut 3.7.0 (control, local) | 285 | 0 | 74 attempted of 285 when stopped | 0.0% |
| pristine mutmut 3.7.0 (CI run `36238247482`) | 285 | 0 | 285 | 0.0% |
| contract-conformant toolchain (local) | 285 | 272 | 13 | 95.4% |

Same commit, same selection, same population. The only variable is the
trampoline dispatch. Evidence:
`runtime/generated/m9-c71-mutation-campaign/toolchain-contract-proof.json` and
`.../control/pristine-trampoline-partial.log`.

**Classification correction:** the item C70 recorded as
`GENUINE_PRODUCT_GAP (test effectiveness)` is reclassified as
`TOOLCHAIN_CONTRACT_DEFECT (measurement integrity)`.

---

## 2. The contract: `runtime/foundation/verification/mutmut_contract.py`

The fix is materialised from repository code, not from a hand-edited venv, so
the declared dependency install and the working toolchain are the same thing
locally and in CI.

Properties:

- **version-gated** — refuses to modify anything but the pinned mutmut
  (`PINNED_MUTMUT = 3.7.0`).
- **region-scoped** — rewrites exactly the module-dispatch region, located by
  two stable anchors. The rest of the toolchain is left byte-identical.
- **idempotent** — re-running is a no-op once satisfied.
- **self-healing** — a hand-edited venv is detected (the region is not
  canonical) and re-derived canonically, instead of being trusted.
- **audited** — writes `backend/tests/generated/mutation/mutmut-toolchain-contract.json`
  with before/after/canonical SHA-256 digests, and every mutation summary now
  carries `toolchain_contract` so a measurement can always be traced to a known
  toolchain state.
- **fail-loud** — if the contract cannot be satisfied the campaign returns an
  `INFRASTRUCTURE_FAILURE`, never a `0%` quality result.

`mutation_runner.execute_mutation` enforces the contract *before* any execution
for smoke, targeted, incremental and full modes.

### Second, independent defect found while diagnosing

`mutmut`'s stdout/stderr was captured into a pipe and thrown away, so a mutation
failure produced no diagnosable evidence — the transcript that revealed this
root cause had to be reconstructed by hand. C71 now streams the mutmut
transcript to `backend/tests/generated/mutation/mutation-logs/<run_id>.log`,
attaches its repo-relative path to the summary and the measurement-truth record,
and keeps the full transcript in the CI shard artifact.

---

## 3. The campaign is now bounded and sharded

### Why the previous campaign could never finish

Component-level sharding is **not** bounded. Measured on 2026-09-26,
`behaviour_engine` alone carries **7 213 mutants** — roughly four hours on one
runner. The original single-process full campaign hit the 5400 s (90 min) wall
and was cancelled with no result at all (run `36233136018`). A cancelled
campaign yields no evidence, so the quality gate was permanently unsatisfiable.

### The shard contract

`runtime/foundation/verification/mutation_shards.py` packs every component's
files into deterministic, size-bounded shards:

- A shard is `(component, subset-of-component-files)`, keeping the component's
  test selection and also-copy contract. **The union of a component's shards IS
  the component** — asserted by test, so the aggregate can neither double-count
  nor silently shrink the certified population.
- Bound: `SHARD_BYTE_CAP = 24 KiB`, calibrated from the one data point we have
  (`balance_engine`, 11.6 KiB → 285 mutants → ~13 min). mutmut's unit of
  mutation is the file, so a file larger than the cap gets a shard of its own
  rather than being split; such shards are visible in the plan and fail
  explicitly if they exhaust their budget.
- A component that fits in one group keeps its component name as the shard id,
  so the common case reads exactly like the pre-sharding campaign.
- The plan is emitted by `verify.py mutation-plan` and consumed by the workflow
  via `fromJson(...)`; the shard list exists in exactly one place.

Result: **26 bounded shards** for 14 components (largest: `behaviour_engine-00`
at 32.8 KiB ≈ 1 400 mutants).

### The aggregate gate

`verify.py mutation-aggregate` is the single authoritative decision. It requires

1. every planned shard to be present (missing shard → `NOT EVALUABLE`);
2. every shard to have passed execution integrity (Gate A);
3. every shard to have a non-empty measured population (Gate B);
4. the combined population to meet the existing `mutation_thresholds.full_campaign`
   threshold — **the same unchanged 80%**.

The score is population-weighted across shards, never a mean of per-shard
percentages, so a tiny weak shard cannot be averaged away by a large strong one.
Exit codes: `0` satisfied, `2` measured but below threshold, `1` not evaluable.

### Workflow topology

```
mutation-smoke ─┬─> mutation-plan ──> mutation (26-shard matrix) ──> mutation-aggregate
                │                              │
                └──────────────────────────────┘
```

Smoke-first is preserved (it is a framework invariant), every job delegates to
one canonical `runtime.verify` command, and every shard uploads its summary,
measurement-truth record, survivor intelligence, toolchain contract and mutmut
transcript **even when it fails**, so the aggregate can report *why* rather than
"missing".

`runtime/tests/test_vea5_m8_merge_enforcement.py::test_m81` previously asserted
the mutation workflow had *exactly* two jobs. That assertion encoded the
single-process assumption that evidence has since falsified, so it was replaced
by a **strictly stronger** invariant: the exact four-job topology, the
smoke-first dependency, the plan→shard→aggregate chain, and a per-job pinned
canonical command.

---

## 4. Post-fix measurement status

| Shard | Generated | Killed | Survived | Score | Threshold |
|---|---|---|---|---|---|
| `balance_engine` | 285 | 272 | 13 | 95.4% | 80% |
| `cashflow_engine` | 172 | 128 | 44 | 74.4% | 80% |

`cashflow_engine` is a genuine measurement now and it genuinely reports 74.4% —
a real test-effectiveness gap (44 survivors, all in
`x_compute_monthly_cashflow`: 34 control-flow, 5 arithmetic, 4 comparison,
1 boolean). This is the first trustworthy per-component quality signal the
repository has produced; the remaining 24 shards are being measured through the
sharded campaign and any shard below threshold will be closed by strengthening
tests or correcting behaviour, never by relaxing the gate.

---

## 5. Invariants added

`runtime/tests/test_m9_c71_mutation_campaign.py` (41 tests) certifies:

- pristine toolchain → `VIOLATED`; `ensure()` → `APPLIED` → `SATISFIED`;
- hand-edited toolchain detected and re-derived, never trusted;
- unrecognised toolchain refused, never patched;
- unpinned mutmut version refused;
- the canonical venv this suite runs against is **in contract**;
- evidence record is durable and digest-backed;
- a component's shards partition its population exactly once;
- shards are bounded; ids are deterministic and unambiguous;
- missing / empty / infrastructure-failed shard ⇒ explicit failure;
- population-weighted scoring;
- targeted campaigns are still gated at 80%;
- both new entrypoints are CANONICAL and dispatch through the single control
  plane;
- the workflow's smoke-first sharded topology and always-upload evidence.
