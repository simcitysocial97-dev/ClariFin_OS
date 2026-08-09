# Backend `src/` CI & Reproducibility Risks — Program H

**REPORT ONLY — nothing fixed in this program.**

Context: a recent incident showed `.gitignore` rules causing required `backend/src` modules to be absent in GitHub Actions. This report re-examines that risk class systematically.

---

## RISK 1 — `backend/src/data/__init__.py` is git-ignored (clean-checkout divergence)

**Severity: HIGH (latent)** · Class **G/H**

```
$ git check-ignore -v backend/src/data/__init__.py
backend/.gitignore:13:data/    backend/src/data/__init__.py

$ git ls-files backend/src/data
backend/src/data/finance.db          # ← tracked
                                     # ← __init__.py NOT tracked
```

The rule `data/` in `backend/.gitignore:13` is **unanchored**, so it matches `data/` at **any depth**, including `backend/src/data/`. This is exactly the failure mode from the prior incident.

**Split-state anomaly:** the directory contains one **tracked** file (`finance.db`, force-added at some point) and one **ignored** file (`__init__.py`). A clean checkout therefore produces `backend/src/data/` containing `finance.db` but **no** `__init__.py`.

**Current blast radius: NONE.** Verified:
- No module imports `src.data` (grep across `src/` and `tests/` returns zero hits)
- `__init__.py` is 0 bytes
- The runtime DB path is CWD-relative `data/finance.db` (from `core/db/config.py`), **not** `backend/src/data/`

**Why it still matters:** the directory is a Python package on the developer machine but not in CI. Any future module added under `backend/src/data/` would be **silently absent** in GitHub Actions — a repeat of the prior incident with a delayed fuse.

**Reported action (not applied):** anchor the rule (`/data/`) or add a negation for `backend/src/**`, and decide whether `backend/src/data/` should exist at all.

---

## RISK 2 — Tracked local database artifact

**Severity: MEDIUM** · Class **G**

```
backend/src/data/finance.db   tracked in git, 0 bytes
```

A `.db` file is tracked despite `*.db` ignore rules in **both** `.gitignore:65` and `backend/.gitignore:11` (it was force-added, so ignore rules no longer apply).

**Risks:**
- A 0-byte file at a plausible DB path can mask "database missing" errors — code that checks `path.exists()` gets `True` for an empty, schema-less file. `startup.py` and `health.py` both branch on `settings.database_path.exists()`.
- Future non-empty commits of this file would leak local financial data into git history.

**Mitigating fact:** the runtime path resolves relative to CWD (`data/finance.db`), so with `cwd=backend/` the runtime uses `backend/data/finance.db`, **not** this file.

---

## RISK 3 — Root `.gitignore` rule `/src/`

**Severity: LOW (currently inert, high-consequence if it drifts)**

`.gitignore:89` contains `/src/` under the comment "Root-level stale directories". The **leading slash correctly anchors it to the repository root**, so `backend/src/` is unaffected.

**Verified safe:** all 243 `backend/src` Python files are tracked; `git check-ignore` on sampled `backend/src` paths returns not-ignored (except RISK 1).

**Why reported:** an ignore pattern named `/src/` in a repo whose primary backend package **is** `src` is a standing hazard. If the leading `/` were ever dropped, the entire backend source tree would vanish from CI. Documented as a fragile-by-name rule.

---

## RISK 4 — Tool cache written inside the source tree

**Severity: LOW** · Class **G**

`backend/src/.mypy_cache/` (20K) sits **inside** the source package rather than at `backend/`. Also 25 × `__pycache__/` and 249 × `.pyc` files.

All are correctly ignored (`backend/.gitignore:2,3,7`) — no tracking risk. Risks are:
- Stale `.pyc` can mask a deleted/renamed module locally, producing "works on my machine, fails in CI" behaviour. Relevant here because Program H found several **phantom module paths** in the provider registry.
- Tooling that walks `backend/src/**` must exclude these paths.

**Note:** `.mypy_cache/3.12` is empty — the cache is Python-version-keyed (see RISK 6).

---

## RISK 5 — Case-sensitivity: `behaviour` vs `behavior`

**Severity: LOW–MEDIUM (spelling, not case)**

The codebase deliberately uses British `behaviour` for the canonical package: `engines/behaviour_engine/`, `services/behaviour_service.py`, `routers/behaviour.py`, `core/dtos/behaviour_dto.py`.

