# Program 5 Verification Audit

## 1. Deliverables Verified

| Component | Path | LOC | Status | Issues |
|-----------|------|-----|--------|--------|
| Impact Rules Engine | `runtime/foundation/verification/planner/impact_rules.py` | 133 | PASS | None |
| Verification Plan Model | `runtime/foundation/verification/planner/plan_models.py` | 235 | PARTIAL | Generated files treated as test paths; golden-test reason/run mismatch; mutation targets include generated files |
| Verification Planner | `runtime/foundation/verification/planner/planner.py` | 652 | FAIL | TODO marker at line 320; `...` placeholder for endpoint resolution (unimplemented) |
| Verification CLI | `runtime/foundation/verification/cli/cli.py` | 634 | FAIL | `import click` (3rd-party); `verify evidence` command broken at runtime (ImportError) |
| Evidence CLI | `runtime/system/evidence/cli/cli.py` | 149 | FAIL | `main()` crashes with `ImportError` in `api/__init__.py` |
| Coverage Collector | `runtime/system/evidence/collectors/coverage.py` | 129 | FAIL | `collect()` returns `CoverageEvidence` not `List[EvidenceArtifact]` (violates base contract) |
| Mutation Collector | `runtime/system/evidence/collectors/mutation.py` | 157 | FAIL | `collect()` returns `MutationEvidence` not `List[EvidenceArtifact>` (violates base contract) |
| Test Result Collector | `runtime/system/evidence/collectors/test_results.py` | 129 | FAIL | `collect()` returns `TestResultEvidence` not `List[EvidenceArtifact>` (violates base contract) |
| Contract Collector | `runtime/system/evidence/collectors/contract.py` | 136 | FAIL | `collect()` returns `ContractEvidence` not `List[EvidenceArtifact>` (violates base contract); `collect_artifacts` references non-existent paths |
| Property Test Collector | `runtime/system/evidence/collectors/property_tests.py` | 64 | PARTIAL | Not exported from `collectors/__init__.py`; `artifact_type` is "property_test" (mismatched) |
| Contract Test Collector | `runtime/system/evidence/collectors/contract_tests.py` | 75 | PARTIAL | Not exported from `collectors/__init__.py`; `artifact_type` is "contract_test" (mismatched) |
| Collector Base | `runtime/system/evidence/collectors/base.py` | 83 | FAIL | `IOError` (deprecated alias for OSError at line 59); `_artifact()` raises `ValueError` for paths outside workspace |
| Collector Package Init | `runtime/system/evidence/collectors/__init__.py` | 27 | FAIL | Missing exports: `PropertyTestCollector`, `ContractTestCollector` |
| Evidence Aggregator | `runtime/system/evidence/aggregator.py` | 405 | PARTIAL | Path mismatches for mutation/contract discovery; emojis in markdown output; hardcoded mutation threshold (60.0) |
| Evidence API (package) | `runtime/system/evidence/api/__init__.py` | 190 | FAIL | `ImportError` — imports non-exported `PropertyTestCollector`/`ContractTestCollector`; `collect()` return-type mismatch would cause `TypeError` |
| Evidence API (module) | `runtime/system/evidence/api.py` | 187 | FAIL | Shadowed by `api/` package (dead code); uses `__dict__` on slotted dataclass (AttributeError); calls non-existent `validate_inputs()` |
| Evidence Models | `runtime/system/evidence/models/evidence.py` | 156 | PASS | None |
| Evidence Models Init | `runtime/system/evidence/models/__init__.py` | 21 | PASS | None |
| Evidence Package Init | `runtime/system/evidence/__init__.py` | 12 | PASS | None |
| Evidence Ingestion | `runtime/system/evidence/ingestion/pipeline.py` | 219 | PARTIAL | Broad `except Exception: pass` (3 occurrences); not used by workflow |
| Registry | `runtime/foundation/verification/registry/registry.py` | 929 | PARTIAL | `import yaml` (3rd-party, undeclared dependency); `pass` statement at line 147 |
| Planner Models | `runtime/foundation/verification/models/model.py` | 193 | FAIL | `dict[str, any]` lowercase `any` (line 143); `VerificationSummary` in `__all__` but never defined (line 34 of `__init__.py`) |
| Scope Resolver | `runtime/foundation/verification/models/scope.py` | 493 | PASS | None |
| Models Init | `runtime/foundation/verification/models/__init__.py` | 40 | FAIL | `__all__` includes `VerificationSummary` which is not importable |
| Runtime | `runtime/foundation/verification/runtime.py` | 303 | PASS | None |
| Validation | `runtime/foundation/verification/validation/validator.py` | 332 | PARTIAL | `import yaml` (3rd-party) inside function (line 61) |
| Validation Init | `runtime/foundation/verification/validation/__init__.py` | 13 | PASS | None |
| Registry Init | `runtime/foundation/verification/registry/__init__.py` | 19 | PASS | None |
| Planner Init | `runtime/foundation/verification/planner/__init__.py` | 43 | PASS | None |
| CLI Init | `runtime/foundation/verification/cli/__init__.py` | 0 | PASS | Empty (placeholder) |
| Verification YAML | `runtime/foundation/verification/verification.yaml` | ~208 | PASS | None |
| Plan Script | `.github/scripts/generate_plan.py` | 69 | PASS | Works; writes `verification_plan.json` and GitHub outputs |
| Aggregator Script | `.github/scripts/aggregate_evidence.py` | 27 | PASS | Works when evidence files are present |
| Aggregator Script (dup) | `.github/scripts/run_aggregator.py` | 27 | FAIL | Duplicate of `aggregate_evidence.py` (confusing) |
| pyproject.toml | `pyproject.toml` | 19 | FAIL | Declares `click>=8.0` (3rd-party); does NOT declare `pyyaml` (used but undeclared) |
| Workflow | `.github/workflows/backend-verify.yml` | 447 | FAIL | Mutation matrix `fromJSON` generates invalid JSON; `contract-tests` missing `if` condition; schemathesis output path mismatch; artifact name mismatch |

