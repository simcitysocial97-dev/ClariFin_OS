# Program 5.1 Convergence Plan

**Scope:** Repository, runtime, pipeline, and workflow convergence for the verification system.  
**Goal:** One canonical verification runtime. No duplicates. No orphans. No partial migrations.  
**Status:** Implementation-ready

---

## 1. Runtime Ownership Matrix

### 1.1 Canonical Verification Runtime

| Component | Current Location | Canonical Location | Referenced By | Safe To Remove? | Migration Required? | Reason |
|-----------|-------------------|---------------------|---------------|------------------|---------------------|--------|
| **Planning models** | `runtime/foundation/verification/planner/plan_models.py` | (same — CANONICAL) | `.github/scripts/generate_plan.py`, `backend-verify.yml` | No — this is canonical | No | Defines `VerificationPlan`, `Impact`, `TestSuiteDecision` |
| **Impact rules** | `runtime/foundation/verification/planner/impact_rules.py` | (same — CANONICAL) | `plan_models.py` | No | No | `classify_change()` — path-based change classification |
| **Planner** | `runtime/foundation/verification/planner/planner.py` | (same — CANONICAL) | `runtime.py`, `cli/cli.py` | No | No | `VerificationPlanner` — scope/capability/module resolution |
| **Registry** | `runtime/foundation/verification/registry/registry.py` | (same — CANONICAL) | `planner.py`, `runtime.py`, `cli/cli.py`, `verification.yaml` | No | No | Loads `verification.yaml` into typed capabilities |
| **Validation** | `runtime/foundation/verification/validation/validator.py` | (same — CANONICAL) | `cli/cli.py` (validate command) | No | No | Validates config + registry consistency |
| **Models** | `runtime/foundation/verification/models/` | (same — CANONICAL) | All canonical modules | No | No | Dataclasses: scope, category, status, requirement, target, step |
| **Runtime** | `runtime/foundation/verification/runtime.py` | (same — CANONICAL) | CLI, tests | No | No | `VerificationRuntime` — orchestrates planner + registry + scope resolver |
| **CLI** | `runtime/foundation/verification/cli/cli.py` | (same — CANONICAL) | `pyproject.toml` entry point `verify` | No | No | Click-based CLI: plan, scope, capability, backend, resolve, validate |
| **Config** | `runtime/foundation/verification/verification.yaml` | (same — CANONICAL) | `registry.py` | No | No | Workflow/script/capability definitions |
| **API** | `runtime/foundation/verification/api/__init__.py` | (same — CANONICAL, EMPTY) | None | No | No | Stub — fill in Program 6 if needed |
| **Verification Registry (old)** | `backend/src/verification/runtime/registries.py` | DELETED | `backend/src/verification/intelligence/*` | **Yes** | YES — remove | Delegates to `backend/tests/runtime/registries.py` |
| **Verification Discovery (old)** | `backend/src/verification/runtime/discovery.py` | DELETED | `backend/src/verification/intelligence/dependency_engine.py` | **Yes** | YES — remove | Delegates to `backend/tests/runtime/discovery.py` |

### 1.2 Backend Intelligence Engines (OBSOLETE — Remove)

| Engine | Current Location | Canonical Replacement | Safe To Remove? | Migration Required? | Reason |
|--------|-------------------|----------------------|------------------|---------------------|--------|
| `coverage_engine.py` (264 lines) | `backend/src/verification/intelligence/` | `runtime/system/evidence/collectors/coverage.py` | **Yes** | YES — converge | Evidence collector handles coverage collection |
| `dependency_engine.py` (548 lines) | `backend/src/verification/intelligence/` | `runtime/foundation/repository/analysis/` | **Yes** | YES — converge | Repository graph handles dependency analysis |
| `evidence_engine.py` (443 lines) | `backend/src/verification/intelligence/` | `runtime/system/evidence/aggregator.py` + collectors | **Yes** | YES — converge | Evidence aggregator replaces evidence engine |
| `impact_engine.py` (465 lines) | `backend/src/verification/intelligence/` | `runtime/foundation/verification/planner/planner.py` + `analysis/impact.py` | **Yes** | YES — converge | Planner + impact analysis handle this |
| `metrics_engine.py` (445 lines) | `backend/src/verification/intelligence/` | `runtime/foundation/repository/analysis/metrics.py` | **Yes** | YES — converge | Repository metrics analysis |
| `qa_report.py` (293 lines) | `backend/src/verification/intelligence/` | `runtime/system/evidence/aggregator.py` | **Yes** | YES — converge | Aggregator produces summary reports |
| `regression_engine.py` (242 lines) | `backend/src/verification/intelligence/` | `runtime/system/evidence/` (contract_tests collector) | **Yes** | YES — converge | Contract test evidence collection |
| `report_engine.py` (183 lines) | `backend/src/verification/intelligence/` | `runtime/system/evidence/aggregator.py` | **Yes** | YES — converge | Aggregator produces evidence summary |
| `risk_engine.py` (382 lines) | `backend/src/verification/intelligence/` | `runtime/foundation/verification/validation/validator.py` | **Yes** | YES — converge | Risk is a validation finding |
| `selective_engine.py` (291 lines) | `backend/src/verification/intelligence/` | `runtime/foundation/verification/planner/impact_rules.py` | **Yes** | YES — converge | Impact rules classify selective verification |
| `self_validation.py` (367 lines) | `backend/src/verification/intelligence/` | `testing/runtime/foundation/verification/` | **Yes** | YES — converge | Tests for runtime validation |
| `verification_matrix.py` (310 lines) | `backend/src/verification/intelligence/` | `runtime/foundation/verification/planner/plan_models.py` | **Yes** | YES — converge | VerificationPlan replaces matrix |

### 1.3 Legacy Runtime Package

