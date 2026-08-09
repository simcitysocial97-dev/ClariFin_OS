# Forensic Recovery Plan — ClariFin_OS (NON-EXECUTING)

**Status:** READ-ONLY audit complete. Control specimen preserved: `0c8410c3` in `~/AI-Projects/ClariFin_OS`.

## Source of truth
- **`c37acaa9f1a8f0c1a6adb602aacbd44abf3fe454`** — last full pre-deletion snapshot (2107 files, Aug 9 01:12:36 UTC).
- Available in TWO independent stores (redundant):
  1. `~/AI-Projects/recovery/kilo-snapshot-repo` (bare recovery repo)
  2. `~/.local/share/kilo/snapshot/9980d0d6.../fbef357c11eb...` (local active Kilo store)
- Verify: `git -C <store> ls-tree -r --name-only c37acaa9 | wc -l` → 2107 in both.

## What was lost (only in snapshots, uncommitted)
The entire post-`0c8410c3` working-tree state: 77 files added, 49 modified, 34 removed vs baseline. This includes:
- Program H audit deliverables (`docs/audits/backend-src/BACKEND_SRC_*.md`, 5 files)
- Program I gitignore hygiene (`.gitignore`, `backend/.gitignore`, `backend/src/data/__init__.py`)
- Program J generator fixes (SINGLE_FILE_ENGINES constants, ENGINE_FACADES empty, Parked fixed, `src.core.db` canonical imports)
- Program K fixture migration (TestDatabase, `src.extraction`, Hypothesis fixtures)
- Program L audit (`docs/audits/backend-src/program-l-root-module-ownership.md/.json`)
- Program M audit (`docs/audits/backend-src/program-m-*.md/.json`)
- Frontend improvements (11 files: cards, error-boundary, eslint.config, hooks, parser, etc.)
- `_probe_emi_up.py`, runtime evidence (`runtime/generated/*`), loan_engine fixes
- **Intentional db.py deletion:** `backend/src/db.py`, `backend/src/common/database.py` REMOVED (user's DB cleanup, post-L)

## What remains in git (0c8410c3)
- 2064 tracked files, clean working tree. OLD baseline. Has `db.py` (to be deleted per user intent), `finance.db` (0-byte, to be removed). NO H-L/M audits.
- Dangling tree `57f548…` in the repo: OLD convergence-era (retired workflows, old migrations). NOT H-L work. Leave it.
- Dangling trees `d1d22e` (tests), `232706` (backend of a clarit-like state) — pre-0c8410c3, low value. Leave them.

## Restoration procedure (for an executing agent)
1. Preserve `0c8410c3` as committed baseline (do not reset/amend).
2. Materialize `c37acaa9`'s tree as the working tree:
   - Extract each blob from `git -C ~/AI-Projects/recovery/kilo-snapshot-repo archive c37acaa9…` into the working repo.
   - Working-tree diff vs `0c8410c3` = exactly +77 / ~49 / -34 (the user's H-L/M work).
3. **34 files to NOT restore** (present in 0c8410c3 but absent in c37acaa9 — user deleted them):
   - `backend/src/db.py`, `backend/src/common/database.py`, `backend/src/data/finance.db` → **keep deleted** (intentional DB cleanup).
   - `data/test/expected/*.json`, `data/test/statements/*.pdf` → root `data/` is gitignored by Program I; regenerable.
   - `backend/tests/generated/*` → gitignored generated artifacts; regenerable by pipeline.
4. Commit on top of `0c8410c3` (new commit, not amend). Branch: `feature/program-12-platform-certification` (or new recovery branch).
5. Validate:
   - `python runtime/verify.py quick` (engineering-runtime budget)
   - `docs/audits/backend-src/` contains 15 audit deliverables.
   - `runtime/generated/architecture-provider.json` shows `"engines": 12`.
   - `backend/tests/fixtures/database.py` has `TestDatabase`.
   - `test_upload_pipeline.py` imports `src.extraction.column_mapper`.
   - `backend/src/data/__init__.py` exists; `backend/src/data/finance.db` is gone.

## Unrecoverable
- **Conversation transcripts** of the H–L/M work: `kilo.db` `session_message` is empty (0 rows). Only ~640-byte session `.md` metadata summaries exist in `~/.local/share/kilo/memory/ClariFin_OS-*/sessions/`. File-level changes recovered; prose rationale lost.
- **Work between `c37acaa9` (01:12:36) and deletion (~01:13–01:14)**: next snapshot (`32084c77`) is already the 1-file survivor. Essentially nothing survived.
- **Runtime DB** `backend/data/finance.db`: gitignored, never in snapshots. Regenerate via app startup.
- **stray `~/AI-Projects/clarit`**: unrelated Flutter/Dart project, NOT a ClariFin duplicate.

## Decision points
1. `db.py`/`common/database.py`: snapshot has them **deleted** (user's intent); Program L audit says "retained." Reconcile before committing — user preference is to delete.
2. Branch: commit on existing `feature/program-12-platform-certification`, or create new `recovery/H-back-to-L`?