---

## 2. Specification Deviations

### 2.1 Impact Rules (Phase 3)

| Function | Spec Behavior | Actual Behavior | Deviation |
|----------|--------------|-----------------|-----------|
| `engine_changed()` | True if `backend/src/engines/` | Matches | None |
| `service_changed()` | True if `backend/src/services/` | Matches | None |
| `router_changed()` | True if `backend/src/routers/` | Matches | None |
| `model_changed()` | True if `backend/src/models/`, `backend/src/core/dtos/`, `backend/src/core/domain/` | Matches | None |
| `test_changed()` | True if `backend/tests/` | Matches | **Spec deviation**: Matches ALL files under `backend/tests/`, including generated artifacts (`backend/tests/generated/*.json`, `*.md`). This causes pytest to receive non-Python files as test paths. |
| `config_changed()` | Checks `backend/pyproject.toml`, `backend/.coveragerc`, `backend/ruff.toml`, `backend/*.cfg` | Matches | None |
| `extract_engine_name()` | Extracts name from `_engine` suffix | Returns "loan" for "loan_engine" (strips `_engine`); returns "cashflow" for `cashflow_engine.py` | **Spec deviation**: Engine name has `_engine` suffix stripped. Workflow reconstructs `${{ matrix.engine }}_engine` for mutmut paths, but this fails for file-based engines (`cashflow_engine.py` → `src/engines/cashflow_engine/` which is a file path, not a directory). |
| `extract_router_name()` | Extracts router from filename | Returns filename without `.py` (e.g., "loans" for `loans.py`); returns `__init__` for `__init__.py` | Minor: `__init__.py` → router name `__init__` is semantically wrong but follows the algorithm literally |
| `classify_change()` | 6-rule classification with blast radius | Matches spec exactly | None |