American `behavior` survives only in:

| Site | Nature |
|---|---|
| `src/config.py:112` | `enable_behavior_engine` feature-flag property (env `ENABLE_BEHAVIOR_ENGINE`) |
| `tests/architecture/test_layer_boundaries.py:43` | whitelist entry for the non-existent `engines/behavior_engine.py` |
| `tests/unit/engines/behavior/test_behavior_engine.py` | directory + filename (imports the correct `behaviour_engine.core`) |

**No two files differ only by case**, so case-insensitive filesystems (macOS/Windows) are **not** at risk of collision. The hazard is developer/tooling confusion and path-matching rules that assume one spelling. `config.enable_behavior_engine` is a public env-var contract — renaming it is a breaking change, not a cleanup.

---

## RISK 6 — Python-version-specific behaviour

**Severity: LOW**

- `backend/src/.mypy_cache/3.12` pins the local toolchain to **Python 3.12**.
- Source uses PEP 604 unions (`str | None`) and PEP 585 generics (`dict[str, Any]`) extensively — requires **Python ≥ 3.10**.
- `from __future__ import annotations` is used inconsistently (present in `common/database.py`, absent elsewhere), so version tolerance is not uniform.

CI must pin ≥3.10 (3.12 recommended to match local). No 3.13-specific incompatibility observed.

---

## RISK 7 — Runtime-path dependence (CWD sensitivity)

**Severity: MEDIUM**

`core/db/config.get_db_path()` falls back to the **relative** path `data/finance.db`:

```python
DEFAULT_DB_RELATIVE_PATH = f"data/{DEFAULT_DB_FILENAME}"   # relative to CWD at runtime
```

Resolution order: explicit arg → `settings._database_path_override` → `FINANCE_DB_PATH` → `DATABASE_PATH` → `data/finance.db`.

The final fallback is **CWD-dependent**: the effective DB location changes with the working directory of the process. `.github/scripts/run_backend_verification.sh` does `cd "$REPO_ROOT/backend"`, so CI resolves `backend/data/finance.db`.

The override chain is well-designed and tests use explicit paths, so this is a **documented behaviour**, not a bug. Reported because any CI step that changes CWD silently changes the DB target. Setting `FINANCE_DB_PATH` explicitly in CI would remove the ambiguity.

---

## RISK 8 — Generated-metadata drift (provider registry)

**Severity: MEDIUM**

`runtime/generated/architecture-provider.json` references **4 paths that do not exist** and **omits one that does** (see baseline §6).

Any CI gate, report, or tool that trusts the provider as ground truth will operate on phantom modules. `backend/src/engines/cashflow_engine.py` (mtime 2026-08-07) postdates the provider snapshot (2026-08-06), confirming drift rather than corruption.

**Not a `backend/src` source defect** — a generated-artifact freshness issue. Reported here because it affects CI reproducibility.

---

## RISK 9 — Missing tracked source check

**Severity: NONE (verified clean, aside from RISK 1)**

| Check | Result |
|---|---|
| Python files on disk (excl. cache) | 244 |
| Python files tracked by git | **243** |
| Delta | **1** — `backend/src/data/__init__.py` (RISK 1) |
| All 243 modules import successfully | **PASS** (0 failures) |
| `src.api:app` composes | **PASS** (119 routes) |

No other local-only module exists. Apart from the ignored empty `data/__init__.py`, **a clean checkout contains the complete backend source tree.**

---

## Risk Summary

| # | Risk | Severity | Class | Blast radius today |
|---|---|---|---|---|
| 1 | `src/data/__init__.py` git-ignored | HIGH (latent) | G/H | None — nothing imports it |
| 2 | Tracked 0-byte `finance.db` | MEDIUM | G | Masks existence checks |
| 3 | Root `/src/` ignore rule | LOW | — | Inert (correctly anchored) |
| 4 | Caches inside source tree | LOW | G | Stale-module masking |
| 5 | `behaviour`/`behavior` spelling | LOW–MED | — | No case collision |
| 6 | Python-version pinning | LOW | — | Requires ≥3.10 |
| 7 | CWD-relative DB fallback | MEDIUM | — | CI CWD-dependent |
| 8 | Provider registry drift | MEDIUM | — | Phantom modules in tooling |
| 9 | Missing tracked source | NONE | — | Verified clean (1 known delta) |

**No `.gitignore` rule, source file, or CI configuration was modified by Program H.**
