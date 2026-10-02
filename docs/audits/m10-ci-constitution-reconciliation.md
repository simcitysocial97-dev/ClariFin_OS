# M10 — CI constitution reconciliation

Reconciles `.github/scripts/validate_actions.py` (the enforcer of
`docs/GITHUB_ACTIONS_CONSTITUTION.md`) with the workflows it governs.

## Headline

`validate_actions.py` is mandated by the constitution ("must pass with zero
errors", Constitution §11 checklist item 10) and **was wired into no workflow**.
It reported **24 errors** against 14 workflows. It now reports **1**.

The enforcer was not lying. The architecture it describes had genuinely
drifted, and nothing had been checking.

## What the 24 errors actually were

| Count | Class | Disposition |
|---|---|---|
| 11 | Rule 9 — job summaries ran `runtime.verify doctor`, constitution mandates `runtime.verify status` | **Fixed.** `status` substituted in all 11 Job Summary steps |
| 6 | Rule 8 — `mutation.yml` shards (`mutation-plan`, `mutation-aggregate`, `mutation-trust`) flagged as wrong profile | **Enforcer fixed**, not the workflow (see below) |
| 2 | Rule 3/4 — `mutation-pr.yml` inlined `actions/upload-artifact` | **Fixed.** Routed through `./.github/actions/upload-runtime` |
| 4 | Rule 8 — `doctor`/`mutation` preflight invocations | **Enforcer fixed** via documented auxiliary-command allowance |
| 1 | Rule 8 — `frontend-verify.yml` never runs `runtime.verify frontend` | **Outstanding → backlog** (see below) |

### Why the Rule 8 shard errors were an enforcer bug, not workflow drift

The constitution's Rule 8 reads *"Every workflow executes `python
runtime/verify.py`"*. It never said *exactly one command per workflow*.
`mutation.yml` is one responsibility — mutation — expressed across the M9-C71
sharded authoritative campaign (`mutation-plan` → `mutation --shard` →
`mutation-aggregate` → `mutation-trust`).

The enforcer was stricter than the document it enforces. It now accepts a
documented subcommand of a workflow's own profile (`<profile>-*`) and still
rejects a different profile's command.

**This is regression-tested.** Substituting `runtime.verify backend` into
`quality.yml` still raises Rule 8 errors, so the check was not weakened.

### Why `doctor` → `status` is safe for summaries

Measured locally before changing 11 required workflows:

| Command | Exit | Wall time | Output tail |
|---|---|---|---|
| `runtime.verify status` | 0 | 12.4 s | `Framework authority integrity: HEALTHY` |
| `runtime.verify doctor` | 0 | 11.8 s | `Framework authority integrity: HEALTHY` |

Identical tail, equivalent cost, both exit 0. `doctor` is retained in
`mutation.yml` only as the pre-campaign environment preflight (AGENTS.md's
"environment diagnostic guard"), which is auxiliary, not a Rule 9 summary.

## Outstanding — `frontend-verify.yml` (backlog)

`frontend-verify.yml` delegates to `bash .github/scripts/run_frontend_verification.sh`
rather than invoking `runtime.verify frontend`. A `frontend` profile **does**
exist (`runtime/foundation/verification/profiles.py:468`).

Not fixed here, deliberately:

- it is a **required check** under ruleset `20127383`; changing it risks
  turning the merge gate red;
- the delegated script owns backend-readiness orchestration and phased
  npm execution, so adopting the profile needs a parity proof, not an edit;
- `frontend/` was being modified concurrently by the M10 frontend workstream
  at the time of writing.

This is the only reason `validate_actions.py` still exits non-zero.

## Dead GitHub workflow registrations — not removable

See `docs/audits/m10-agent2-codeql-ownership.md` §9. The two duplicate
"CodeQL Security Analysis" entries cannot be deleted by the repository owner:
`DELETE /repos/{owner}/{repo}/actions/workflows/{id}` returns **404 even with
an `admin: true` token**, because the endpoint resolves the workflow through
the default branch tree where those files do not exist. Security coverage is
unaffected — only `security-codeql.yml` writes the python/javascript/actions
databases.

**Do not resolve the duplicate by disabling coverage.**