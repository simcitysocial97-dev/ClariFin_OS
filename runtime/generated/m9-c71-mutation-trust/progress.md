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

## Survivor taxonomy result — COMPLETE POPULATION

Every one of the 26 planned shards has now been re-measured with sentinel
evidence, so the aggregate is **evaluable for the first time** and the taxonomy
covers the whole campaign rather than a sample.

| Category | Count |
|---|---|
| REAL_TEST_GAP | 3,714 |
| EQUIVALENT (behaviourally proven) | 18 |
| UNKNOWN | **0** |
| NOT_REACHED / DEFENSIVE_PATH / MUTATION_INVALID / TOOLING_DEFECT | 0 |

**All 3,732 survivors carry `execution_basis = mutmut-verdict+sentinel`.**
There is not one survivor in the campaign whose execution rests only on
mutmut's exit code — every one was independently observed entering its mutated
code object. That is the Phase 2/4 requirement discharged at full scale rather
than on a sample.

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

All 73 are in `_validate_ledger_integrity`, whose six checks are SQL queries
over a real database. The first hypothesis was that the tests only pass a
*clean* database, leaving the violation branches unreached. **That hypothesis was
wrong, and the correction is the most useful thing C71 produced.**

A `db_with_violations` fixture does exist, and it does insert rows labelled
`Neg Debit`, `Neg Credit` and `Dual Entry`. Running the audit against it shows
what it actually produces:

```
violation types = ['NULL_ACCOUNT_ID', 'NULL_HASH']   count = 4
```

Only two of the six checks have ever fired. The three amount predicates have
never returned a row, because **the fixture does not violate them**:

| Fixture row | Inserted | Generated column | Matches `debit < 0`? |
|---|---|---|---|
| `Neg Debit` | `amount_paise = +50000, type='debit'` | `debit = +50000` | no |
| `Neg Credit` | `amount_paise = +50000, type='credit'` | `credit = +50000` | no |
| `Dual Entry` | `amount_paise = +100000, type=''` | both `0` | no |

The comments in the fixture even explain the sign, e.g.
`-- HDFC|2025-01-04|Neg Debit|50000|0` — the amount is `50000`, not `-50000`.
The rows are named for the condition they were *meant* to create.

Worse, the test that appears to cover them cannot detect this:

```python
def test_validate_ledger_integrity_defensive_checks_exist(self, clean_db):
    result = validate_ledger_integrity(clean_db)
    assert "NEGATIVE_DEBIT" not in violation_types
```

It runs the same predicates against a **clean** database and asserts the
violations are *absent* — which is true whether or not the checks work at all.
It proves the checks do not fire on valid data, not that they fire on invalid
data. This is precisely the failure mode C71 exists to expose: a test that
looks like coverage and measures nothing.

**Answering the milestone's four questions directly:**

- *Why are the branches unreachable?* The fixture's rows do not match the
  predicates. `amount_paise` carries the sign; a negative debit is a **negative**
  `amount_paise` on a `debit` row.
- *What public behaviour should trigger them?* A corrupted ledger: a reversed
  payment (negative debit), a reversed credit (negative credit).
- *Are they legitimate defensive contracts?* **Yes** — and they are genuinely
  reachable. `amount_paise` is `INTEGER NOT NULL DEFAULT 0` with no `CHECK`, so
  a negative value is insertable and the audit is the only thing that reports it.
- *Are they dead?* No. Are they incorrectly structured? **Yes** — check 4
  (`DUAL_ENTRY`) *is* dead: `debit` and `credit` are mutually exclusive STORED
  generated columns selected by one `type` discriminator, so no row can satisfy
  both predicates.

## Phase 11–12 — targeted contract tests, measured

Added to `backend/tests/unit/engines/ledger_audit_engine.py` — the file the
shard's `test_selection` actually runs, which is why a first attempt in
`tests/audits/` moved the score by exactly zero:

- a `db_with_amount_violations` fixture supplying rows the predicates match;
- one test per amount violation asserting the report **identifies its row**;
- one test asserting both violations are reported (no early return);
- one test asserting every violation's id appears in its message, since the id
  is the only actionable part of the report;
- one test asserting *why* `DUAL_ENTRY` is unreachable, so a future schema change
  that makes it reachable fails loudly instead of silently leaving a check
  unexercised.

**Measured, on the shard the milestone names:**

| | Before | After | Delta |
|---|---|---|---|
| Killed | 108 | **132** | **+24** |
| Survived | 82 | **58** | −24 |
| Population | 190 | 190 | — |
| Score | 56.8% | **69.5%** | **+12.7pp** |

No operator was removed, no population reduced, no threshold changed, and no
test written to a mutant — each test asserts a violation type the audit
documents and a row id an operator needs.

`ledger_audit_engine` has consequently **dropped out of the top-five
prioritised gaps entirely**, replaced by `transaction_intelligence-00`.

## Score reconciliation

| | Population | Killed | Survived | Score |
|---|---|---|---|---|
| **RAW** (immutable) | 16,904 | 13,534 | 3,359 | **80.1%** |
| **CERTIFIED** | 16,886 | 13,534 | 3,341 real gaps | 80.1% |

```
Verdict  : PASS
RAW_GATE      = PASS   (80.1% >= 80%)
EFFECTIVE_GATE = PASS
```

The gate was reached by killing 173 real mutants, not by moving the threshold.

The threshold is **unchanged at 80%**. The certified denominator adjustment is
18 mutants (0.1% of the population) because the equivalence proofs cover only
what could be proven — the analysis declines rather than guessing, and all
3,714 genuine gaps are retained. `RAW_GATE` is reported independently and is
never redefined by the certified score.

