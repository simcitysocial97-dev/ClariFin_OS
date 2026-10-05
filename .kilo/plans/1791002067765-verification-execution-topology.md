# M10-R3 — Close the Execution-Condition Gap

**Status:** plan only. No files modified.

---

## 1. The question asked, answered directly

> *What is the use of the complex runtime framework we built over months?*

**It is authoritative about verification semantics, and completely silent about
verification execution conditions. Every defect this milestone lived in the silent half.**

The framework was never wrong. In ten CI defects it produced a correct verdict every
time — refusing to certify when shard reports were missing, naming the missing task ids,
catching a tree that drifted mid-run, propagating a `not_certified` upward instead of
laundering it. That is precisely what a certification authority is for, and it is not
disposable.

But it answers only *"what must run"*. It does not answer *"under what conditions"*.
Those conditions were therefore re-implemented, by hand, in every layer that spawns a
process — a shell-script guard here, a YAML `env:` block there, a `timeout` expression in
a third place — and **none of those copies is visible to the planner, the prerequisite
checker, or the aggregate.** They drifted, and they drifted silently.

### 1.1 The finding that settles it

`execution/task.py:90` already declares:

```python
required_environment: tuple[str, ...]
```

It is populated in eight places (`executor_pipeline.py:366,390,422,458,526,585,2173`),
serialised (`task.py:111`, `executor_pipeline.py:215`), and appears in test fixtures.

**It is never read by any enforcement path.** `verify_prerequisites` — the single
enforcement function in the codebase — reads `t.prerequisites`, not
`t.required_environment`. And every value ever assigned is a *tool or path*
(`.venv`, `pytest`, `mutmut==3.7.0`) — never an environment *variable*.

So the concept was conceived, named, typed, serialised, populated — and left inert. That
is why this was hard: the model already had the right shape, so the gap was invisible to
code review, and the symptom appeared in YAML where nobody looks for a missing concept.

And `profiles.py:443-451` shows the same lesson arriving a second time, in almost exactly
these words:

> *"the visual pass … was implemented correctly in the script and then never executed,
> because CI goes through the profile. It failed green on the regeneration dispatch,
> which uses the script, and red on every pull request, which does not."*

and, one line later, the fix chosen was to make the script *"require FINANCE_DB_PATH"* —
a **shell-script-level** guard. The framework was told an environment requirement existed
and the requirement was pushed **down into the script** instead of **up into the model**.

### 1.2 Why it worked for some workflows and fought us on others

Not luck. The two green workflows share three properties, and the two that fought us each
violate exactly one:

| | Runtime shards | Backend legs | Reconcile | Playwright visual |
|---|---|---|---|---|
| Obligations homogeneous? | yes — all `pytest <files>` | yes — one command each | **no** — mixed shell/measurement/playwright | **no** — filtered pass |
| Transport = one artifact, one path? | yes | yes | **no** — report + evidence + logs | **no** |
| Needs per-leg mutable state? | no | no | **yes** — Playwright task | **yes** — DB per leg |

Homogeneous obligations need identical envelopes, so a wrong envelope applies uniformly
and stays invisible. The moment obligations differ — or need per-leg state — each one
needs a *different* envelope, and there was nowhere to put it.

**The variable was never framework correctness. It was uniformity of the obligation set.**

---

## 2. Root cause, stated as one sentence

> The runtime owns **obligations, evidence, and certification**; it does not own the
> **execution envelope** — command context, required environment, time budget, evidence
> transport, liveness — so that envelope is hand-written once per workflow per leg, and
> the runtime cannot validate it, reproduce it, or test it.

| Execution condition | Owner today | Modelled? | The defect it caused |
|---|---|---|---|
| What must run | runtime plan | yes | never wrong |
| Command + cwd | runtime | yes | never wrong |
| Tool paths | runtime `verify_prerequisites` | paths only | — |
| **Required env vars** | **shell script / YAML** | **no** | `FINANCE_DB_PATH` unset ⇒ guaranteed task failure |
| **Time budget** | **YAML `timeout`** | **no** | `timeout 85` = 85 **seconds**; 4/7 shards killed |
| **Evidence transport** | **YAML path lists** | **no** | artifact LCA nesting ⇒ 0-byte results |
| **Liveness** | nowhere until this milestone | no | 4 shards died invisibly |
| Evidence → verdict | runtime | yes | never wrong |

