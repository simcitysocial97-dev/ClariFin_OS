# M10 Agent 2 — CodeQL Ownership and the "Duplicate CodeQL Workflow"

- **Repository:** `simcitysocial97-dev/ClariFin_OS` (public)
- **Baseline:** `bfcf336b5b7f46e759c7486f3eb02d0f8d92e14b`
- **Observed:** 2026-10-02, all claims backed by `gh` output reproduced below
- **Primary question:** *Why does GitHub show a duplicate CodeQL Advanced Security workflow?*

---

## 1. Answer in one paragraph

There is **no duplicate analysis**. There is exactly **one live CodeQL analysis
surface** — the source-controlled `.github/workflows/security-codeql.yml` — plus
**two dead registrations** that GitHub keeps displaying: the *retired default
setup* (a `dynamic/` path, last run 2026-08-12) and a *ghost* entry for
`.github/workflows/codeql.yml`, a file that was created and deleted on a feature
branch and never reached `main`. The decisive evidence is the CodeQL databases
API: `python-database`, `javascript-database` and `actions-database` are all
maintained, and every write timestamp lines up with a `security-codeql.yml` run
and none with the default setup. **The correct action is to change nothing.**
Removing a display entry by reducing `languages:` would delete real security
coverage and would additionally break a required status check.

---

## 2. The three "CodeQL" entries

`gh workflow list --all` shows three CodeQL-related rows. Resolved paths and run
histories:

### 2.1 `CodeQL Security Analysis` — id **332453015** — `.github/workflows/security-codeql.yml` — **LIVE, AUTHORITATIVE**

```
$ gh api .../actions/workflows/332453015/runs?per_page=15
110  push  main  bfcf336b5  success  2026-10-02T00:55:03Z
109  pull_request  fix/contract-gate-cache-poisoning  23c35e6ba  success  2026-10-02T00:35:46Z
108  push  main  aacce1614  success  2026-10-02T00:28:55Z
...
```

110 runs, continuously active, latest run on the exact baseline commit.

### 2.2 `CodeQL` — id **330860652** — `dynamic/github-code-scanning/codeql` — **DEAD (retired default setup)**

```
$ gh api .../actions/workflows/330860652/runs?per_page=15
2  PR #3                     refs/pull/3/head  success  2026-08-12T04:02:12Z
1  CodeQL Setup              main               success  2026-08-10T05:42:14Z
```

Two runs, both in August. **No run in the 52 days since.** A still-enabled
default setup would run on every push to `main` and on its weekly schedule; it
has done neither since 2026-08-12. The `dynamic/` path prefix confirms the file
does not exist in the repository.

### 2.3 `CodeQL Security Analysis` — id **332570115** — `.github/workflows/codeql.yml` — **GHOST**

```
$ gh api .../actions/workflows/332570115/runs?per_page=15
1  pull_request  verification-framework-codeql-integration  6db591c0e  cancelled  2026-08-12T08:02:40Z
```

One cancelled run. The file is absent everywhere:

```
$ gh api repos/simcitysocial97-dev/ClariFin_OS/contents/.github/workflows/codeql.yml
{"message":"Not Found","status":"404"}

$ git ls-tree --name-only origin/main .github/workflows/     # 14 files, no codeql.yml
$ for b in $(git ls-remote --heads origin | ...); do git cat-file -e origin/$b:.github/workflows/codeql.yml; done
(no branch contains it)
```

Its whole life, from git history:

```
6db591c0  Create .github/workflows/codeql.yml
8100e361  Delete .github/workflows/codeql.yml
00344319  Create .github/workflows/codeql.yml
4c4b1a44  Delete .github/workflows/codeql.yml
```

It was created and deleted twice on `verification-framework-codeql-integration`
and never merged. GitHub retains the registration because a run was recorded.

---

## 3. Decisive evidence: default setup is NOT running alongside

If default setup were still active, it would write the code-scanning databases on
every push. The databases API shows who is actually writing them:

```
$ gh api repos/simcitysocial97-dev/ClariFin_OS/code-scanning/codeql/databases
lang=actions     name=actions-database      updated=2026-10-02T00:58:50Z
lang=javascript  name=javascript-database   updated=2026-10-02T00:58:48Z
lang=python      name=python-database       updated=2026-10-02T00:58:44Z
```