| Component | Current Location | Canonical Location | Safe To Remove? | Migration Required? | Reason |
|-----------|-------------------|---------------------|------------------|---------------------|--------|
| `backend/tests/runtime/__init__.py` | `backend/tests/runtime/` | DELETED | **Yes** | YES — remove | Causes `runtime` namespace collision |
| `backend/tests/runtime/registries.py` | `backend/tests/runtime/` | `runtime/foundation/verification/registry/` | **Yes** | YES — remove | Registry moved to canonical location |
| `backend/tests/runtime/discovery.py` | `backend/tests/runtime/` | `runtime/foundation/repository/builder/` | **Yes** | YES — remove | Discovery handled by repository scanners |
| `backend/tests/runtime/orchestrator.py` | `backend/tests/runtime/` | `backend-verify.yml` workflow | **Yes** | YES — remove | Orchestration handled by CI workflow |
| `backend/tests/runtime/self_validator.py` | `backend/tests/runtime/` | `runtime/foundation/verification/validation/validator.py` | **Yes** | YES — converge | Validation moved to canonical validator |
| `backend/tests/runtime/ci_targets.py` | `backend/tests/runtime/` | `plan_models.py` `from_changed_files()` | **Yes** | YES — remove | Plan generation handles CI target derivation |

### 1.4 Tools (DUPLICATED — Consolidate)

| Tool | Current Location | Canonical Location | Safe To Remove? | Migration Required? | Reason |
|------|-------------------|---------------------|------------------|---------------------|--------|
| `verification_intelligence.py` (282 lines) | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Old CLI stub for planning; canonical is `verify` CLI |
| `verification_intelligence.py` (323 bytes) | `tools/verification/` | `tools/verification/` | **Yes — delete** | YES — fix/delete | Broken shim referencing non-existent `src/` |
| `mutation_verification.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Mutation test runner |
| `coVF_discover.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Contract coverage discovery |
| `change_intelligence.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Change impact analysis |
| `check_coverage.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Coverage checking |
| `generate_contract_tests.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Contract test generation |
| `generate_health_dashboard.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Health dashboard generation |
| `generate_validation_report.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Validation report generation |
| `mutation_discovery.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Mutation target discovery |
| `selective_verify.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Selective verification runner |
| `test_strength.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Test strength analysis |
| `validation_audit.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Validation audit |
| `validation_orchestrator.py` | `backend/tools/` + `tools/development/` | `tools/development/` | `backend/tools/` version: **Yes** | YES — remove duplicate | Test orchestration |
| `CAPABILITY_HEALTH_DASHBOARD.json` | `backend/tools/` | `docs/reports/` | **Yes — move** | YES — relocate | Health dashboard report |

### 1.5 CI Scripts (Untracked — Must Commit)

| Script | Current Location | Purpose | Git-Tracked? | Action |
|--------|-------------------|---------|---------------|--------|
| `generate_plan.py` | `.github/scripts/` | Generates `verification_plan.json` from git diff using canonical `VerificationPlan.from_changed_files()` | **No** | **Commit** |
| `aggregate_evidence.py` | `.github/scripts/` | Aggregates CI evidence artifacts using `EvidenceAggregator` | **No** | **Commit** |
| `run_aggregator.py` | `.github/scripts/` | Alias for `aggregate_evidence.py` | **No** | **Commit or merge** |

### 1.6 Workflows

| Workflow | Current Location | Status | Action |
|-----------|-------------------|--------|--------|
| `backend-verify.yml` | `.github/workflows/` | New selective pipeline, uses canonical runtime | **Commit** (currently untracked) |
| `backend.yml` | `.github/workflows/` | Old full-suite workflow, unconditional test runs | **Retire** — superseded by backend-verify.yml |
| `quality.yml` | `.github/workflows/` | Fast quality gate (lint, typecheck) | **Keep** |
| `mutation.yml` | `.github/workflows/` | Nightly mutation testing | **Keep** but update imports |
| `nightly-property-tests.yml` | `.github/workflows/` | Nightly property testing | **Keep** |
| `golden.yml` | `.github/workflows/` | Nightly golden dataset tests | **Keep** |
| `ci.yml` | `.github/workflows/` | Superseded full CI | **Retire** |
| `full-validation.yml` | `.github/workflows/` | Superseded full stack | **Retire** |

---

## 2. Validation Pipeline Diagram

The canonical execution flow from local CLI invocation through CI to Evidence Summary.

### 2.1 Local CLI Path (`verify backend`)

```
User: verify backend --plan
  │
  ▼
CLI: runtime/foundation/verification/cli/cli.py:backend_cli_cmd()
  │  (finds repo root, adds to sys.path)
  ▼
VerificationPlan.from_changed_files()     [plan_models.py:112]
  │  Iterates changed files via git diff
  ▼
classify_change(f)                        [impact_rules.py:91]
  │  Path-based rules: engine/service/router/model/test/config
  ▼
ChangeClassification                      [impact_rules.py:14]
  │  change_type, engine_name, blast_radius
  ▼
VerificationPlan (dataclass)              [plan_models.py:54]
  │  run_unit, run_property, run_contract, run_mutation, etc.
  │  impact.engines, impact.services, impact.routers
  ▼
Output: Print plan summary to stdout
  (No test execution — planning only)
```

### 2.2 Local CLI Path (`verify backend` — default)

```
User: verify backend
  │
  ▼
CLI: backend_cli_cmd()
  │  Calls _get_changed_files(repo_root) via git diff
  ▼
VerificationPlan.from_changed_files()     [plan_models.py:112]
  │  Same classification as above
  ▼
subprocess: ruff check backend/src/        [cli.py:451]
  │
  ▼
subprocess: black --check backend/src/      [cli.py:460]
  │
  ▼
For each affected test path:
  subprocess: pytest -x --tb=short <path>   [cli.py:478]
  │  (cwd=backend/)
  ▼