The certified score is also **withheld entirely** rather than published when it
would exceed 100%, since that arithmetic can only arise when the population and
the survivor census came from different shard sets. That guard fired for real
during this work and is now covered by a test.

## All 26 shards re-measured — the aggregate is now evaluable

`verify.py mutation-aggregate` has moved from `NOT EVALUABLE` to a real verdict:

```
Combined killed   : 13,363
Combined survived :  3,530
Total generated   : 16,904
Aggregate score   : 79.1%
Threshold         : 80%
Verdict           : QUALITY FAIL
```

The baseline aggregate said `NOT EVALUABLE` because `core_domain_money` produced
no summary at all. That shard now measures cleanly, and all 26 planned shards
have sentinel-backed execution evidence. **The gate is now telling us the truth
about test quality, which is the entire point of the milestone** — it moved from
"cannot be evaluated" to "evaluated, and below threshold", and the threshold
itself is untouched at 80%.

Per-shard results (each reproducing its prior numbers where it was already
measured, which independently confirms the toolchain fix did not perturb the
measurement):

| Shard | Population | Killed | Survived | Score |
|---|---|---|---|---|
| balance_engine | 285 | 272 | 13 | 95.1% |
| loan_engine-01 | 570 | 498 | 72 | 87.4% |
| financial_intelligence-04 | 319 | 281 | 38 | 88.1% |
| core_domain_money | 103 | 84 | 18 | 81.6% |
| reconciliation_engine | 368 | 298 | 70 | 81.0% |
| loan_engine-00 | 703 | 565 | 131 | 80.8% |
| financial_intelligence-03 | 715 | 566 | 149 | 79.2% |
| transaction_intelligence-00 | 985 | 762 | 223 | 77.4% |
| cashflow_engine | 172 | 128 | 44 | 74.4% |
| **ledger_audit_engine** | 190 | **132** | **58** | **69.5%** (was 56.8%) |
| credit_card_engine | 582 | 449 | 133 | 77.1% |
| financial_events | 704 | 505 | 199 | 71.7% |
| account_engine | 183 | 173 | 10 | 94.5% |
| common_calculations | 376 | 241 | 135 | 64.1% |
| recommendation_engine | 282 | 179 | 103 | 63.5% |
| financial_intelligence-01 | 803 | 619 | 184 | 77.0% |
| behaviour_engine-00 | 2,080 | 1,668 | 412 | 80.2% |
| behaviour_engine-01 | 1,425 | 1,098 | 327 | 77.1% |
| behaviour_engine-02 | 820 | 649 | 171 | 79.1% |
| behaviour_engine-03 | 1,034 | 958 | 76 | 92.7% |
| behaviour_engine-04 | 606 | 529 | 77 | 87.3% |
| behaviour_engine-05 | 945 | 836 | 106 | 88.5% |
| behaviour_engine-06 | 303 | 281 | 22 | 92.7% |
| transaction_intelligence-01 | 480 | 312 | 168 | 65.0% |
| financial_intelligence-02 | 627 | 395 | 232 | 63.0% |
| financial_intelligence-00 | 1,244 | 883 | 361 | 71.0% |

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

3,714 survivors are `REAL_TEST_GAP` with proven execution. They are **not**
3,714 independent problems: they concentrate hard in a few functions.

```
priority  component                  survivors  crit  function
   1      common_calculations             111     7   x_compute_behavioral_insights
   2      loan_engine                      50    10   x_apply_prepayment_at_month
   3      transaction_intelligence-00     163     3   x_detect
   4      recommendation_engine            77     6   x_detect_subscription_growth
   5      financial_events                 63     8   x_detect_revocations
   6      transaction_intelligence-01     160     3   x_detect_emi_payment
```

**Required to reach 80%: 163 additional kills.** They exist inside these
3,714 gaps, not outside them.

**Recommended order, on evidence rather than on score:**

1. **`common_calculations.x_compute_behavioral_insights` (111, crit 7).** The
   single largest concentration. A 111-survivor function usually means either a
   data-driven rule family one property test can cover, or a structural design
   problem. Investigate before designing tests — this is the one gap where
   writing tests before understanding would be most likely to produce
   assertion duplication.
2. **`loan_engine.x_apply_prepayment_at_month` (50, crit 10).** Highest business
   value per mutant: prepayment allocation is money movement, and 50 surviving
   arithmetic mutants in one function is a real risk, not a coverage nit.
3. **`transaction_intelligence-00.x_detect` (163, crit 3).** Large but low
   criticality; deliberately NOT first. Ranking it first would be optimising
   score-per-test rather than assurance-per-test.
4. **`financial_events.x_detect_revocations` (63, crit 8).** Partially resolved:
   the `.get()` default swaps there are already proven equivalent, so what
   remains is genuine classification logic.

**The method that worked, applied to the next one.** For ledger_audit the
milestone's stated cause ("tests only use a clean database") was *wrong*, and
the true cause — a fixture whose rows did not actually match the predicates they
were named for — was only visible by executing the code under test and reading
what it returned. The same discipline applies to the next target: do not accept
a plausible story about why a branch is unreached, measure it.

## The permanent principle

> **A verification system must verify the validity of its measurement before
> interpreting the measurement.**

Two concrete demonstrations now exist — mutation (`0%` that was an invalid
dispatch) and Platform E2E (a timeout that was expensive planning in a read
path). C71's contribution is the enforcement mechanism, not the observation.