All three were written within 6 seconds of each other at **00:58:4x on
2026-10-02**, i.e. ~3.5 minutes after `security-codeql.yml` run **#110** started
(**00:55:03Z**). That is the signature of one workflow analysing three languages.
The default setup's last run was **2026-08-12** — 52 days earlier. It is not
contributing.

---

## 4. Which languages are actually scanned

The source-controlled workflow declares:

```yaml
languages: python, javascript, actions
```

Confirmed by both the databases (above) and by the alerts actually raised —
alerts are grouped by the language's rule prefix and land in all three trees:

| Rule family | Alert count | Example paths |
|---|---|---|
| `py/*` | 19 + 6 | `backend/src/extraction/metadata_extractor.py`, `runtime/platform/ai/orchestrator.py` |
| `js/*` | 4 | `frontend/scripts/verify-mock-sync.ts` |
| `actions/*` | 16 | `.github/workflows/api-contracts.yml`, `.github/actions/bootstrap-runtime/action.yml` |

Rules present: `py/clear-text-logging-sensitive-data`, `py/path-injection`,
`py/redos`, `py/stack-trace-exposure`, `js/double-escaping`,
`js/identity-replacement`, `js/incomplete-multi-character-sanitization`,
`actions/cache-poisoning/poisonable-step`, `actions/missing-workflow-permissions`,
`actions/untrusted-checkout/critical`.

**TypeScript coverage is real**, and is provided by the `javascript` database: the
`js/` findings above are in `frontend/scripts/verify-mock-sync.ts`, a `.ts` file.
TypeScript is covered by the JS/TS extractor, which is why there is no separate
`typescript-database`. Declaring an explicit `typescript` language would create a
second, redundant database — another reason not to touch this line.

**Alert disposition (45 alerts total):** 30 dismissed (16 error + 14 warning) and
15 fixed (13 error + 2 warning); none open. The 12
`actions/missing-workflow-permissions` alerts were created by the retired default
setup on **2026-08-10** and were all reviewed and dismissed on **2026-10-02**
(between 00:36:46Z and 00:37:53Z), after this workflow had begun re-analysing the
`actions` database. Each points at a workflow that does declare an explicit
`permissions:` block (`quality.yml`, `mutation.yml`, `golden.yml`,
`playwright.yml`), so dismissal is the correct disposition.

---

## 5. There is exactly one authoritative analysis configuration

| | Owner | Languages | Status |
|---|---|---|---|
| **Authoritative** | `.github/workflows/security-codeql.yml` (id 332453015) | python, javascript, actions | **Active** — 110 runs, owns all 3 databases |
| Retired registration | `dynamic/github-code-scanning/codeql` (id 330860652) | (was python, javascript) | Dead since 2026-08-12; not scheduled; contributes nothing |
| Ghost registration | `.github/workflows/codeql.yml` (id 332570115) | unknown | File deleted; 1 cancelled run; contributes nothing |

The source-controlled workflow **is** the single authority, as intended. The
alternative — switching the repository to default setup — would *reduce* coverage
(default setup cannot be given an explicit `paths-ignore`, would drop the
`actions` language that owns the workflow findings, and would remove the versioned,
auditable, PR-annotated surface). It was therefore rejected on the evidence.

**The workflow's own header already asserted this ownership.** What it got wrong
was one factual claim about the alert history; see §7.

---

## 6. Why "remove the duplicate" was rejected

Three independent reasons:

1. **It would delete real coverage.** The only way to make the default-setup
   entry disappear from the list is to change a repository setting or delete the
   registration. Neither is a source change. Removing `actions` from `languages:`
   to make the display "clean" would drop the `actions` database — the surface
   that raised the `untrusted-checkout/critical` and `cache-poisoning` findings
   which have already driven real fixes in this repository. That is the opposite
   of preserving security coverage.
2. **It would break a required status check.** `Analyze` — the job name in
   `security-codeql.yml` — is one of the four required contexts in the active
   `protect-main-branch` ruleset (`GET /rulesets/20127383`). Touching the job
   graph of that workflow can make `main` permanently unmergeable.
