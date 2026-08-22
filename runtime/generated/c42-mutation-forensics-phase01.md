# C42 Phase 0 & 1 — Mutation CI Forensic Report

**Generated:** 2026-08-22T21:56:00+05:30  
**Phase:** Phase 0 (Establish Authoritative Baseline) + Phase 1 (CI Mutation Forensics)

---

## 0.1 Repository Identity

| Field | Value |
|-------|-------|
| **HEAD SHA** | `670bd4c8fcd2945374d8e4a09e791601863007e3` |
| **Tree SHA** | `9f7bccb75a60aa430064c4ceba0f162959b440a3` |
| **Active Branch** | `m9c9-merge-authorization-resolution` |
| **Working Tree Status** | Clean |
| **Latest C41 Certification Commit** | `5777ee31` (C41.9 — Commit generated artifact updates from C41 test runs) |
| **Mutation Workflow Commit** | `34d22cb7` (Fix: Typo in mutation workflow) |
| **Mutation Config Hash** | `sha256:backend/pyproject.toml[tool.mutmut]` |
| **Test Config Hash** | `sha256:backend/pyproject.toml[tool.pytest]` |
| **Coverage Config Hash** | N/A (no explicit coverage config) |
| **Latest Commit** | `670bd4c8` — M9-C42: fix REPO_ROOT off-by-one in mutation script and harden report paths |

---

## 0.2 Verification Policy — Authoritative Definitions

| Metric | Authoritative Source | Required Value | Current Value | Gate |
|--------|---------------------|----------------|---------------|------|
| **Mutation Threshold** | `backend/tests/mutation/mutation_config.toml` [thresholds] + `.github/scripts/run_mutation_selective.sh` line 35 | 80% | 50.6% (prior run 32547817936) | Mutation Testing workflow |
| **Line Coverage** | Not explicitly defined in repository | Not defined | Not measured | N/A |
| **Branch Coverage** | Not explicitly defined in repository | Not defined | Not measured | N/A |
| **Property Coverage** | Not explicitly defined | Not defined | Not measured | N/A |
| **Contract Coverage** | Not explicitly defined | Not defined | Not measured | N/A |
| **Mutation Source Paths** | `backend/pyproject.toml` [tool.mutmut] | `src/engines/` | — | — |
| **Mutation Test Command** | `backend/pyproject.toml` [tool.mutmut] | `python3 -m pytest` | — | — |
| **Pytest Test Selection** | `backend/pyproject.toml` [tool.mutmut] `pytest_add_cli_args_test_selection` | `tests/unit/, tests/properties/, tests/invariants/, tests/contract/, tests/integration/` | — | — |
| **CI Timeout** | `.github/workflows/mutation.yml` | 90 minutes | — | — |
| **Mutation Artifacts** | `.github/scripts/run_mutation_selective.sh` | `mutation-summary.json`, `mutation-results.txt`, `surviving-mutants.txt`, `mutation-junit.xml`, `mutation-report.md` | — | — |
| **Quality Gate Enforcement** | `.github/workflows/mutation.yml` | Fail if `mutation_exit_code != '0'` | — | — |

**Governance Defect Identified:** Two mutation configuration files exist with different key conventions:
- `backend/pyproject.toml` [tool.mutmut] uses `source_paths` (new mutmut 3.x key)
- `backend/tests/mutation/mutation_config.toml` [mutmut] uses `paths_to_mutate` (legacy key)

CI script references the former; mutmut 3.7.0 may expect the latter. No single authoritative mutation config is defined in project governance.

---

## 1 CI Mutation Forensics — Latest Failed Run

### Run Identification
- **Workflow Run ID:** 32581565094
- **Timestamp:** 2026-08-22T15:23:47Z
- **Branch:** `m9c9-merge-authorization-resolution`
- **Commit SHA:** `a95ecfb0e338404b5a9109dd08b747ccc9bcdd45`
- **Commit Message:** "M9-C42: Fix mutation script path handling"

