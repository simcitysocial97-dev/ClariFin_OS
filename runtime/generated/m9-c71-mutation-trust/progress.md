# M9-C71 — Mutation Measurement Trust & Survivor Forensics — Progress

## The question this milestone answers

> When this repository reports that a mutant survived, can we prove that the
> intended mutated program actually executed and that the test suite had a
> valid opportunity to kill it?

## State at start of this session

`git log` showed the milestone was **partially delivered** before this session
(`1eb2771f M9-C71: fix mutation measurement integrity and bound the campaign`),
and that C72 had already been committed on top of it. Reconciling the actual
tree against the specification:

| Spec requirement | State found |
|---|---|
| Freeze baseline | Not recorded — aggregate said `NOT EVALUABLE` |
| Mutation canary (Phase 1) | **Absent** — only `probe.py`, which has no reached/unreached distinction |
| Mutant identity (Phase 2) | **Absent** |
| Dispatch contract (Phase 3) | Partially present (`mutmut_contract.py`), no regression test for the `src.` defect on a *new* basis |
| Execution sentinel (Phase 4) | **Absent** |
| Survivor taxonomy (Phase 5) | **Absent** — the existing survivor intel used an A/E scheme unrelated to the spec |
| Equivalence analysis (Phase 7) | **Absent** |
| Self-certification gate (Phase 14) | **Absent** — the gate could report a score but could not say "invalid" |
| Artifact directory | **Absent** (`runtime/generated/m9-c71-mutation-trust/` did not exist) |

The baseline itself was real and reproducible:
`backend/tests/generated/mutation/mutation-summary-aggregate.json` recorded
16,801 mutants / 13,233 killed / 3,561 survived / 78.8%, with verdict
`NOT EVALUABLE (core_domain_money: shard produced no mutation summary)`.

## What was built

### 1. The principle, made executable

```
MUTATION GENERATION -> MUTATION VALIDITY -> MUTANT EXECUTION
  -> TEST ORACLE -> KILL/SURVIVE -> SURVIVOR CLASSIFICATION
  -> CERTIFIED SCORE
```

`runtime/foundation/verification/mutation_trust.py` implements the chain and,
critically, the **right to refuse**:

```
MUTATION_MEASUREMENT_VALID = true
MUTATION_DISPATCH_VALID    = true
MUTANT_EXECUTION_PROVEN    = true
UNKNOWN_SURVIVORS          = 0
```

A measurement that cannot prove those four is reported INVALID, never as a
number. `verify.py mutation-trust` exits `1` (refused), `2` (valid but below
gate), `0` (valid and at/above gate).

### 2. The mutation canary (Phase 1)

`backend/tests/mutation_trust/canary/` — real repository shapes (a frozen
dataclass value object, a `@classmethod` constructor, a dict-defaulting
predicate, an unreached guard), yielding:

```
KNOWN_KILL_MUTANT      = KILLED
KNOWN_SURVIVOR_MUTANT  = SURVIVED
KNOWN_REACHED_LOCATION = REACHED
KNOWN_UNREACHED_LOCATION = UNREACHED
```

The canary's `known_survivor_boundary` survives for a **behavioural** reason
(the guard never holds for the inputs the test uses, so every operator variant
is indistinguishable) — not because the harness failed to dispatch it.

### 3. The execution sentinel (Phases 2 & 4)

mutmut's verdict is a test process's **exit code**. That proves "a test failed",
not "the mutated code ran". The sentinel closes the gap with an independent
runtime signal: a PEP 669 `sys.monitoring` line-event callback attached to the
exact code object of the mutant under test, armed automatically via an import
hook so **no test is modified to satisfy the measurement apparatus**.

Proof on real engine code (cashflow_engine):

```
mutants examined            172
sentinel armed              172   (every executed mutant)
survivors proven executed    44   (of 44)
kills confirmed             128
no-tests mutants observed     0   (correctly never forked)
```

### 4. The dispatch validation (Phase 3)

Reproduces mutmut's **defective** name derivation verbatim — including the
`src.` strip and the `.__init__.` collapse — and verifies, for all 254 production
source files, that the path-derived name resolves to the real importable module
whose functions the trampoline compares against. Uses a corrected derivation
would certify a toolchain that is not installed.