**Verified output for all 13 test paths**: All rules classify correctly per their implementation logic. No mismatches with the documented rule descriptions in docstrings.

### 2.2 Verification Plan (Phase 4)

| Decision | Spec Expectation | Actual | Deviation |
|----------|-----------------|--------|-----------|
| `golden_tests.run` | Should be True only for config changes | True for engine changes (golden_paths gets "tests/") | Engine changes populate golden_paths, triggering golden tests with reason "No golden dependency" |
| `golden_tests.reason` | Should explain why running | "No golden dependency" when run=True (engine change) | Reason/run mismatch: tests run but reason denies dependency |
| `unit_tests.paths` | Should contain test source directories | Includes `tests/generated/change-report.json`, `tests/generated/test-strength.json` etc. | Generated artifacts classified as test files via `_strip_backend(f)` for `test_changed` files |
| `mutation_targets` | Should list files to mutate | Includes `_strip_backend(f)` for ALL non-test files when `has_model_change` (line 161) | When model changes occur, ALL non-test files (including generated artifacts) are added as mutation targets |
| `impact.blast_radius` | Full for config, high for model, medium for engine/service/router, low for test/other | Matches | None |

### 2.3 Evidence Collector Interface (Phase 5)

Base class `EvidenceCollector.collect()` (base.py:46):
```python
@abstractmethod
def collect(self) -> List[EvidenceArtifact]:
```

Concrete implementations:
- `CoverageCollector.collect(self, artifact_path=None) -> CoverageEvidence` — different signature, different return type
- `MutationCollector.collect(self, artifact_path=None) -> MutationEvidence` — different signature, different return type
- `TestResultCollector.collect(self, artifact_path=None) -> TestResultEvidence` — different signature, different return type
- `ContractCollector.collect(self, artifact_path=None) -> ContractEvidence` — different signature, different return type
- `PropertyTestCollector.collect(self) -> List[EvidenceArtifact]` — matches base contract
- `ContractTestCollector.collect(self) -> List[EvidenceArtifact]` — matches base contract

### 2.4 Two Parallel Evidence APIs

`runtime/system/evidence/api.py` (module, 187 lines) and `runtime/system/evidence/api/__init__.py` (package, 190 lines) both define `collect_all_evidence`, `build_verification_evidence`, `write_verification_summary` with incompatible signatures:

- `api.py`: `collect_all_evidence(workspace_root)`, `build_verification_evidence(commit_sha, branch, artifacts, status)`
- `api/__init__.py`: `collect_all_evidence(workspace_root) -> EvidenceCollectionResult`, `build_verification_evidence(commit_sha, branch, artifacts, property_tests=None, contract_tests=None, status)`

Python resolves the package over the module — `api.py` is dead code. The package's `collect_all_evidence()` would crash with `TypeError` even if the `ImportError` were fixed (calls `asdict(a)` on non-iterable `CoverageEvidence`).

### 2.5 Two Parallel VerificationPlan Classes

| Class | Location | Fields | Used By |
|-------|----------|--------|---------|
| `VerificationPlan` (selective) | `plan_models.py:55` | plan_id, generated_at, triggered_by, changed_files, impact, unit_tests, property_tests, contract_tests, mutation, integration_tests, golden_tests | `generate_plan.py`, CLI `backend_cli_cmd` |
| `VerificationPlan` (rich) | `models/model.py:163` | id, name, scope, created_at, targets, steps, required_workflows, required_scripts, estimated_duration_seconds, metadata | `planner.py`, CLI `plan` command, `runtime.py` |

Both named `VerificationPlan` — the `__init__.py` re-exports the selective one, while `models/__init__.py` re-exports the rich one. The CLI imports both with aliases.

---

## 3. Architectural Issues

1. **Broken evidence collection pipeline** (CRITICAL): `api/__init__.py` `collect_all_evidence()` is unimportable due to `ImportError`. The `verify evidence` CLI command (`runtime/system/evidence/cli/cli.py`) crashes at runtime every time.