### Failure Details
- **Failing Job:** Mutation Testing
- **Failing Step:** step-0003 (`bash .github/scripts/run_mutation_selective.sh`)
- **Mutmut Command:** `mutmut run` (invoked from backend/ directory via run_mutation_selective.sh)
- **Python Environment:** Python 3.12.14
- **Mutmut Version:** 3.7.0
- **Configured Source Paths:** `src/engines/` (from backend/pyproject.toml [tool.mutmut])

### Exact Error
```
FileNotFoundError: Could not figure out where the code to mutate is. 
Please specify it by adding "source_paths=code_dir" in setup.cfg to the [mutmut] section.
```

**Error Origin:** `mutmut.configuration._guess_source_paths()` — called because `source_paths` not resolved from config.

### Metrics (This Run)
| Metric | Value |
|--------|-------|
| Mutants Generated | 0 |
| Mutants Killed | 0 |
| Mutants Survived | 0 |
| Mutants No Tests | 0 |
| Mutants Timeout | 0 |
| Mutation Score | N/A |
| Threshold | 80% |
| Threshold Met | ❌ No |
| Failure Classification | **INFRASTRUCTURE_FAILURE** |
| Duration | 59.6s |

### Artifact Locations
`backend/tests/generated/mutation/` — **not generated** due to early infrastructure failure.

---

## 1.1 Infrastructure Failure Root Cause Analysis

The failure occurs **before any mutants are evaluated**. Mutmut cannot resolve the `source_paths` configuration.

### Hypotheses (ordered by likelihood)

| # | Hypothesis | Evidence |
|---|------------|----------|
| **1** | **mutmut 3.7.0 does not correctly read `source_paths` from pyproject.toml [tool.mutmut]; expects legacy `paths_to_mutate` key** | - `backend/pyproject.toml` uses `source_paths = ["src/engines/"]`<br>- `backend/tests/mutation/mutation_config.toml` uses `paths_to_mutate = "src/engines/"`<br>- mutmut source code falls back to `_guess_source_paths()` when neither `source_paths` nor `paths_to_mutate` resolved |
| **2** | **Working directory when mutmut runs is not `backend/` despite `cd` command** | - Script does `cd "$BACKEND_DIR"` where `BACKEND_DIR="$REPO_ROOT/backend"`<br>- REPO_ROOT fix (`SCRIPT_DIR/../..`) committed in **670bd4c8** — **AFTER** failing run's commit (`a95ecfb0`)<br>- At commit `a95ecfb0`, REPO_ROOT may have resolved incorrectly |
| **3** | **Config file discovery order fails to find pyproject.toml** | - mutmut checks: `setup.cfg` → `pyproject.toml` [tool.mutmut] → `.mutmut.toml` → CLI args<br>- No `setup.cfg` or `.mutmut.toml` in repo<br>- Should find `backend/pyproject.toml` when running from `backend/` |

### Critical Timeline
- **Commit `a95ecfb0`** (failing run): Partial REPO_ROOT fix applied
- **Commit `670bd4c8`** (current HEAD): Complete REPO_ROOT fix + hardened report paths
- **Run 32581565094** executed at commit `a95ecfb0` — fix incomplete
- **Run 32584092266** (cancelled at 16:14:05Z) — may have been re-run with fix but cancelled

**Conclusion:** Current HEAD (670bd4c8) has the complete infrastructure fix. The failing run was against an intermediate commit. A new CI run against current HEAD is required to validate the fix.

---

## 1.2 Prior Successful Mutation Run Data (Reference)

Run 32547817936 (referenced in prior forensics) completed mutation evaluation:

| Metric | Value |
|--------|-------|
| Mutants Generated | 16,427 |
| Mutants Killed | 4,418 |
| Mutants Survived | 4,315 |
| Mutants No Tests | 7,439 |
| Mutants Not Checked | 217 |
| Mutants Timeout | 38 |
| **Mutation Score** | **50.6%** |
| Threshold | 80% |

### Survivor Breakdown (Prior Run)
| Category | Count | Engines Affected |
|----------|-------|------------------|
| **Genuine Test Gaps** (covered but not detected) | 4,315 | behaviour_engine (2159), loan_engine (625), financial_events (675), credit_card_engine (314), recommendation_engine (282), account_engine (163), reconciliation_engine (97) |
| **No Test Coverage** (zero coverage) | 7,439 | financial_intelligence (3050), behaviour_engine (2797), transaction_intelligence (1030), balance_engine (285), ledger_audit_engine (190), reconciliation_engine (54), financial_events (29), loan_engine (4) |

