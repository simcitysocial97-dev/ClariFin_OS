# VEA-3 M9 — BL-004 CI Workflow Topology Audit

**Status:** AUDITED — topology unchanged, no workflow files modified
**Milestone:** V3-M9
**Authority:** `docs/verification/VEA_BACKLOG.md#bl-004`

---

## 1. Method

Re-read every file under `.github/workflows/` and compared against the BL-004 M0
baseline (9 workflows, 7-profile map, trigger-overlap observations). No file was
modified. The audit deliberately stops at *observation + recommendation* because
BL-004's own hard constraints forbid modification until execution equivalence is
proven:

> 1. Consolidate only after execution equivalence is proven — with evidence
> 2. Do not remove a workflow merely because it appears redundant
> 3. Check branch-protection required status checks before proposing removal
> 4. Preserve separation of heavy workloads (`golden`, `mutation`) from ordinary verification

Equivalence proof is **not** part of VEA-3 (it needs the `unit_id`-keyed
`run-manifest.json` compared across workflows — a distinct, larger effort). Therefore
this milestone records the audit and defers consolidation.

---

## 2. Topology — UNCHANGED (re-asserted)

```
backend-verify.yml        frontend-verify.yml       golden.yml
mutation.yml              playwright.yml            quality.yml
verification-runtime.yml  dependency-update.yml     release.yml
```
→ 9 workflows, identical to the BL-004 M0 baseline. ✅

---

## 3. Workflow → `verify.py <profile>` map (verified)

| Workflow | Command | Profile | Job summary |
|----------|---------|---------|-------------|
| `backend-verify.yml` | `python runtime/verify.py backend` | backend | `verify.py status >> $GITHUB_STEP_SUMMARY` |
| `frontend-verify.yml` | `python runtime/verify.py frontend` | frontend | yes |
| `golden.yml` | `python runtime/verify.py golden` | golden | yes |
| `mutation.yml` | `python runtime/verify.py mutation` | mutation | yes |
| `playwright.yml` | `python runtime/verify.py playwright` | playwright | yes |
| `quality.yml` | `python runtime/verify.py quick` | quick | yes |
| `verification-runtime.yml` | `python runtime/verify.py runtime` | runtime | yes |
| `dependency-update.yml` | (no profile) | — | `verify.py status >> summary` only |
| `release.yml` | (no profile) | — | delegation note |

All 7 profile-invoking workflows execute **exclusively** through the unified
`verify.py` runtime (project decision `workflow_execution_model`) and emit the
standard `verify.py status` job summary (decision `job_summaries`). Local/CI parity
holds: every profile command has the identical local equivalent
`python runtime/verify.py <profile>` (decision `local_ci_parity`). ✅

---

## 4. Trigger-overlap catalogue (re-verified, unchanged from baseline)

| Path pattern | Workflows triggered |
|--------------|---------------------|
| `runtime/**` | `backend-verify`, `frontend-verify`, `playwright`, `verification-runtime` |
| `backend/src/routers/**` | `backend-verify`, `frontend-verify`, `verification-runtime` |
| `backend/src/engines/**` | `backend-verify`, `verification-runtime` |
| `frontend/**` | `frontend-verify`, `playwright` |
| *(any path)* | `quality.yml` — **no `paths:` filter** |

Additional facts:
- `quality.yml` triggers on `push: branches: ["**"]` with **no path filter** — the
  single largest source of redundant execution (runs `verify.py quick` on every
  branch/push regardless of changed files).
- `playwright.yml` is branch-restricted (`main`, `master`, `develop`); the other
  profile workflows run on `"**"`.
- `golden.yml` / `mutation.yml` are `cron`-schedule + `workflow_dispatch` only — by
  design, not redundancy.

---

## 5. Consolidation candidates (recommendation only — NOT executed)

1. **`quality.yml` redundant-trigger reduction.** The `quick` profile is a strict
   subset of the fast checks already run inside `backend-verify`/`frontend-verify`/
   `verification-runtime`. Adding a `paths:` filter to `quality.yml` (e.g.
   `backend/**`, `frontend/**`, `runtime/**`) would eliminate ~all redundant
   `quick` runs. **This is the safest single change**, but it still changes trigger
   behaviour and must be proven equivalent (and checked against required status
   checks) before applying — deferred per constraint #1/#3.
2. **`backend-verify` vs `verification-runtime` overlap on `runtime/**` and
   `backend/src/**`.** These run different profiles (`backend` vs `runtime`); they
   are *not* duplicate execution of the same work, so collapsing them would lose
   coverage. Left as-is.
3. **`frontend-verify` vs `playwright`** — different profiles (fast frontend
   verification vs browser e2e); intentional separation. Left as-is.

---

## 6. Decision

- **No `.github/workflows/` file was modified.**
- Topology re-asserted at 9 workflows, byte-for-byte in structure with the baseline.
- All verification workflows comply with the `workflow_execution_model` and
  `job_summaries` project decisions; local/CI parity holds.
- Consolidation is **deferred** to a dedicated phase that first proves
  `unit_id`-keyed execution equivalence across workflows (BL-004 prerequisite).

This satisfies BL-004's VEA-3 objective: the audit is complete and the topology
control (unchanged CI execution) that VEA-2/VEA-3 rely on remains intact.