2. **Shadowed module** (HIGH): `runtime/system/evidence/api.py` (187 lines) is dead code, shadowed by the `api/` package directory. Contains incompatible API definitions and calls non-existent `validate_inputs()` method.

3. **Collector interface violation** (CRITICAL): Base class `collect()` declares `-> List[EvidenceArtifact]` but 4 concrete collectors return single evidence objects. Any code using the base interface crashes with `TypeError: 'CoverageEvidence' object is not iterable`.

4. **Duplicate scripts** (LOW): `aggregate_evidence.py` and `run_aggregator.py` are identical. Only `aggregate_evidence.py` is used by the workflow.

5. **Missing `__init__.py` files** (LOW): `runtime/__init__.py` and `runtime/system/__init__.py` don't exist. Relies on Python 3 namespace packages. Works but inconsistent with packages that do have `__init__.py`.

6. **`VerificationSummary` phantom export** (HIGH): Listed in `models/__init__.py` `__all__` but never defined/imported. `from runtime.foundation.verification.models import VerificationSummary` → `ImportError`. `from ... import *` → `AttributeError`.

7. **Mutation matrix coupling** (BLOCKING): Plan outputs `affected_engines` as comma-separated unquoted strings (e.g., `cashflow,loan`). Workflow consumes via `fromJSON('[' + affected_engines + ']')` producing `[cashflow,loan]` — invalid JSON. Mutation testing never runs.

8. **Two `VerificationPlan` classes** (MEDIUM): Same name, different fields, different purposes. Risk of type errors and confusion.

9. **File-based vs directory-based engines** (HIGH): `extract_engine_name` strips `_engine` suffix. Workflow uses `src/engines/${{ matrix.engine }}_engine/` expecting a directory. File-based engines (`cashflow_engine.py`) would produce `src/engines/cashflow_engine/` which doesn't exist (it's a `.py` file).

---

## 4. Implementation Issues

### 4.1 Bugs

| File:Line | Issue | Severity |
|-----------|-------|----------|
| `model.py:143` | `dict[str, any]` — lowercase `any` (builtin function, not `Any`). With `from __future__ import annotations`, deferred but semantically wrong. | LOW |
| `plan_models.py:123` | `golden_paths.add("tests/")` for engine changes — golden tests run on engine changes but `run` is True with reason "No golden dependency" | MEDIUM |
| `plan_models.py:161` | `has_config_change`/`has_model_change` blocks add ALL non-test files as mutation targets via `_strip_backend(f)`, including generated artifacts | HIGH |
| `cli.py:449` | `python3 -m ruff check` — ruff not always available as module | LOW |
| `aggregator.py:75` | `mut = backend.get("mutation", {})` — empty fallback `{"overall": {...}}` causes attention loop to treat "overall" as engine name | LOW |
| `aggregator.py:132-133` | `from_artifact_directory` — `workspace_root = path.parent.parent if path.is_file() else path`. For a file, assumes 2-level-up structure. Fragile. | MEDIUM |
| `cli.py:528` | `gh run download --name evidence-summary` — artifact uploaded as `evidence-summary-${{ github.run_id }}`, exact match fails | MEDIUM |
| `pipeline.py:68,137,159,180` | `except Exception: pass` — swallows all errors silently during ingestion | LOW |
| `coverage.py:100` | `file_data.get("missing_lines", [])` — pytest-cov JSON key name may vary across coverage.py versions | LOW |
| `test_results.py:120` | `collect_artifacts` artifact path is `coverage.xml` — misleading (this is the test-results collector) | LOW |
| `registry.py:147` | `pass` statement after `except ValueError: pass` in `_register_scopes` | LOW |
| `cli.py:59` | `pass` statement in `cli()` click group function | LOW |
| `base.py:37,43,52` | `pass` statements in abstract property/method bodies | LOW |