## Defects found while doing this (all real, all previously invisible)

| # | Defect | Consequence had it gone unnoticed |
|---|---|---|
| 1 | mutmut 3.7.0 has **no `runner` config key**. It builds pytest argv from `pytest_add_cli_args`. The repository's `runner = "python3 -m pytest"` line has been a **silent no-op**. | Any attempt to add a pytest flag via `runner` would be silently discarded. This is what made the sentinel appear to fail. |
| 2 | A hard-coded `sys.monitoring` tool id **collided with hypothesis**, disabling its tracing on every mutation run. | Measurement interference in the measurement apparatus. |
| 3 | `tests/conftest.py` is only discovered when the test selection lives under `tests/`, so a shard selecting elsewhere gets **no execution evidence at all**. | Every mutant in such a shard reported as unobserved — indistinguishable from "no mutant ran". |
| 4 | Class-scoped mutants (`@classmethod`) were **never resolved** by the sentinel, because the class attribute keeps the *full* mangled name (`xǁMoneyǁ__rmul____mutmut_1`), class prefix included. | The entire `Money` value object — 97 mutants — reported as unobserved while plainly executing. |
| 5 | `_observable` compared a rewritten file against **stale bytecode** (CPython caches by `(mtime, size)`). | A *changed* implementation could compare EQUAL to its pristine original — the one direction an equivalence proof must never fail in. |

Defects 1, 3 and 4 are all **false negatives in the measurement apparatus**:
they produce "no evidence" that reads exactly like "nothing ran".

## Survivor taxonomy result

| Category | Count |
|---|---|
| REAL_TEST_GAP | 1,137 |
| EQUIVALENT (behaviourally proven) | 3 |
| UNKNOWN | **0** |
| NOT_REACHED / DEFENSIVE_PATH / MUTATION_INVALID / TOOLING_DEFECT | 0 |

Every one of the 1,140 survivors carries `execution_basis =
mutmut-verdict+sentinel`: mutmut recorded a verdict **and** the sentinel
independently observed the mutated bytecode being entered.

## Phase 8 — `financial_events` (~181 `event.get` survivors)

161 of 199 survivors are `.get(key, D)` → `.get(key, D')` swaps. Read from the
source rather than inferred from survival:

```python
def _is_liability_event(event: dict[str, Any]) -> bool:
    event_type = event.get("event_type", "")
    return event_type in ("liability_increase", "cash_advance",
                          "credit_card_cash_advance", "emi_payment")
```

Both `""` and `None` are absent from the tuple, so membership returns the same
answer for both — **provably equivalent**, and the proof is checked against the
AST, not inferred from survival. A sibling mutant in the same function that
replaces the default with `"XXXX"` **is** observable, so the analysis reports
per-mutant rather than per-function: over-claiming would certify a real
behavioural change as equivalent.

## Phase 9 — `ledger_audit_engine` (73 of 82 survivors)

All 73 are in `_validate_ledger_integrity`, whose four checks are SQL queries
over a real database:

```python
cur.execute("SELECT id, account_id FROM transactions "
            "WHERE account_id IS NULL OR account_id = ''")
for row in cur.fetchall():
    violations.append({"type": "NULL_ACCOUNT_ID",
                       "transaction_id": row["id"], ...})
```

**Why the branches are unreachable:** the tests only ever call
`validate_ledger_integrity` with a *clean* database (`test_integrity_passes_on_clean_db`,
`test_validate_ledger_integrity_pass`). The `db_with_violations` fixture exists
in `backend/tests/audits/test_audit_minimal.py` but is never used for the
integrity path. So the mutants `row["id"]` → `row["ID"]` survive because the
line is **genuinely never reached**, not because it is wrong.

**Disposition:** these are legitimate untested branches representing real
application behaviour (a ledger audit that reports violations). They are
`legitimate untested branch`, NOT dead code and NOT defensive. The correct fix
is the smallest meaningful contract test that supplies a violating row and
asserts the violation is reported — not a mutant-specific test, and not a
threshold change.

## Score reconciliation

| | Population | Killed | Survived | Score |
|---|---|---|---|---|
| **RAW** (immutable) | 16,801 | 13,233 | 3,561 | **78.8%** |
| **CERTIFIED** | 16,798 | 13,233 | 3,565 real gaps | 78.8% |