Output: Summary of failures, or "Done."
```

### 2.3 CI Pipeline Path

```
CI: backend-verify.yml (workflow)
  │
  │  PLAN JOB
  ├── Checkout code (fetch-depth: 0)
  ├── Setup Python 3.12
  ├── Find changed files (git diff)
  ├── Run: python3 .github/scripts/generate_plan.py
  │     │
  │     ▼
  │     generate_plan.py:7
  │     └── imports: VerificationPlan.from_changed_files()
  │           [runtime/foundation/verification/planner/plan_models.py:112]
  │     └── classify_change() → impact_rules.py
  │     └── Writes verification_plan.json to repo root
  │     └── Writes GitHub Outputs via to_github_outputs()
  │           [plan_models.py:91]
  │           run_unit='true'/'false'
  │           run_property='true'/'false'
  │           affected_engines=json.dumps(["engine1","engine2"])
  │           unit_paths="tests/unit/engines/cashflow/" etc.
  │     └── Uploads verification_plan.json as artifact
  │
  │  TEST JOBS (parallel, gated by needs.plan.outputs)
  │
  ├── unit-tests (if: run_unit == 'true')
  │   ├── Checkout + Setup Python 3.12
  │   ├── Download verification_plan.json
  │   ├── Install: pip install pytest pytest-cov hypothesis
  │   ├── Install: pip install -e backend/
  │   ├── Run: pytest --cov=src --cov-report=json:coverage.json
  │   │         --junit-xml=tests/generated/junit.xml
  │   │         ${UNIT_PATHS:-tests/unit/}
  │   └── Upload: evidence-unit-<run_id>
  │     (coverage.json, coverage.xml, junit.xml)
  │
  ├── property-tests (if: run_property == 'true')
  │   ├── Same setup
  │   ├── Run: HYPOTHESIS_MAX_EXAMPLES=200 python3 -m pytest
  │   │         --junit-xml=tests/generated/junit-property.xml
  │   │         ${PROPERTY_PATHS:-tests/properties/}
  │   └── Upload: evidence-property-<run_id>
  │     (junit-property.xml)
  │
  ├── contract-tests (if: run_contract == 'true')
  │   ├── Same setup + pip install schemathesis
  │   ├── Run: python3 -m schemathesis run
  │   │         --hypothesis-max-examples=50
  │   │         --output tests/generated/schemathesis-report.json
  │   │         tests/contract/
  │   └── Upload: evidence-contract-<run_id>
  │     (tests/generated/*)
  │
  ├── mutation (if: run_mutation == 'true' AND unit-tests success)
  │   ├── matrix.engine: fromJSON(needs.plan.outputs.affected_engines)
  │   ├── Run: python3 -m mutmut run
  │   │         --paths-to-mutate src/engines/${ENGINE}_engine/
  │   │         --tests-dir tests/unit/engines/${ENGINE}/
  │   ├── Run: mutmut results / mutmut show
  │   └── Upload: evidence-mutation-<engine>-<run_id>
  │     (tests/generated/mutation/)
  │
  ├── integration-tests (if: run_integration == 'true')
  │   └── Run: pytest --junit-xml=junit-integration.xml
  │             ${INTEGRATION_PATHS:-tests/integration/}
  │
  └── golden-tests (if: run_golden == 'true')
      └── Run: pytest -m golden --junit-xml=junit-golden.xml
                ${GOLDEN_PATHS:-tests/}

  │  EVIDENCE JOB (if: always() — runs even if upstream fails)
  ├── Download ALL evidence artifacts to evidence/
  ├── Run: python3 .github/scripts/aggregate_evidence.py evidence/
  │     │
  │     ▼
  │     aggregate_evidence.py:7
  │     └── imports: EvidenceAggregator.from_artifact_directory()
  │           [runtime/system/evidence/aggregator.py:131]
  │     └── aggregate(evidence_dir)
  │     ├── _collect_coverage() → CoverageCollector
  │     │   Finds: coverage.json (pytest-cov format)
  │     ├── _collect_mutation() → MutationCollector
  │     │   Finds: *-results.txt in mutation/ dir
  │     ├── _collect_test_results() → TestResultCollector
  │     │   Finds: junit.xml in backend/tests/generated/
  │     ├── _collect_contract() → ContractCollector
  │     │   Finds: schemathesis-report.json
  │     └── _collect_property_tests() → TestResultCollector
  │         Finds: junit-property.xml
  │     └── Builds: EvidenceSummary (dataclass)
  │         overall_status = "attention_needed" if any issues
  │     └── Writes: evidence_summary.json + evidence_summary.md
  ├── Upload: evidence-summary-<run_id>
  │   (evidence_summary.json, evidence_summary.md)
  └── Post PR comment (if: pull_request)
      Uses github-script to find/update bot comment
      with evidence_summary.md content
```

### 2.4 Evidence Collector Details

| Collector | Module | Artifact Searched | Output Model |
|-----------|--------|-------------------|--------------|
| `CoverageCollector` | `runtime/system/evidence/collectors/coverage.py` | `coverage.json` (pytest-cov totals) | `CoverageEvidence` (percentage, covered/ total lines, gaps) |
| `MutationCollector` | `runtime/system/evidence/collectors/mutation.py` | `*-results.txt`, `*-survivors.txt` | `MutationEvidence` (score, killed/survived/timeout/error/skipped) |
| `TestResultCollector` | `runtime/system/evidence/collectors/test_results.py` | JUnit XML (`junit*.xml`) | `TestResultEvidence` (passed/failed/errors/skipped) |
| `ContractCollector` | `runtime/system/evidence/collectors/contract.py` | Schemathesis JSON report | `ContractEvidence` (endpoints_tested, failures, schema_violations) |
| `PropertyTestCollector` | `runtime/system/evidence/collectors/property_tests.py` | JUnit property XML | `TestResultEvidence` subclass |
| `ContractTestCollector` | `runtime/system/evidence/collectors/contract_tests.py` | Contract JUnit XML | `TestResultEvidence` subclass |

### 2.5 Pipeline Failure Modes

| Stage | Failure Mode | Impact | Mitigation |
|-------|-------------|--------|------------|
| Plan | `generate_plan.py` crashes | All downstream jobs skipped (if: conditions false) | Fix script + error handling |
| Plan | Empty `affected_engines` matrix | Mutation job silently skipped | Add `|| true` guard or default engine |
| Plan | `verification_plan.json` not written | Downstream jobs can't download plan | Verify output exists before continuing |
| Unit | `--cov=src` fails if src missing | Coverage not collected | Ensure `pip install -e backend/` succeeds |
| Mutation | `fromJSON` on empty string | Matrix error, job fails | Ensure `affected_engines` is always valid JSON array |
| Contract | Schemathesis reports errors | Job reports failures | `|| echo "..."` already applied |
| Evidence | Artifacts not found for download | `evidence-summary` artifact empty | `if: always()` ensures evidence job runs |
| Evidence | Aggregator script crashes | No evidence summary | Fix aggregator + add error output |

---

## 3. Root Cleanup Plan

### 3.1 Root-Level Inventory

Every top-level item in the repository root, classified.

| Item | Type | Action | Reason |
|------|------|--------|--------|
| `CAPABILITY_AUDIT.md` | Report | **MOVE** → `docs/reports/audits/capability_audit.md` | Report file at root; belongs in docs/reports/audits/ |
| `CAPABILITY_COVERAGE.md` | Report | **MOVE** → `docs/reports/audits/capability_coverage.md` | Report file at root; belongs in docs/reports/audits/ |
| `clarinfin_verification.egg-info/` | Build artifact | **DELETE** | Unregistered (top_level.txt lists 15 bogus entries); stale pip install artifact |
| `evidence-download/` | Generated | **DELETE** | Transient CI artifact download; not source |
| `evidence_summary.json` | Generated | **DELETE** | CI-generated; should not live at root; produced by `aggregate_evidence.py` |
| `evidence_summary.md` | Generated | **DELETE** | CI-generated; produced by `aggregate_evidence.py` |
| `pyproject.toml` | Config | **KEEP** | Canonical runtime package definition; entry point `verify` |
| `start.sh` | Script | **MOVE** → `scripts/start.sh` | Root-level script; belongs in scripts/ |
| `start.bat` | Script | **MOVE** → `scripts/start.bat` | Root-level script; belongs in scripts/ |
| `verification_plan.json` | Generated | **DELETE** | CI-generated; produced by `generate_plan.py`; should go to `runtime/generated/verification/plan.json` |
| `backend/` | Source | **KEEP** | Backend source, tests, generated |
| `frontend/` | Source | **KEEP** | Frontend source, tests |
| `runtime/` | Source | **KEEP** | Canonical runtime |
| `servers/` | Source | **KEEP** | MCP servers |
| `tools/` | Source | **KEEP** | Development/diagnostics/generators tools |
| `testing/` | Source | **KEEP** | Runtime integration tests |
| `docs/` | Source | **KEEP** | Documentation |
| `memory-bank/` | Source | **KEEP** | Memory context |
| `scripts/` | Source | **KEEP** | Scripts (after moving start.sh/start.bat here) |
| `data/` | Data | **KEEP** | Test data |
| `.github/` | Source | **KEEP** | CI/CD workflows, actions, scripts |
| `target/` | Generated | **DELETE** | Build artifacts (contains .husky directory) |
| `src/` | Stale | **DELETE** | Contains only `__pycache__/` — no source code |
| `.cgcignore` | Config | **KEEP** | CGC analysis ignore patterns |
| `.clinerules` | Config | **KEEP** | Cline agent rules |
| `.coverage` | Generated | **DELETE** | pytest coverage data file |
| `.env.example` | Config | **KEEP** | Environment template |
| `.gitattributes` | Config | **KEEP** | Git attributes |
| `.gitignore` | Config | **KEEP** | Git ignore patterns |
| `.gitignore` additions needed: | — | **MODIFY** | Add `clarinfin_verification.egg-info/`, `evidence_summary.*`, `verification_plan.json`, `evidence-download/`, `target/`, `.venv` |
| `.git/` | System | **KEEP** | Git metadata |
| `.github/` | Source | **KEEP** | CI/CD |
| `.husky/` | Source | **KEEP** | Git hooks |
| `.kilo/` | Config | **KEEP** | Kilo agent configuration |
| `.memory-cache/` | Generated | **DELETE** | Transient cache |
| `.mypy_cache/` | Generated | **DELETE** | Type checker cache (or gitignore) |
| `.pytest_cache/` | Generated | **DELETE** | pytest cache (or gitignore) |
| `.ruff_cache/` | Generated | **DELETE** | Linter cache (or gitignore) |
| `.venv` | Generated | **DELETE** (untrack) | Symlink to backend/venv; must be gitignored |
| `.vscode/` | Config | **KEEP** | Editor config |
| `node_modules/` | Dependency | **DELETE** (gitignore) | Node.js dependencies |
| `tests/` | Duplicate | **DELETE** | Stale duplicates of backend/tests/properties/ |

### 3.2 Generated Artifacts Relocation

| Artifact | Current (Root) | Target Location | Reason |
|----------|----------------|-----------------|--------|
| `verification_plan.json` | Root | `runtime/generated/verification/plan.json` | Generated by `generate_plan.py`; must not live at root |
| `evidence_summary.json` | Root | `runtime/generated/evidence/summary.json` | Generated by `aggregate_evidence.py`; must not live at root |
| `evidence_summary.md` | Root | `runtime/generated/evidence/summary.md` | Generated by `aggregate_evidence.py`; must not live at root |
| `evidence-download/` | Root | Delete after use | Transient CI artifact download directory |

**Action:** Update `generate_plan.py` and `aggregate_evidence.py` to write to `runtime/generated/` instead of CWD.

### 3.3 .gitignore Updates

Add the following to root `.gitignore`:
```
# Verification generated artifacts
verification_plan.json
evidence_summary.json
evidence_summary.md
evidence-download/

# Build artifacts
target/

# Python build
clarinfin_verification.egg-info/
src/

# Virtual environments
.venv
```

Delete `.venv` from git tracking (it is currently tracked):
```bash
git rm --cached .venv
```

---

## 4. Workflow Corrections

### Correction A: `affected_engines` Must Be a JSON Array String

**Current state (canonical):** `to_github_outputs()` in `plan_models.py:99` returns:
```python
"affected_engines": json.dumps(self.impact.engines),
```
This produces a JSON array string like `["cashflow"]`.

**Workflow consumer** (`backend-verify.yml:346`):
```yaml
matrix:
  engine: ${{ fromJSON(needs.plan.outputs.affected_engines) }}
```
This already uses `fromJSON()` correctly.

**Problem:** If `affected_engines` is empty (`json.dumps([])` → `[]`), `fromJSON("[]")` returns an empty array, producing a matrix with zero entries. The mutation job is silently skipped even if `run_mutation == 'true'`.

**Fix:** Wrap `fromJSON` with a fallback:
```yaml
engine: ${{ fromJSON(needs.plan.outputs.affected_engines || '[]') }}
```
And add a job-level guard:
```yaml
strategy:
  fail-fast: false
  matrix:
    engine: ${{ fromJSON(needs.plan.outputs.affected_engines || '[]') }}
    include:
      - engine: "__none__"
```
OR better: ensure `generate_plan.py` always outputs at least one engine when `run_mutation == 'true'`.

### Correction B: `contract-tests` Job Condition

**Current workflow** (`backend-verify.yml:193`):
```yaml
contract-tests:
  if: needs.plan.outputs.run_contract == 'true'
```

This is **already correct**. No change needed. The condition uses string comparison `== 'true'` which matches `str(True).lower()` output from `to_github_outputs()`.

### Correction C: Review Every GitHub Output Type

| Output | Type in `to_github_outputs()` | Workflow Consumer | Correct? |
|--------|------------------------------|-------------------|----------|
| `run_unit` | `str(bool).lower()` → `'true'`/`'false'` | `if: needs.plan.outputs.run_unit == 'true'` | ✅ |
| `run_property` | `str(bool).lower()` | `if: needs.plan.outputs.run_property == 'true'` | ✅ |
| `run_contract` | `str(bool).lower()` | `if: needs.plan.outputs.run_contract == 'true'` | ✅ |
| `run_mutation` | `str(bool).lower()` | `if: needs.plan.outputs.run_mutation == 'true'` | ✅ |
| `run_integration` | `str(bool).lower()` | `if: needs.plan.outputs.run_integration == 'true'` | ✅ |
| `run_golden` | `str(bool).lower()` | `if: needs.plan.outputs.run_golden == 'true'` | ✅ |
| `affected_engines` | `json.dumps(list[str])` | `fromJSON(needs.plan.outputs.affected_engines)` | ✅ (with empty fix per Correction A) |
| `affected_services` | `json.dumps(list[str])` | Not consumed (unused in workflow) | N/A |
| `affected_routers` | `json.dumps(list[str])` | Not consumed (unused in workflow) | N/A |
| `blast_radius` | `str` | Not consumed (unused in workflow) | N/A |
| `unit_paths` | `" ".join(list[str])` | `UNIT_PATHS: ${{ ... }}` → shell default `${UNIT_PATHS:-tests/unit/}` | ✅ |
| `property_paths` | `" ".join(list[str])` | `PROPERTY_PATHS: ${{ ... }}` → shell `${PROPERTY_PATHS:-tests/properties/}` | ✅ |
| `contract_paths` | `" ".join(list[str])` | Not consumed (unused in workflow) | N/A |
| `mutation_targets` | `" ".join(list[str])` | Not consumed (unused in workflow) | N/A |
| `integration_paths` | `" ".join(list[str])` | `INTEGRATION_PATHS: ${{ ... }}` → shell default | ✅ |
| `golden_paths` | `" ".join(list[str])` | `GOLDEN_PATHS="${{ ... }}"` → shell default | ✅ |

**Finding:** All outputs have correct types. No string parsing inside YAML. Boolean outputs use string comparison (correct for GHA). JSON array outputs use `fromJSON()`. Path outputs use shell defaults.

**Action items:**
1. Fix empty `affected_engines` fallback (Correction A)
2. Remove unused outputs (`affected_services`, `affected_routers`, `blast_radius`, `contract_paths`, `mutation_targets`) or document their intended use
3. Ensure `generate_plan.py` is committed to git

### Correction D: `.github/scripts/` Must Be Committed

**Finding:** `generate_plan.py`, `aggregate_evidence.py`, and `run_aggregator.py` are NOT git-tracked, but `backend-verify.yml` (also untracked) references them. A fresh checkout would fail.

**Fix:** Commit all three scripts before converging.

---

## 5. Migration Execution Order

> **Rule:** Each step must end with validation. No step may be skipped. If validation fails, execute rollback (§7).

### Pre-Step 0: Baseline Capture

```bash
# 0.1 Capture current test counts
cd backend && python -m pytest tests/ -q --tb=no 2>&1 | tail -3
# Record: ___ passed, ___ failed, ___ errors

# 0.2 Capture current import state
python3 -c "
from runtime.foundation.verification.planner.plan_models import VerificationPlan
from runtime.foundation.verification.planner.impact_rules import classify_change
print('Canonical imports OK')
"

# 0.3 Commit baseline
git checkout -b convergence/program-5.1
git add -A && git commit -m "Pre-convergence baseline"
```

**Validation:** All baseline counts recorded. Canonical imports resolve.

---

### Step 1: Commit Untracked CI Scripts and Workflow

**Action:**
- `git add .github/scripts/generate_plan.py`
- `git add .github/scripts/aggregate_evidence.py`
- `git add .github/scripts/run_aggregator.py`
- `git add .github/workflows/backend-verify.yml`
- Commit: "Track canonical verification pipeline scripts and workflow"

**Validation:**
- `git ls-files -- '.github/scripts/'` includes generate_plan.py, aggregate_evidence.py, run_aggregator.py
- `git ls-files -- '.github/workflows/backend-verify.yml'` returns the file
- `python3 .github/scripts/generate_plan.py` runs without error and produces `verification_plan.json`

---

### Step 2: Resolve `runtime` Namespace Collision

**Action:**
- Rename `backend/tests/runtime/` → `backend/tests/verification_runtime/` (temporary name to break collision)
- Update all imports: `from runtime.` → `from verification_runtime.` (within backend/tests/ scope)
- Update `backend/src/verification/runtime/discovery.py` delegation references
- Update pytest `pythonpath` if needed

**Files affected:**
- `backend/tests/runtime/__init__.py`
- `backend/tests/runtime/registries.py`
- `backend/tests/runtime/discovery.py`
- `backend/tests/runtime/orchestrator.py`
- `backend/tests/runtime/self_validator.py`
- `backend/tests/runtime/ci_targets.py`
- `backend/src/verification/intelligence/*.py` (import references)
- `backend/src/verification/runtime/discovery.py` (delegation reference)
- `backend/tools/verification_intelligence.py` (imports)
- `backend/tools/mutation_verification.py` (imports)
- `tools/development/verification_intelligence.py` (imports)

**Validation:**
```bash
# Import resolves to canonical runtime
python3 -c "import runtime; print(runtime.__file__)"  # Should show runtime/foundation/__init__.py
# Old runtime tests still pass
cd backend && python -m pytest tests/verification_runtime/ -q --tb=no
```

---

### Step 3: Remove Broken Shim and Consolidate Tools

**Action:**
- Delete `tools/verification/verification_intelligence.py` (broken shim — references non-existent `src/`)
- Delete `tools/verification/` directory (only contains the broken shim)
- Delete all files from `backend/tools/` EXCEPT `CAPABILITY_HEALTH_DASHBOARD.json`
- Move `CAPABILITY_HEALTH_DASHBOARD.json` → `docs/reports/audits/`
- Delete `backend/tools/__init__.py`
- Delete `backend/tools/__pycache__/`
- Verify `tools/development/` has all needed scripts (14 .py files + `__init__.py`)

**Validation:**
```bash
ls tools/verification/  # Should not exist
ls backend/tools/       # Should be empty (or deleted)
diff <(ls tools/development/*.py) <(echo "change_intelligence.py check_coverage.py coVF_discover.py ... ")
python3 -m py_compile tools/development/verification_intelligence.py  # No syntax errors
```

---

### Step 4: Remove Stale Root-Level Source Directory

**Action:**
- Delete root `src/` directory (contains only `clarinfin_verification.egg-info/` + `__pycache__/`)
- Delete root `clarinfin_verification.egg-info/` directory
- Add `clarinfin_verification.egg-info/` and `src/` patterns to `.gitignore`

**Validation:**
```bash
ls src/  # Should not exist
ls clarinfin_verification.egg-info/  # Should not exist
python -m pip install -e .  # Should still work (regenerates egg-info)
```

---

### Step 5: Remove Duplicate Root-Level Tests

**Action:**
- Delete `tests/` directory (root-level duplicate of `backend/tests/properties/`)
- Verify `backend/tests/properties/` has all needed test files
- Update any references to root `tests/` in CI scripts or documentation

**Validation:**
```bash
cd backend && python -m pytest tests/properties/ -q --tb=no  # All property tests pass
```

---

### Step 6: Clean Up Root-Level Generated Artifacts

**Action:**
- Delete `verification_plan.json` from root (regenerated on each CI run)
- Delete `evidence_summary.json` from root (regenerated on each CI run)
- Delete `evidence_summary.md` from root (regenerated on each CI run)
- Delete `evidence-download/` from root (transient CI artifact)
- Delete `target/` from root (build artifacts)
- Delete `.coverage` from root (pytest data)
- Uncache `.venv` from git (`git rm --cached .venv`)
- Update `.gitignore` with all generated patterns

**Validation:**
```bash
git status --short | grep verification_plan  # Empty
git status --short | grep evidence_summary  # Empty
git status --short | grep .venv             # Empty (untracked)
```

---

### Step 7: Update `generate_plan.py` Output Path

**Action:**
- Modify `generate_plan.py` to write `verification_plan.json` → `runtime/generated/verification/plan.json`
- Update `backend-verify.yml` plan job to upload/download from new path
- Update evidence collection to look for plan in new location

**Current code** (`generate_plan.py:44`):
```python
with open("verification_plan.json", "w") as f:
    f.write(plan.to_json())
```

**New code:**
```python
output_dir = Path("runtime/generated/verification")
output_dir.mkdir(parents=True, exist_ok=True)
plan_path = output_dir / "plan.json"
with open(plan_path, "w") as f:
    f.write(plan.to_json())
```

**Validation:**
```bash
python3 .github/scripts/generate_plan.py
ls runtime/generated/verification/plan.json  # Exists
```

---

### Step 8: Update `aggregate_evidence.py` Output Paths

**Action:**
- Modify `aggregate_evidence.py` to write `evidence_summary.json` → `runtime/generated/evidence/summary.json`
- Modify `aggregate_evidence.py` to write `evidence_summary.md` → `runtime/generated/evidence/summary.md`
- Update `backend-verify.yml` evidence job artifact upload path
- Update CLI evidence command references

**Current code** (`aggregate_evidence.py:15-16`):
```python
summary.save(Path("evidence_summary.json"))
summary.save_markdown(Path("evidence_summary.md"))
```

**New code:**
```python
output_dir = Path("runtime/generated/evidence")
output_dir.mkdir(parents=True, exist_ok=True)
summary.save(output_dir / "summary.json")
summary.save_markdown(output_dir / "summary.md")
```

**Validation:**
```bash
python3 .github/scripts/aggregate_evidence.py evidence/  # (with test artifacts)
ls runtime/generated/evidence/summary.json  # Exists
ls runtime/generated/evidence/summary.md   # Exists
```

---

### Step 9: Apply Workflow Corrections

**Action:**
- Fix `affected_engines` matrix to handle empty array:
  ```yaml
  engine: ${{ fromJSON(needs.plan.outputs.affected_engines || '[]') }}
  ```
- Add `include` fallback for mutation matrix when no engines affected:
  ```yaml
  strategy:
    fail-fast: false
    matrix:
      engine: ${{ fromJSON(needs.plan.outputs.affected_engines || '[]') }}
  ```
  (No include needed — empty matrix correctly skips mutation)
- Verify `contract-tests` condition uses `== 'true'` (already correct)
- Verify all `fromJSON()` for matrix inputs consume `json.dumps()` outputs (already correct)
- Ensure `if: always()` on evidence job (already correct)

**Validation:**
```bash
# YAML syntax check
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/backend-verify.yml'))"
# Dry-run plan generation
python3 .github/scripts/generate_plan.py
cat verification_plan.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('engines:', d['impact']['engines']); print('run_mutation:', d['mutation']['run'])"
```

---

### Step 10: Remove Obsolete Backend Intelligence

**Action:**
- Remove `backend/src/verification/` directory (17 Python files: 12 intelligence engines + 3 runtime + 2 `__init__.py`)
- Remove `backend/src/verification_intelligence.py` (stub CLI)
- Update any remaining references in `backend-src/` code that imported `src.verification.*`

**Files to check for references:**
```bash
grep -rn "src.verification\|verification.intelligence\|verification.runtime" backend/src/ --include="*.py" | grep -v __pycache__
```

**Validation:**
```bash
# No remaining references to old verification
grep -rn "src.verification\|verification.intelligence" backend/src/ --include="*.py"  # Should be empty
# Backend tests still pass
cd backend && python -m pytest tests/ -q --tb=no
# Canonical imports still work
python3 -c "from runtime.foundation.verification import runtime; print('OK')"
```

---

### Step 11: Update Verification YAML and Registry

**Action:**
- Fix `runtime/foundation/verification/verification.yaml`:
  - Change `evidence: enabled: false` → `enabled: true` (evidence runtime is implemented)
  - Change `cli: enabled: false` → `enabled: true` (CLI is implemented)
  - Change `intelligence: enabled: false` → `enabled: true` (planning is implemented)
- Fix `runtime/foundation/verification/__init__.py` — remove placeholder comment
- Fix `runtime/system/evidence/README.md` — update from "Not yet implemented" to "Implemented"
- Fix `runtime/foundation/__init__.py` — remove misplaced verification config comment

**Validation:**
```bash
# YAML parses correctly
python3 -c "import yaml; yaml.safe_load(open('runtime/foundation/verification/verification.yaml')); print('YAML OK')"
# Registry loads
python3 -c "from runtime.foundation.verification.registry import VerificationRegistry; r=VerificationRegistry(); r.load(); print(f'Workflows: {len(r._workflows)}'); print(f'Capabilities: {len(r._capabilities)}')"
```

---

### Step 12: Retire Old Workflows

**Action:**
- Add "retired" notice to `backend.yml` (or remove trigger):
  ```yaml
  on:
    # RETIRED: Superseded by backend-verify.yml
    push:
      branches: []
    pull_request:
      branches: []
  ```
- Add "retired" notice to `ci.yml` and `full-validation.yml`

**Validation:**
```bash
# Verify no workflow conflicts
grep -l "RETIRED" .github/workflows/*.yml  # Should include backend.yml, ci.yml, full-validation.yml
```

---

### Step 13: Update .gitignore and Verify Clean State

**Action:**
- Ensure `.gitignore` includes all generated patterns
- Run `git status --short` to verify no stray files
- Commit all remaining changes

**Validation:**
```bash
# No untracked files (except .venv which should be ignored)
git status --short  # Should show only intended changes
# Root is clean of generated artifacts
ls *.json *.md 2>/dev/null | grep -E "verification_plan|evidence_summary"  # Should be empty
```

---

## 6. Program Boundary

### What Belongs in Program 5.1 (This Plan)

**Program 5.1 contains ONLY:**

| Category | Scope | Details |
|----------|-------|---------|
| Repository convergence | Merge old `backend.tools` → `tools.development` | Remove 14 duplicate files; track CI scripts; retire old workflows |
| Runtime convergence | Migrate `backend.src.verification.*` → `runtime.foundation.verification.*` | 12 intelligence engines → canonical submodules; 6 legacy runtime files → canonical runtime.py |
| Pipeline convergence | `pyproject.toml` → `backend-verify.yml` → `evidence_summary` | Single pipeline: plan → test → collect → aggregate |
| Workflow correctness | `.github/workflows/backend-verify.yml` | Fix affected_engines, contract-tests condition, output types |
| Artifact cleanup | Root-level cleanup | Delete src/, tests/, target/, generated artifacts; update .gitignore |

### What Belongs in Program 6

**Program 6 — Verification Test Coverage Expansion:**

- Tests for `runtime/foundation/verification/` (currently 0 tests)
- Tests for `runtime/system/evidence/` (README says "do not write tests" — contradiction)
- Tests for `runtime/foundation/repository/` modules beyond the existing scanner test
- Property-based tests migrated from legacy `backend/tests/properties/` to `testing/runtime/foundation/verification/`
- Mutation testing for canonical runtime code

### What Belongs in Program 7

**Program 7 — Frontend CI/CD Integration:**

- Frontend verification workflow (`frontend.yml`, `frontend-build.yml`)
- Frontend evidence collection
- API contract verification between frontend and backend
- Playwright test pipeline
- All frontend-specific testing and coverage

### Boundary Enforcement

| Concern | Program 5.1? | Notes |
|---------|:------------:|-------|
| `frontend/` directory | ❌ | Frontend convergence is Program 7 |
| `frontend/tests/` | ❌ | Not in scope |
| Frontend coverage | ❌ | Out of scope |
| UI changes | ❌ | Out of scope |
| Visualization tools | ❌ | Out of scope |
| `backend/src/verification/intelligence/` | ✅ | Core migration target |
| `tools/verification/` broken shim | ✅ | Must be deleted |
| `.github/workflows/backend-verify.yml` | ✅ | Can correct workflow logic |
| `runtime/foundation/verification/verification.yaml` | ✅ | Config consistency fix |
| Evidence README contradiction | ✅ | Documentation fix only |

---

## 7. Validation Gates

### Gate 1: Canonical Runtime Imports

```bash
python3 -c "
from runtime.foundation.verification.planner.plan_models import VerificationPlan
from runtime.foundation.verification.planner.impact_rules import classify_change, ChangeClassification
from runtime.foundation.verification.planner.planner import VerificationPlanner, PlanningContext, plan_verification
from runtime.foundation.verification.registry import VerificationRegistry, get_registry
from runtime.foundation.verification.models import VerificationScope, VerificationCategory, VerificationPlan as VPlan
from runtime.foundation.verification.runtime import VerificationRuntime, get_runtime
from runtime.foundation.verification.validation import validate_all, ValidationFinding
from runtime.foundation.verification.cli.cli import cli
from runtime.system.evidence.aggregator import EvidenceAggregator, EvidenceSummary
from runtime.system.evidence.collectors import CoverageCollector, MutationCollector, TestResultCollector, ContractCollector
from runtime.system.evidence.models.evidence import EvidenceArtifact, EvidenceCollectionResult, VerificationEvidence
print('All canonical imports OK')
"
```

### Gate 2: Namespace Collision Resolved

```bash
python3 -c "import runtime; print(runtime.__file__)"
# Must show: runtime/foundation/__init__.py (NOT backend/tests/runtime/)
```

### Gate 3: Plan Generation Works

```bash
python3 .github/scripts/generate_plan.py
python3 -c "
import json
d = json.load(open('runtime/generated/verification/plan.json'))
print('Plan ID:', d['plan_id'])
print('Engines:', d['impact']['engines'])
print('Run unit:', d['unit_tests']['run'])
print('Run mutation:', d['mutation']['run'])
"
```

### Gate 4: Evidence Aggregation Works

```bash
# Requires CI artifacts in evidence/ directory
python3 .github/scripts/aggregate_evidence.py evidence/
python3 -c "
import json
d = json.load(open('runtime/generated/evidence/summary.json'))
print('Summary ID:', d['summary_id'])
print('Overall status:', d['overall_status'])
print('Backend keys:', list(d['backend'].keys()))
"
```

### Gate 5: Backend Tests Pass

```bash
cd backend && python -m pytest tests/ -q --tb=no
# Must match or improve upon baseline count
```

### Gate 6: No Old References

```bash
# No references to old verification intelligence
grep -rn "src.verification.intelligence\|backend/src/verification" . \
  --include="*.py" --include="*.yml" --include="*.yaml" --include="*.sh" \
  | grep -v __pycache__ | grep -v .pyc | grep -v .git/
# Should be empty

# No references to backend/tools/ duplicate scripts
grep -rn "backend/tools/verification_intelligence\|backend/tools/mutation_verification" . \
  --include="*.py" --include="*.yml" --include="*.sh" \
  | grep -v __pycache__ | grep -v .git/
# Should be empty
```

### Gate 7: Root Clean

```bash
# No generated artifacts at root
ls verification_plan.json evidence_summary.json evidence_summary.md evidence-download/ src/ 2>/dev/null
# Should fail (files don't exist)

# .venv not tracked
git ls-files -- '.venv'  # Should be empty
```

### Gate 8: Workflow YAML Valid

```bash
python3 -c "
import yaml
for wf in ['.github/workflows/backend-verify.yml']:
    yaml.safe_load(open(wf))
    print(f'{wf}: valid YAML')
"
```

---

## 8. Rollback Strategy

```bash
# If any step fails validation:
git checkout main
# Everything restored to pre-convergence baseline

# Or, to rollback to pre-step state:
git reset --hard <commit-before-step-N>

# To inspect what would be lost:
git diff HEAD~1 --stat
```

**Critical checkpoints** (commit after each step):
1. `commit-convergence-step-1-scripts` — CI scripts and workflow committed
2. `commit-convergence-step-2-namespace-fix` — namespace collision resolved
3. `commit-convergence-step-3-tools-consolidated` — tools deduplicated
4. `commit-convergence-step-4-stale-removal` — src/ and egg-info removed
5. `commit-convergence-step-5-test-dedup` — root tests/ removed
6. `commit-convergence-step-6-root-cleanup` — root artifacts cleaned
7. `commit-convergence-step-7-8-output-paths` — output paths updated
8. `commit-convergence-step-9-workflow-fix` — workflow corrections applied
9. `commit-convergence-step-10-old-removal` — old intelligence removed
10. `commit-convergence-step-11-yaml-fix` — YAML/config fixes applied
11. `commit-convergence-step-12-13-retire-cleanup` — old workflows retired, final cleanup

---

## 9. Exit Criteria

Migration is complete ONLY when ALL of the following are true:

- [ ] **One verification runtime:** `runtime/foundation/verification/` is the sole canonical verification runtime; `backend/src/verification/` is fully removed
- [ ] **No namespace collision:** `import runtime` resolves to `runtime/foundation/__init__.py`, not `backend/tests/`
- [ ] **No duplicate tools:** `backend/tools/` is empty/deleted; `tools/development/` is canonical
- [ ] **No broken shims:** `tools/verification/` is deleted; `verify` CLI is the sole entry point
- [ ] **One pipeline:** `backend-verify.yml` is the sole active verification workflow; `backend.yml`/`ci.yml`/`full-validation.yml` are retired
- [ ] **All CI scripts committed:** `generate_plan.py`, `aggregate_evidence.py`, `run_aggregator.py` are git-tracked
- [ ] **Generated artifacts relocated:** `verification_plan.json` → `runtime/generated/verification/plan.json`; `evidence_summary.*` → `runtime/generated/evidence/`
- [ ] **Root clean:** No `src/`, `target/`, `evidence-download/`, `*.egg-info` at root
- [ ] **No root-level duplicates:** `tests/` directory deleted
- [ ] **YAML configuration consistent:** `verification.yaml` has `enabled: true` for implemented runtimes
- [ ] **Documentation consistent:** Evidence README matches implementation status
- [ ] **All validation gates pass** (§6)
- [ ] **Backend tests pass** at the same or better count than baseline
- [ ] **No circular dependencies** between old and new code (old code is fully removed)
- [ ] **`pip install -e .` works** from repo root (pyproject.toml entry point resolves)
- [ ] **`.venv` is gitignored** (not tracked)
- [ ] **Clean commit history** (one commit per migration step, as per checkpoints in §7)

---

READY FOR IMPLEMENTATION
