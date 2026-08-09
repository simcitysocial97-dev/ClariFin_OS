# Program I — Backend `src` Hygiene & Gitignore Correctness

**Status: GATE PASSED**
**Date:** 2026-08-08
**Scope:** `.gitignore` correctness + `backend/src/data/` tracking state. No source code modified.

---

## I.1 — Finding Re-Verified

Program H's Finding A reproduced exactly.

```
$ git check-ignore -v backend/src/data/__init__.py
backend/.gitignore:13:data/    backend/src/data/__init__.py

$ git ls-files backend/src/data/
backend/src/data/finance.db          # tracked
                                     # __init__.py NOT tracked
```

**Root cause:** the unanchored pattern `data/` matches a directory named `data` at **any depth**, so it captured `backend/src/data/` — a source directory — in addition to the intended runtime data directory.

**Second instance discovered:** the same unanchored bug exists in the **root** `.gitignore:68`. Both had to be addressed, because gitignore rules compose — fixing only `backend/.gitignore` left the root rule still masking the file (verified: after the first fix, `check-ignore` reported `.gitignore:68:data/`).

**Inconsistent state confirmed:** `finance.db` was tracked (force-added historically, so ignore rules no longer applied to it), while `__init__.py` was ignored — the same directory in two different tracking states.

### Evidence gathered before changing anything

| Question | Evidence | Answer |
|---|---|---|
| Does any code import `src.data`? | grep across `backend/src`, `backend/tests`, `runtime`, `.github` | **No — zero imports** |
| Is `src/data/finance.db` the runtime DB? | `core/db/config.py` resolves CWD-relative `data/finance.db`; backend CI runs `cd backend` | **No** — runtime DB is `backend/data/finance.db` (315 KB, untracked) |
| Does `src/data/finance.db` contain anything? | `stat` = 0 bytes; `sqlite_master` query = **0 tables** | **No** — empty, no schema |
| Is `src/data/__init__.py` architecturally recognised? | Present in `runtime/generated/architecture-inventory.json` | **Yes** — recorded as a package |
| Is `src/data/finance.db` referenced anywhere? | grep across py/sh/yml/json (excl. generated) | **Zero references** |

---

## I.2 — Minimal Correction Applied

### `backend/.gitignore` (anchored)

```diff
 Database
 *.db
 .sqlite
-data/
-uploads/
+# Anchored to backend/data (the runtime DB dir resolved by core/db/config.py).
+# Unanchored "data/" also matched backend/src/data/, masking tracked source.
+/data/
+/uploads/
 test_.db
```

Anchoring with a leading `/` scopes the rule to `backend/data/` and `backend/uploads/` — the directories it was written for — while no longer matching `backend/src/data/`.

### Root `.gitignore` (targeted negation)

```diff
 data/
 uploads/
+# "data/" above is unanchored and matched backend/src/data/, masking backend
+# source from clean checkouts. backend/src is source, never local data.
+!backend/src/data/
```

Here I used a **negation instead of anchoring**, deliberately. The root `data/` rule legitimately ignores local data at multiple depths (`backend/data/` 12 files, `backend/tests/data/` 154 files, all untracked). Anchoring it would have un-ignored ~166 local files. The negation removes only the backend-source collision.

**No global `.gitignore` redesign was performed**, per the mission constraint.

### Deliberately NOT changed (observation)

`backend/.gitignore` lines 1, 10, 17 (`Python`, `Database`, `Environment`) lack `#` prefixes and are therefore **active patterns, not comments**. Verified they currently match nothing. Out of scope for Program I — recorded as a follow-up candidate.

### Ignore-intent regression check

| Path | After fix |
|---|---|
| `backend/data/finance.db` | ignored ✅ |
| `backend/tests/data/x.pdf` | ignored ✅ |
| `data/local.json` | ignored ✅ |
| `backend/uploads/y.pdf` | ignored ✅ |
| `backend/src/data/__init__.py` | **NOT ignored** ✅ (fixed) |
| `backend/src/data/finance.db` | ignored by `*.db` ✅ |

---

## I.3 — `finance.db` Disposition: UNTRACKED (file retained on disk)

**Classification: accidentally tracked database state.**

Evidence supporting untracking:
1. **0 bytes, 0 tables** — carries no data or schema
2. **Zero references** anywhere in the repository
3. **Not the runtime DB** — runtime resolves to `backend/data/finance.db` (315 KB)
4. Tracked only because it was force-added historically, contradicting `*.db` rules in both `.gitignore` files
5. **Actively harmful:** `startup.py` and `health.py` branch on `settings.database_path.exists()`; a 0-byte file returns `True`, masking a genuinely missing database

Action taken:
```bash
git rm --cached backend/src/data/finance.db   # untrack only
```

**The file remains on disk** (verified). It was **not deleted** — honouring the guardrail "Do NOT delete `backend/src/data/`". It is now correctly ignored by `*.db`.

### Package marker consistency

`backend/src/data/__init__.py` was **added to tracking** (`git add`). It is recognised as a package in the architecture inventory, and the guardrails forbid removing `backend/src/data/`. Tracking the marker makes the directory's state internally consistent: the package marker is versioned, the local database artifact is not.

> **Note on `git status` display:** the change shows as `R backend/src/data/finance.db -> backend/src/data/__init__.py`. This is git's content-similarity heuristic pairing two 0-byte files; it is **not** a rename. The net effect is one file untracked and one file tracked.

---

## I.4 — Clean-Checkout Validation (the decisive test)

Reproduced a clean checkout via `git archive` from the tree, before and after the fix:

| | Source `.py` files | `src/data/__init__.py` present | `src/data/finance.db` present |
|---|---|---|---|
| **HEAD (before)** | **243** | **NO** ❌ | YES (0-byte) |
| **Staged (after)** | **244** | **YES** ✅ | **NO** ✅ |

This is the direct proof: a clean CI checkout at HEAD was **missing a backend source file**. After the fix, the checkout contains the complete source tree and no stray database artifact.

**Clean-checkout import test** (run inside the extracted tree, not the dev tree):
```
CLEAN-CHECKOUT IMPORT: OK=243 FAILURES=0
```

---

## Gate Results

| Gate criterion | Result |
|---|---|
| `.gitignore` no longer masks backend source | **PASS** |
| Tracked/ignored state intentional | **PASS** |
| No production behavior changed | **PASS** — zero `.py` files modified |
| No unrelated files changed | **PASS** — only 2 `.gitignore` files + tracking state |
| Backend source imports intact | **PASS** — 243/243, 0 failures |
| FastAPI composition intact | **PASS** — 119 routes (baseline match) |
| `git status` shows only intended changes | **PASS** |
| Repo reproduces expected source tree | **PASS** — 244/244 files in clean checkout |
| `git diff --check` | **PASS** — clean |

### Files changed
- `.gitignore` (3 insertions)
- `backend/.gitignore` (4 insertions, 2 deletions)
- `backend/src/data/finance.db` — untracked (file retained on disk)
- `backend/src/data/__init__.py` — now tracked

### Files deleted: **NONE**
### Production source modified: **NONE**
### Verification rules modified: **NONE**

---

## Follow-up candidates (NOT actioned)

1. `backend/.gitignore` lines 1/10/17 are unintentional active patterns rather than comments (currently match nothing).
2. Root `.gitignore` `data/` still masks new files under `data/`, `backend/data/`, `backend/tests/data/`. The 14 tracked golden statement fixtures in `data/test/` survive only because tracked files bypass ignore rules — new golden fixtures added there would be silently ignored.