### 4.2 Incomplete Logic

| File:Line | Issue | Severity |
|-----------|-------|----------|
| `planner.py:320-324` | `# TODO Program 7: implement graph-based capability resolution` with `...` ellipsis. `changed_endpoints` parameter accepted but ignored. | HIGH |
| `plan_models.py:171-172` | `has_test_change` adds `unit_paths.add("tests/unit/")` but does NOT add specific changed test file paths. Instead, ALL changed test files (including generated artifacts) are individually added via `_strip_backend(f)` at line 146. | HIGH |
| `aggregator.py:168` | `"delta_from_last": "0.0"` — hardcoded, never compares with previous CI run | LOW |
| `aggregator.py:206` | `verification_plan: str = "selective"` — hardcoded, never reflects actual plan | LOW |
| `plan_models.py` | `blast_radius` resolution loop iterates `blast_rank.items()` which in Python 3.7+ preserves insertion order: `{"low": 0, "medium": 1, "high": 2, "full": 3}`. The loop `for name, rank in blast_rank.items(): if max_blast_rank >= rank: blast_radius = name` would correctly produce the highest matching rank. Verified working. | None |
| `plan_models.py:185` | `plan_id` uses `datetime.now(timezone.utc).isoformat()` — not deterministic; same files at different times produce different plan_ids | LOW |

### 4.3 Incorrect Assumptions

| File | Assumption | Problem |
|------|-----------|---------|
| `plan_models.py` | All files under `backend/tests/` are test source files | Generated artifacts in `backend/tests/generated/` are treated as test changes |
| `plan_models.py` | All engines under `backend/src/engines/` are directories | File-based engines (`cashflow_engine.py`) exist; workflow's `src/engines/${{ matrix.engine }}_engine/` path fails |
| `api/__init__.py` | `collectors/__init__.py` exports all collectors | `PropertyTestCollector` and `ContractTestCollector` not exported → `ImportError` |
| `api/__init__.py` | `collect()` returns `List[EvidenceArtifact]` | 4 of 6 concrete collectors return single evidence objects → `TypeError` |
| `api.py` | Collectors have `validate_inputs()` method | No such method exists on any collector class |
| `cli.py:594` | `git diff --name-only HEAD~1 HEAD` works for all pushes | Fails on first commit of a repository or branch (no HEAD~1 ancestor) |
| `aggregator.py:216-226` | Evidence artifacts are organized in `evidence/coverage/` and `evidence/backend/tests/generated/` subdirectories | Actual workflow uploads use `actions/upload-artifact` with `merge-multiple: true`, placing artifacts at `evidence/backend/tests/generated/` — coverage search partially matches, mutation search fails (looks in `evidence/mutation/` first) |
| `aggregator.py:288-298` | Contract evidence is in `evidence/contract/` directory | Actual artifacts are in `evidence/backend/tests/generated/` — `evidence/contract/` doesn't exist, falls back to default collect which looks for `schemathesis-report.json` in wrong location |

### 4.4 Potential Runtime Failures

1. **`verify evidence`** — Always crashes: `ImportError` at `api/__init__.py:10` when importing `PropertyTestCollector`.
2. **`--plan` output includes non-test paths** — `unit_tests.paths` contains `tests/generated/*.json`, `tests/generated/*.md` — pytest will fail on these.
3. **Mutation matrix in CI** — `fromJSON('[cashflow,loan]')` is invalid JSON. Mutation testing job never runs.
4. **Contract tests in CI** — Runs unconditionally (no `if` condition); schemathesis output goes to `backend/schemathesis-report.json` but aggregator looks for `backend/tests/generated/schemathesis-report.json`.
5. **`collect_all_evidence()`** — Even if ImportError fixed: `TypeError: 'CoverageEvidence' object is not iterable` when calling `[asdict(a) for a in collected]`.
6. **`VerificationEvidence.__dict__`** — In dead-code `api.py:95-96`, `self.coverage.__dict__` on slotted dataclass raises `AttributeError`.
7. **`registry.load()`** — `import yaml` at module level. If PyYAML is not installed (undeclared in pyproject.toml), `ImportError` at import time.
8. **`plan_to_dict()` in CLI** — Called with rich `VerificationPlan` from `plan_verification()`. Accesses `plan.targets`, `plan.steps`, `plan.id`, `plan.scope`. The rich plan has these fields. But if accidentally called with the selective plan, it would crash with `AttributeError`.