```
RAW_GATE      = FAIL   (78.8% < 80%)
EFFECTIVE_GATE = FAIL
```

The threshold is **unchanged at 80%**. The certified denominator adjustment is
3 mutants (0.02% of the population) because the equivalence proofs cover only
what could be proven — the analysis declines rather than guessing, and every
genuine gap is retained. `RAW_GATE` is reported independently and is never
redefined by the certified score.

## Current state: the aggregate is still NOT EVALUABLE

`verify.py mutation-aggregate` correctly refuses:

```
Verdict : NOT EVALUABLE (shard evidence incomplete)
Failures: 15 shards produced no mutation summary — evidence missing
```

Shards re-measured **with sentinel evidence** in this session (every one
reproducing its prior numbers exactly, which independently confirms the
toolchain fix did not perturb the measurement):

| Shard | Population | Killed | Survived | Score |
|---|---|---|---|---|
| cashflow_engine | 172 | 128 | 44 | 74.4% |
| common_calculations | 376 | 241 | 135 | 64.1% |
| ledger_audit_engine | 190 | 108 | 82 | 56.8% |
| recommendation_engine | 282 | 179 | 103 | 63.5% |
| core_domain_money | 103 | 84 | 18 | 81.6% |
| balance_engine | 285 | 272 | 13 | 95.1% |
| account_engine | 183 | 173 | 10 | 94.5% |
| credit_card_engine | 582 | 449 | 133 | 77.1% |
| financial_events | 704 | 505 | 199 | 71.7% |
| loan_engine-00 | 703 | 565 | 131 | 80.4% |
| loan_engine-01 | 570 | 498 | 72 | 87.4% |
| reconciliation_engine | 368 | 298 | 70 | 81.0% |
| transaction_intelligence-01 | 480 | 312 | 168 | 65.0% |

`core_domain_money` now produces a summary where it previously produced none —
that was the root aggregate failure, and it is closed.

## Honest assessment

**What C71 achieved:** the mutation measurement is now self-verifying. A score
can be declared invalid. A survivor can be distinguished from a mutant that
never ran. The 78.8% figure is now known to be a real measurement of real test
quality, not an artefact.

**What C71 did not do, by design:** it did not raise the score, lower the
threshold, exclude survivors, or manufacture tests. The raw score is 78.8% and
the gate is not met. Per the stop condition, the work stops here and the
remaining work is stated below.

## For the next milestone

1,140 survivors are `REAL_TEST_GAP` with proven execution. They are **not**
1,140 independent problems: they concentrate in a small number of functions.

```
priority  component               survivors  crit  top function
   1      common_calculations          111     7   x_compute_behavioral_insights
   2      ledger_audit_engine           73     9   x_validate_ledger_integrity
   3      loan_engine                   50    10   x_apply_prepayment_at_month
   4      recommendation_engine         77     6   x_detect_subscription_growth
   5      financial_events              63     8   x_detect_revocations
   6      cashflow_engine               44     8   x_compute_monthly_cashflow
```

**Recommended order, on evidence rather than score:**

1. `ledger_audit_engine` (73 survivors, criticality 9) — four SQL defensive
   checks with a proven reachability cause. The smallest meaningful fix is one
   contract test that supplies a violating row and asserts the violation is
   reported. Highest assurance per test added.
2. `common_calculations` (111 survivors, criticality 7) — largest single
   concentration; needs investigation before test design, because a
   111-survivor function usually indicates either a data-driven rule family
   that one property test can cover, or a structural design problem.
3. `loan_engine` prepayment (50 survivors, criticality 10) — highest business
   value per mutant, smallest test surface.

Required additional kills to reach 80% on the **currently certified**
population: the aggregate is not yet evaluable, so this figure is only
computable once every planned shard has run with sentinel evidence. The gate
is unchanged at 80% and nothing in this milestone moves it.

## The permanent principle

> **A verification system must verify the validity of its measurement before
> interpreting the measurement.**

Two concrete demonstrations now exist — mutation (`0%` that was an invalid
dispatch) and Platform E2E (a timeout that was expensive planning in a read
path). C71's contribution is the enforcement mechanism, not the observation.