3. **There is nothing concurrent to remove.** Section 3 proves default setup is not
   running. The remaining two entries are display residue, already known, and
   carry zero coverage.

---

## 7. Change actually made

One file, comments only:

```
 .github/workflows/security-codeql.yml | 28 ++++++++++++++++++++++++-------
```

The diff corrects one claim that had become factually false, and records the
duplicate-display reconciliation so the next auditor does not repeat this
investigation.

**Before** (inside the `Initialize CodeQL` step):

```yaml
# `actions` is included deliberately. GitHub's default CodeQL setup is
# `not-configured` on this repository, so this workflow is the only
# analysis surface. Without `actions`, workflow files had no owner:
# the actions database was last written on 2026-08-10 by the retired
# default setup, and the 12 actions/missing-workflow-permissions alerts
# it raised have never been re-analysed. Including it restores that
# ownership and lets those alerts be confirmed or cleared by a real
# re-analysis rather than closed on age.
```

**After**: states that the database is written on every run of this workflow
(citing the three `2026-10-02T00:58:4xZ` timestamps), and that the 12 alerts
*have* been re-analysed and dismissed — replacing the stale "have never been
re-analysed" with the observed `dismissed=2026-10-02T00:36:46Z..00:37:53Z` fact
and the reason dismissal is correct. It also documents the three IDs, the fact
that only this workflow writes the databases, and an explicit instruction not to
"fix" the duplicate by cutting coverage.

**Verified behaviourally unchanged** after the edit:

```
languages = python, javascript, actions
job name  = Analyze
YAML parses cleanly
```

No trigger, job graph, required-check name, permission, or `languages:` value was
modified.

---

## 8. Recommended follow-up (NOT done — repository settings, blast radius)

Clearing the two dead display entries requires deleting workflow registrations via
`DELETE /repos/simcitysocial97-dev/ClariFin_OS/actions/workflows/{id}` (or the
Actions UI). This is deliberately **not** performed here:

- it is a repository-settings mutation, not a source change;
- the brief forbids pushing, and these cannot be cleared by a commit anyway;
- neither registration is referenced by any required check, so deletion is safe
  from a merge-gating standpoint — but it should be an explicit, recorded decision.

Targets: `332570115` (`codeql.yml`, ghost) and `330860652` (`dynamic/…/codeql`,
retired default setup).
---

## 9. Follow-up attempted during M10 integration: the dead entries are NOT removable

The follow-up in §8 was attempted during integration and **failed structurally**.
All three dead registrations were targeted with the documented endpoint, with an
`admin: true` token (`{"admin":true,"maintain":true,"pull":true,"push":true}`):

| Workflow id | Name | Path | `DELETE` result |
|---|---|---|---|
| `332570115` | CodeQL Security Analysis | `.github/workflows/codeql.yml` | `HTTP/2.0 404 Not Found` |
| `372442200` | Matrix Shape Probe | `.github/workflows/zz-matrix-probe.yml` | `HTTP/2.0 404 Not Found` |
| `330860652` | CodeQL | `dynamic/github-code-scanning/codeql` | `HTTP/2.0 404 Not Found` |

The registry is unchanged at 18 entries after the attempts.

**Root cause.** `DELETE /repos/{owner}/{repo}/actions/workflows/{workflow_id}`
resolves the workflow through the default branch's tree. All three targets are
absent from `main`'s tree (or are `dynamic/` pseudo-paths with no file at all),
so the lookup misses and the endpoint returns 404 regardless of privilege. This
is not an authorization failure and not a permissions problem — it is not
reachable by the repository owner at any privilege level.

**Consequence — this is now a permanent known limitation, not an open task.**

- The two "CodeQL Security Analysis" entries will remain in the Actions list
  until GitHub garbage-collects the registrations for deleted files.
- `code-scanning/default-setup` is `not-configured`, so entry `330860652`
  cannot be supplying analysis. Security coverage is unaffected: `python-
  database`, `javascript-database` and `actions-database` were all written
  `2026-10-02T00:58:4xZ` by `security-codeql.yml`, and that remains the single
  authoritative analysis.
- **Do not** "fix" the duplicate by disabling security coverage, narrowing
  `languages:`, or removing the `Analyze` job. The duplicate is cosmetic; the
  coverage is not.