Eight conditions. Six unowned. All six produced defects that looked like framework bugs.

---

## 3. Architectural fix

### 3.0 Governing rule

> **The runtime is the single authority for how an obligation executes. YAML states only
> *which* obligations and *how they are scheduled* — never *how one runs*.**

Not "simplify the framework". The complexity is justified where it models semantics; the
unjustified complexity is the **five hand-maintained copies of orchestration logic now
living in YAML** (env blocks, budget expressions, artifact path lists, matrix emission,
report parsing). We paid for that duplication. The fix deletes it by giving the framework
the one concept it is missing and making it authoritative.

### 3.1 Guard against building a second framework

Hard constraints, stated so this cannot sprawl:

- The envelope is **data**. It introduces no execution engine.
- The **only** place a verification subprocess is spawned remains
  `parallel_executor.run_streaming_command`. One worker, as the M10-R2-C3 promotion
  established.
- The envelope cannot weaken a threshold, skip an obligation, or alter a verdict. It may
  only *describe* and *validate* how an already-decided obligation runs.
- Every field is **readable and checkable by `validate_actions.py`**, so the constitution
  validator can assert that workflows contain no execution logic.

### 3.2 L1 — Environment: declared, resolved, enforced

Make `required_environment` authoritative and give it the axis it never had.

```
required_environment = (
    ".venv",                                  # tool  — already enforced today
    "pytest",                                 # tool
    "FINANCE_DB_PATH=@workspace/backend/data/e2e-$LEG.db",   # variable, self-resolving
    "PLAYWRIGHT_PROJECT=chromium",            # variable
)
```

- **Tool form** (bare name): presence on PATH / file exists — current behaviour.
- **Variable form** (`NAME=<value>` or `NAME` meaning "must be set"): presence and
  validity, checked **before any spawn**.
- `@`-prefixed placeholders resolve from the envelope's own provenance (`@workspace`,
  `@leg`, `@shard`, `@plan`). The same declaration therefore yields the correct value in a
  shard, in CI, and on a laptop — this is what makes local execution identical to CI
  rather than merely similar.

`verify_prerequisites` validates both axes and names what is missing.

**Delete the shell-script guard** at `run_playwright_tests.sh` (the `FINANCE_DB_PATH`
check) and **declare the requirement in `profiles.py`**. One authority, not two.

*Effect:* today's 400-second opaque `EXIT_NONZERO` becomes a named prerequisite failure at
second zero.

### 3.3 L2 — Budget: a typed quantity, one authority

`timeout_seconds: int` already exists on the task. The defect was that YAML *also*
expressed the budget, in free text, and got the unit wrong.

- The executor takes its budget **only** from the task.
- Workflows may not express a budget. `timeout-minutes:` stays as a coarse runner backstop,
  documented as such, and the executor asserts its own budget is strictly below it — so the
  two can never disagree about which fires first.

*Effect:* the `timeout 85` unit class of bug is structurally impossible; a bare number can
never reach a shell.

### 3.4 L3 — Transport: declared once, consumed by writer and reader

Add a declared `evidence_transport` to the emitted plan: artifact name pattern, path set,
and the **declared artifact root**.

The writer publishes at that root; the reader resolves against that root. Neither infers it
from whatever `upload-artifact` computed.

*Effect:* the artifact-LCA class is permanently closed. This is what `mutation.yml` gets
right by construction and what the three fan-out workflows each had to rediscover.

### 3.5 L4 — One executor, and local ≡ CI

`verify execute-envelope <file>` becomes the single entry point that spawns a verification
obligation. It reads the envelope, validates prerequisites, enforces the budget, runs
through the shared worker, and writes the leg result.

A fan-out workflow reduces to its irreducible content:

```yaml
jobs:
  <name>-plan:
    outputs: { matrix: ... }
    steps: [{ run: .venv/bin/python -m runtime.verify <profile>-plan }]

  <name>-leg:                       # matrix over the emitted envelopes
    needs: [<name>-plan]
    steps:
      - run: .venv/bin/python -m runtime.verify execute-envelope ${{ matrix.envelope }}

  <name>-gate:
    needs: [<name>-plan, <name>-leg]
    if: always()
    steps: [{ run: .venv/bin/python -m runtime.verify <profile>-aggregate ... }]
```

No env blocks. No budget expressions. No artifact path lists. No report parsing.

### 3.6 The local harness is not a debugging convenience — it is the acceptance test

Once L4 exists, `verify local-shards --workflow <name>` is *the same envelope* executed
against a local path. Reproducibility stops being a hope and becomes a test.

Its output is the artefact a reviewer actually wants:

```
SHARD  TASKS  STATUS       TIME   TERMINATION
0      2/11   PASS         42.1s   EXIT_ZERO
1      1/11   FAIL         31.7s   EXIT_NONZERO
5      1/11   TIMED_OUT   600.0s   WRAPPER_TIMEOUT

RESULT: NOT CERTIFIED
  shard 1 -> exec-0004 -> EXIT_NONZERO (term from the shared classifier)
```

**Local success still does not prove CI success** — runners differ in cores, browser
revisions, fonts, filesystem paths, and service availability. The division of labour is
deliberate: *local reproduction catches implementation bugs; one CI run validates
runner-specific assumptions.* The harness makes the first half exhaustive and cheap.

---

## 4. Sequence

Ordered so each stage is verifiable before the next, and so the two currently-blocked
failures get diagnosed **without another CI cycle**.

### Stage 0 — Diagnose the two open failures locally (no workflow change)

The review direction is right that CI must not be the debugger. Before touching any
workflow, reproduce both locally:

- **Reconcile shards 0–6**: `verify plan --shard-plan --out /tmp/p.json`, then
  `verify run --plan /tmp/p.json --shard i --count 7 --result-out …` for each `i`.
  Capture exit code, termination kind, task ids, duration, and generated evidence.
- **Playwright visual legs**: run the exact visual command against a freshly seeded
  per-leg DB with the leg's env, to separate *baseline drift* from *environment*.

Deliverable: a per-shard table. If a shard fails locally, it is an implementation bug and
is fixed locally. If it passes locally and failed in CI, the difference is a runner
assumption and is named as such.

### Stage 1 — L1 environment (highest value, lowest risk)

1. Extend `required_environment` with the variable form and `@`-placeholders.
2. Enforce both axes in `verify_prerequisites`; report before spawn.
3. Declare `playwright-e2e`'s `FINANCE_DB_PATH` + `PLAYWRIGHT_PROJECT` in `profiles.py`;
   delete the script's guard.
4. Tests: missing variable ⇒ named failure, no spawn; `@`-resolution identical across
   leg/workspace; the playwright task now declares what it needs.

**Gate:** any previously silent missing requirement now surfaces as a *named prerequisite*.
Expect this to make some paths red that were green — that is the signal working, and each
must be resolved or explicitly declared, never suppressed.

### Stage 2 — L2 budget

Single authority from the task; executor asserts it is under the job backstop; remove
budget expressions from workflows. Tests: a unit-less budget is unrepresentable; the
`85`-vs-`85m` class cannot recur.

### Stage 3 — L3 transport

Declared artifact root on the plan; writer and reader both consume it. Tests: the
`mutation.yml` shape is the only shape; a declared root round-trips.

### Stage 4 — L4 executor + envelopes + local harness

1. `verify <profile>-envelopes` emits one envelope per leg.
2. `verify execute-envelope` is the only spawn path.
3. `verify local-shards --workflow <name>`.
4. **Then** convert the four fan-out workflows. Required identities untouched; `needs`,
   `matrix` and one `run:` per job is the whole diff.

**Gate for the whole milestone:** for each workflow, `local-shards` reproduces CI's
per-shard outcomes exactly, or every divergence is named and explained as a runner
assumption.

### Stage 5 — Validator rules (the constitution follows, it does not precede)