---

## 5. Workflow Issues

| Issue | Description | Severity |
|-------|-------------|----------|
| **Mutation matrix invalid JSON** | `fromJSON('[' + needs.plan.outputs.affected_engines + ']')` produces `[cashflow,loan]` — invalid JSON (unquoted strings). Only `[]` (empty) parses successfully. Mutation job NEVER runs when engines are affected. | BLOCKING |
| **contract-tests missing `if`** | All other test jobs have `if: needs.plan.outputs.run_X == 'true'` but `contract-tests` (line 191) has no `if`. Runs unconditionally on every push/PR. | HIGH |
| **Schemathesis output path mismatch** | Workflow runs `python3 -m schemathesis run --output schemathesis-report.json` from `backend/` directory. Output at `backend/schemathesis-report.json`. But uploads `backend/tests/generated/` — the report is NOT in the uploaded artifacts. Aggregator can't find it. | HIGH |
| **Mutation path assumes directory** | `--paths-to-mutate src/engines/${{ matrix.engine }}_engine/` assumes engine is a directory. File-based engines (`cashflow_engine.py`) produce `src/engines/cashflow_engine/` which doesn't exist. | HIGH |
| **Evidence artifact name mismatch** | Workflow uploads artifact as `evidence-summary-${{ github.run_id }}`. CLI downloads with `--name evidence-summary` (exact match). Fallback uses `gh run download <run_id>` which downloads ALL artifacts. | MEDIUM |
| **unit-tests masks failures** | `2>&1 \|\| true` in pytest command makes step always succeed. `mutation` job's `needs.unit-tests.result == 'success'` check is always true, so mutation runs even when unit tests fail. | MEDIUM |
| **Duplicate aggregator scripts** | `aggregate_evidence.py` and `run_aggregator.py` are identical. Only `aggregate_evidence.py` is used by workflow. | LOW |
| **contract-tests unconditional** | Without `if: needs.plan.outputs.run_contract == 'true'`, contract tests run even when no routers changed, wasting CI resources. | MEDIUM |
| **No `if` on contract-tests for mutation dependency** | Mutmut path resolution requires directory-based engines only | HIGH |
| **Evident artifact upload path for contract** | `--path backend/tests/generated/` uploads entire directory, but schemathesis report is at `backend/` (not `backend/tests/generated/`) | HIGH |

### Detailed workflow step verification

| Step | Status | Notes |
|------|--------|-------|
| Triggers (push, PR, workflow_dispatch) | PASS | All three triggers configured |
| Concurrency group | PASS | `backend-verify-${{ github.ref }}` with `cancel-in-progress: true` |
| Job dependencies (plan → tests → evidence) | PASS | Correct dependency chain |
| Conditional execution | PARTIAL | `contract-tests` missing `if` condition |
| Outputs (12 plan outputs) | PASS | All map correctly to `to_github_outputs()` |
| Artifacts (upload/download) | PARTIAL | Schemathesis report in wrong location; contract evidence not uploaded |
| Python setup | PASS | Python 3.12 via `actions/setup-python@v5` |
| Git diff logic | PARTIAL | `git diff --name-only HEAD~1 HEAD` fails on first commit; PR mode uses `base_ref...HEAD` correctly |
| Matrix generation | FAIL | `fromJSON('[engine1,engine2]')` invalid JSON |
| PR commenting | PASS | Posts/updates comment with evidence summary markdown |
| Artifact download (evidence job) | PARTIAL | Downloads to `evidence/` with `merge-multiple: true` |