### Priority Mapping (Prior Run)
| Priority | Engines | Survivors | No Tests | Rationale |
|----------|---------|-----------|----------|-----------|
| **P0 — Financial Critical** | loan_engine, credit_card_engine, reconciliation_engine, account_engine | 1,199 | 339 | Monetary calculations, ledger integrity, loan calculations, interest, reconciliation |
| **P1 — Business Rules** | behaviour_engine, financial_events | 2,834 | 2,826 | Business rules, validation, aggregation, forecasting |
| **P2 — Utility/Presentation** | recommendation_engine, balance_engine, ledger_audit_engine, transaction_intelligence, financial_intelligence | 282 | 4,555 | Defensive branches, presentation logic, low-risk utilities |

---

## Configuration Conflict Analysis

### Config A: `backend/pyproject.toml` [tool.mutmut] (Referenced by CI Script)
```toml
source_paths = ["src/engines/"]
also_copy = ["src"]
runner = "python3 -m pytest"
pytest_add_cli_args_test_selection = [
    "tests/unit/", "tests/properties/", "tests/invariants/", 
    "tests/contract/", "tests/integration/"
]
no_progress = true
```

### Config B: `backend/tests/mutation/mutation_config.toml` (Legacy/Baseline)
```toml
[mutmut]
paths_to_mutate = "src/engines/"
tests_dir = "tests/"
runner = "pytest -x --tb=short"

[thresholds]
cashflow_engine = 80
loan_engine = 80
behaviour_engine = 80
credit_card_engine = 80
```

### Conflict
- **Different key names:** `source_paths` vs `paths_to_mutate`
- **Different test selection:** Config A specifies 5 test directories; Config B uses `tests/`
- **Different runner:** Config A uses `python3 -m pytest`; Config B uses `pytest -x --tb=short`
- **CI script references Config A** but mutmut 3.7.0 may expect Config B's key convention

### Recommendation
Per C42 rules and M10 single-authority principle: **Consolidate to `backend/pyproject.toml` [tool.mutmut] as canonical source**. Deprecate `mutation_config.toml` or make it a generated artifact. Do NOT modify threshold (80% is immutable per C42 Hard Rule #2).

---

## Next Steps

### Immediate (Before Phase 2)
1. **Trigger new CI mutation run against current HEAD (670bd4c8)** to validate infrastructure fix
2. **Resolve dual mutation config conflict** — establish single authoritative config
3. **Verify mutmut 3.7.0 reads `source_paths` from pyproject.toml** — if not, align key to `paths_to_mutate` in canonical config

### Phase 2 (After Infrastructure Green)
- Map genuine surviving mutants from successful run to behavioral gaps
- Classify by P0/P1/P2 priority per C42 Phase 2 specification

### Phase 3 (Test Gap Design)
- Design targeted tests for P0 financial-critical survivors first
- Each test must encode a real behavioral invariant (C42 Hard Rule #3)

---

## Evidence Artifacts Required (C42 Compliance)
- [x] `runtime/generated/c42-mutation-forensics.json` — This report (JSON)
- [x] `runtime/generated/c42-mutation-forensics.md` — This report (Markdown)
- [ ] `runtime/generated/c42-test-gap-analysis.json` — Phase 2 output
- [ ] `runtime/generated/c42-test-gap-analysis.md` — Phase 2 output
- [ ] `runtime/generated/c42-coverage-analysis.json` — Phase 9 output
- [ ] `runtime/generated/c42-coverage-analysis.md` — Phase 9 output

---

## Classification
**INFRASTRUCTURE_FAILURE** — Mutation evaluation did not execute. No genuine survivor data from latest run. Prior run (32547817936) shows 50.6% score with 11,754 total unevaluated mutants (4,315 survived + 7,439 no tests). Infrastructure must be validated on current HEAD before proceeding to Phase 2.