New `validate_actions.py` rules, each with a rejection test:

- a fan-out workflow may not declare an `env:` block for a verification obligation;
- may not express a per-leg budget;
- may not list artifact paths for verification evidence;
- must invoke `execute-envelope` for every leg.

This is what stops the duplication from regrowing. It is the durable part of the fix.

---

## 5. What this deletes

The point of the exercise — YAML shrinks to `needs`, `matrix`, and one `run:`:

| Removed from workflows | Replaced by |
|---|---|
| `env:` blocks per leg | `required_environment` in `profiles.py` |
| `timeout "${X:-N}"` expressions | `timeout_seconds` on the task |
| artifact `path:` lists | declared `evidence_transport` |
| `--result-out` / report `jq` parsing | declared leg-result schema |
| matrix emission boilerplate | `<profile>-envelopes` |
| the shell's `FINANCE_DB_PATH` guard | `required_environment`, enforced |

---

## 6. Risk, stated without hedging

| Risk | Sev | Mitigation |
|---|---|---|
| L1 surfaces many previously hidden missing requirements; more is red | **High** | Expected and desirable. Stage 1 is gated on triaging every one — resolve or declare, never suppress. Red is the measurement working. |
| L4 touches every fan-out workflow | **High** | Sequenced last, behind L1–L3 and behind `local-shards` proving equivalence. `local-shards` is the acceptance test, so the blast radius is measured before it is pushed. |
| Envelope becomes a second framework | Med | §3.1 constraints: data only, one spawn path, no new engine, validator-enforced |
| `required_environment` gains a second meaning | Med | Tool form vs variable form are syntactically distinct; both validate to the same `Prerequisite` type; migration is explicit per task |
| Declaring L1–L4 is a large change to a system that currently produces correct verdicts | **High** | Accepted deliberately. The alternative is permanent hand-maintained duplication in YAML, which is what produced every defect in this milestone. **No compromise: the duplication is the defect.** |

---

## 7. Answers to the specific questions asked

**Why did it work for some workflows and become hard to diagnose?**
Because those workflows had homogeneous obligations, single-path transport, and no
per-leg state — so the hand-written envelope was identical everywhere and its errors were
either absent or uniform. The moment obligations differ or need per-leg state, each needs
a different envelope, and the framework had nowhere to put it.

**What is the use of the runtime framework?**
It is the certification authority, and it performed correctly throughout. It owns
obligations, evidence, fingerprints, mutation, measurement, reconciliation, and the
split-brain guards — and every verdict it produced this milestone was right, including
refusing to certify on incomplete evidence. That is not the problem and should not be
reduced.

**What is the core problem?**
It has a declared-but-inert `required_environment` field and no other representation of
execution conditions, so six execution facts are hand-written per workflow per leg, drift
silently, and cannot be validated, reproduced, or tested by anything.

**The architectural fix?**
Make the execution envelope a first-class, serialized, runtime-owned artifact. Declare
environment, budget, and transport in the model; enforce them before spawn; execute through
one entry point that is byte-identical locally and in CI; and delete the YAML duplication
— enforced by new validator rules so it cannot regrow.

**Why is a local shard harness part of the architectural fix rather than a convenience?**
Because it is the *same envelope* executed locally. It converts "reproduce in CI" from a
multi-minute, opaque, guess-driven loop into a deterministic function of one artifact —
and it is the acceptance test that proves the CI topology is faithful.

---

## 8. Immediate next step

Stage 0 only: build the harness, reproduce reconcile shards 0–6 and the two Playwright
visual legs locally, and produce the per-shard table. **Push no workflow change until that
table exists.** The two open failures are already narrowed to `exec-0004`
(`run_property_tests.sh`, 409 s in CI vs 30 s local) and 11 `toHaveScreenshot` mismatches
on a branch carrying 119 changed frontend files and a 970-line `tools/e2e_seed.py`
rewrite — both reproduced offline, neither needs a CI cycle to characterise further.

Implementation requires source edits across `runtime/foundation/verification/**` and
`.github/workflows/**`, plus mutating verification runs: switch to an implementation-capable
agent.