---

## 6. Production Readiness

| Subsystem | Architecture | Implementation | Robustness | Production | Avg (/10) |
|-----------|-------------|----------------|------------|------------|-----------|
| Impact Rules | 8 | 9 | 8 | 8 | **8.25** |
| Verification Plan | 7 | 8 | 6 | 7 | **7.00** |
| Coverage Collector | 6 | 6 | 8 | 5 | **6.25** |
| Mutation Collector | 6 | 6 | 8 | 5 | **6.25** |
| Test Result Collector | 6 | 6 | 8 | 5 | **6.25** |
| Contract Collector | 6 | 6 | 7 | 5 | **6.00** |
| Aggregator | 6 | 7 | 6 | 5 | **6.00** |
| Workflow | 6 | 7 | 4 | 3 | **5.00** |
| CLI | 6 | 7 | 5 | 4 | **5.50** |
| **Overall** | | | | | **6.25/10** |

---

## 7. Ready for Program 6?

**NO**

### Blocker-level issues (execution priority):

1. **Mutation matrix JSON is invalid** — `fromJSON('[cashflow,loan]')` produces invalid JSON for any non-zero number of affected engines. The plan outputs `affected_engines` as comma-separated unquoted strings. Fix: change `to_github_outputs()` to emit a JSON array, or change the workflow to `fromJSON(needs.plan.outputs.affected_engines)` after the plan emits JSON.

2. **Evidence API ImportError** — `api/__init__.py:10` imports `PropertyTestCollector` and `ContractTestCollector` from `collectors/__init__.py`, which doesn't export them. The `verify evidence` command and `collect_all_evidence()` are completely non-functional. Fix: add exports to `collectors/__init__.py` OR fix `api/__init__.py` to import from the correct module paths.

3. **Collector interface contract violation** — Base class `collect()` declares `-> List[EvidenceArtifact]` but 4 concrete collectors return single evidence objects. Any code using `collect()` polymorphically crashes with `TypeError`. Fix: either change return types to match base, or add a separate `collect_evidence()` method for the evidence-returning behavior.

4. **`contract-tests` job missing `if` condition** — Runs unconditionally. Fix: add `if: needs.plan.outputs.run_contract == 'true'`.

5. **Plan includes generated artifacts as test paths** — `backend/tests/generated/*.json` and `*.md` files are classified as test changes and added to `unit_tests.paths`. When pytest runs on these, it fails. Fix: exclude `tests/generated/` from `test_changed()` or `_strip_backend()`.

6. **Third-party dependencies in runtime** — `click` (declared in pyproject.toml but third-party) and `yaml`/PyYAML` (NOT declared in pyproject.toml despite being used at module level in `registry.py`). Phase 9 requires stdlib-only. Fix: remove `click` dependency or use `argparse`; remove `yaml` dependency or implement a minimal YAML parser / move to `json`.

7. **Schemathesis output path mismatch** — Workflow writes report to `backend/schemathesis-report.json` but uploads from `backend/tests/generated/` and aggregator expects `backend/tests/generated/schemathesis-report.json`. Fix: either change schemathesis `--output` path or change upload path.

8. **TODO + placeholder in `planner.py:320`** — `# TODO Program 7: implement graph-based capability resolution` with `...` ellipsis. Endpoint-based capability resolution is unimplemented. Fix: implement at least a minimal version or remove the TODO.

9. **File-based engine dir mismatch** — `extract_engine_name` returns "cashflow" for `cashflow_engine.py`, but the workflow's `--paths-to-mutate src/engines/cashflow_engine/` expects a directory (it's a `.py` file, not a directory). Fix: handle file-based vs directory-based engines in mutation target construction.

10. **`VerificationSummary` phantom export** — Listed in `models/__init__.py` `__all__` but never defined. Fix: either implement the class or remove from `__all__`.
