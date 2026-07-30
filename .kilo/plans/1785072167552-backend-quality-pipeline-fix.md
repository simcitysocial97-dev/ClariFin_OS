# Backend Quality Validation Pipeline Fix Plan

## Canonical Test Namespace Convention

Establish one convention and apply it everywhere:

```
backend/tests/
├── capability/       # singular — keep (matches current directory)
├── properties/       # plural — rename from property/
└── invariants/       # plural — rename from invariant/
```

Rationale: domain registry keys already use plural semantics (`property_tests`, `invariants`), and generated artifacts/tools already reference the plural forms. Normalizing to these names eliminates drift instead of adding more aliases.

## Current State

| Stage | Current State | Problem |
|-------|--------------|---------|
| pytest + pytest-cov | Outputs raw `coverage.json` | Raw output lacks `capabilities` section |
| `tools/check_coverage.py` | Crashes with `NameError` | `CAPABILITIES_DIR` undefined on line 349 |
| `tests/meta/test_coverage_integrity.py` | Fails | `coverage.json` missing `capabilities` |
| `tests/invariant/test_*.py` (4 files) | ImportError | `sys.path` points to `src/`; imports `invariant.*` package |
| `tests/property/` | Directory singular | Tools/generated artifacts expect `tests/properties/` |
| `tests/invariant/` | Directory singular | Tools/generated artifacts expect `tests/invariants/` |
| Multiple tools | Use `tests/capabilities/` | Actual directory is `tests/capability/` |
| `test_selective_verify.py` | Fails | Test data uses `tests/capabilities/` (wrong) |

## Required Changes

Execute in this exact order. Rename first so tools cannot regenerate old paths mid-migration.

### 1. Normalize test namespace conventions (do first)

**1a. Rename directories**
```bash
cd backend/tests
mv invariant invariants
mv property properties
```

**1b. Update package imports**
Files importing from the renamed packages:
- `backend/tests/invariants/test_account.py`: `from invariant.account import *` → `from invariants.account import *`
- `backend/tests/invariants/test_credit.py`: `from invariant.credit import *` → `from invariants.credit import *`
- `backend/tests/invariants/test_statement.py`: `from invariant.statement import *` → `from invariants.statement import *`
- `backend/tests/invariants/test_transaction.py`: `from invariant.transaction import *` → `from invariants.transaction import *`

**1c. Update tool references (tests/capabilities/ → tests/capability/)**
Tools that wrongly use plural `tests/capabilities/`:
- `backend/tools/validation_audit.py`
- `backend/tools/mutation_discovery.py`
- `backend/tools/test_strength.py`
- `backend/tools/change_intelligence.py`
- `backend/tools/validation_orchestrator.py`
- `backend/tests/meta/test_selective_verify.py`

Replace all occurrences of `tests/capabilities/` with `tests/capability/` in these files.

**1d. Generated artifacts**
Do not manually edit `backend/tests/generated/*`. These are output artifacts. After all source fixes are complete, run `python tools/check_coverage.py` to regenerate them with correct paths.

### 2. Fix test discovery reliability

Remove all `sys.path.insert(0, ...)` workarounds from test files and add `tests` to pytest's `pythonpath` in `pyproject.toml`.

**2a. Update `pyproject.toml`**
```toml
[tool.pytest.ini_options]
pythonpath = ["src", "tests"]
```

**2b. Remove `sys.path.insert` blocks**
Files containing `sys.path.insert` that must be cleaned:
- `backend/tests/conftest.py`
- `backend/tests/property/conftest.py`
- `backend/tests/capability/conftest.py`
- `backend/tests/architecture/test_boundary.py`
- `backend/tests/integration/e2e/test_statement_upload_pipeline.py`
- `backend/tests/capability/*/test_capability.py` (all capability tests)
- `backend/tests/properties/*/test_engine_properties.py` (all property tests)
- `backend/tests/unit/engines/*/test_*.py` (unit engine tests with path hacks)
- `backend/tests/unit/repositories/test_*.py` (unit repo tests with path hacks)
- `backend/tests/unit/services/test_*.py` (unit service tests with path hacks)
- `backend/tests/invariants/test_determinism.py`
- `backend/tests/invariants/test_reconciliation_determinism.py`
- `backend/tests/meta/test_validation_orchestrator.py`
- `backend/tests/meta/test_contract_registry.py`
- `backend/tests/audits/test_audit_minimal.py`
- `backend/tests/migrations/test_migration_*.py`
- `backend/tests/contract/schema_providers.py`
- `backend/tests/contract/schema_validators.py`

For each file: delete the `sys.path.insert(0, ...)` line and the now-unused `import sys` / `from pathlib import Path` if they become unused.

### 3. Fix `backend/tools/check_coverage.py`

**3a. Fix `generate_capability_registry()` undefined variable**
Replace the function body to read from `CAPABILITY_REGISTRY`:
```python
def generate_capability_registry(
    capabilities: list[CapabilityCoverage],
) -> dict[str, Any]:
    if not CAPABILITY_REGISTRY.exists():
        return {"capabilities": []}
    with open(CAPABILITY_REGISTRY) as f:
        return yaml.safe_load(f) or {"capabilities": []}
```

**3b. Enrich `coverage.json` with raw pytest-cov data**
Update `main()` to merge raw coverage with capability metadata. Add a guard so the failure mode is clear if pytest-cov was not run first:
```python
raw_path = GENERATED_DIR / "raw-coverage.json"
if not raw_path.exists():
    raise FileNotFoundError(
        "raw-coverage.json missing. Run pytest with --cov-report=json first."
    )
with open(raw_path) as f:
    raw_coverage = json.load(f)

coverage_json = {
    "generated_at": str(os.popen("date -Iseconds").read().strip()),
    "capabilities": [
        {
            "id": cap.id,
            "name": cap.name,
            "criticality": cap.criticality,
            "risk": cap.risk,
            "structural_maturity": cap.structural_maturity,
            "validation_maturity": cap.validation_maturity,
            "documentation_maturity": cap.documentation_maturity,
            "overall_maturity": cap.overall_maturity,
            "missing": [
                item.path
                for item in (cap.routers + cap.services + cap.engines +
                             cap.repositories + cap.tables + cap.golden_datasets +
                             cap.property_tests + cap.invariants)
                if not item.exists
            ],
        }
        for cap in capabilities
    ],
    "files": raw_coverage.get("files", {}),
    "totals": raw_coverage.get("totals", {}),
}
```

### 4. Fix `backend/tests/meta/test_selective_verify.py` test data

Update `test_duplicate_removal` test data to use canonical paths:
```python
"capability_tests": ["tests/capability/household_cashflow", "tests/capability/household_cashflow"],
"property_tests": ["tests/properties/cashflow", "tests/properties/cashflow"],
"golden_tests": ["normal_household", "normal_household"],
"invariants": ["tests/invariants/test_cashflow.py", "tests/invariants/test_cashflow.py"],
```

### 5. Update `.github/workflows/quality.yml`

Change the unit-tests job to produce `raw-coverage.json`, then enrich it:

```yaml
- name: Run unit tests with coverage
  working-directory: backend
  run: |
    pytest tests/unit/ \
      -x \
      --timeout=30 \
      --tb=short \
      -v \
      --no-header \
      -n auto \
      --cov=. \
      --cov-report=json:tests/generated/raw-coverage.json \
      --cov-report=xml:tests/generated/coverage.xml \
      --cov-report=term-missing \
      --cov-config=.coveragerc \
      -q

- name: Enrich coverage with capabilities
  working-directory: backend
  run: |
    python tools/check_coverage.py

- name: Check coverage threshold
  working-directory: backend
  run: |
    python ../.github/scripts/check_coverage_threshold.py \
      --coverage-file tests/generated/coverage.json \
      --phase 1
```

### 6. Acceptance test for coverage schema

Add a quick validation after `check_coverage.py` runs:
```bash
python - <<'PY'
import json
with open("tests/generated/coverage.json") as f:
    d = json.load(f)
assert "capabilities" in d, "missing capabilities"
assert "files" in d, "missing files"
assert "totals" in d, "missing totals"
print("coverage schema OK")
PY
```

## Validation Steps

Run from `backend/` directory after all changes:

```bash
# 0. Clear caches so pytest does not use stale collection info
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
rm -rf .pytest_cache

# 1. Regenerate enriched coverage (do not edit generated files manually)
python tools/check_coverage.py

# 2. Acceptance test
python - <<'PY'
import json
with open("tests/generated/coverage.json") as f:
    d = json.load(f)
assert "capabilities" in d, "missing capabilities"
assert "files" in d, "missing files"
assert "totals" in d, "missing totals"
print("coverage schema OK")
PY

# 3. Run all key test suites
pytest tests/unit/ -q
pytest tests/invariants/ -q
pytest tests/properties/ -q
pytest tests/architecture/ -q
pytest tests/meta/ -q

# 4. Check coverage threshold
python ../.github/scripts/check_coverage_threshold.py --coverage-file tests/generated/coverage.json

# 5. Migration grep gate — must produce no output
grep -R "tests/invariant/" -n . --include="*.py" --include="*.yaml" --include="*.yml" --include="*.md" --include="*.json" --exclude-dir=__pycache__
grep -R "tests/property/" -n . --include="*.py" --include="*.yaml" --include="*.yml" --include="*.md" --include="*.json" --exclude-dir=__pycache__
grep -R "tests/capabilities/" -n . --include="*.py" --include="*.yaml" --include="*.yml" --include="*.md" --include="*.json" --exclude-dir=__pycache__
grep -R "from invariant\." -n tests --include="*.py" --exclude-dir=__pycache__
grep -R "from property\." -n tests --include="*.py" --exclude-dir=__pycache__
```

Expected: all commands pass, grep gates produce no output.

## Final Execution Sequence

Equivalent of `.github/workflows/quality.yml` that must pass from a clean checkout:

```bash
cd backend

# Clean state
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
rm -rf .pytest_cache

# Unit tests with coverage
pytest tests/unit/ -q \
  --cov=. \
  --cov-report=json:tests/generated/raw-coverage.json \
  --cov-report=xml:tests/generated/coverage.xml \
  --cov-report=term-missing \
  --cov-config=.coveragerc

# Enrich coverage
python tools/check_coverage.py

# Schema guard
python - <<'PY'
import json
with open("tests/generated/coverage.json") as f:
    d = json.load(f)
assert "capabilities" in d
assert "files" in d
assert "totals" in d
print("coverage schema OK")
PY

# Threshold check
python ../.github/scripts/check_coverage_threshold.py \
  --coverage-file tests/generated/coverage.json

# Architecture + meta
pytest tests/architecture/ -q
pytest tests/meta/ -q
```

## Files Modified

| File | Change |
|------|--------|
| `backend/tests/invariant/` → `backend/tests/invariants/` | Directory rename |
| `backend/tests/property/` → `backend/tests/properties/` | Directory rename |
| `backend/tests/invariants/test_account.py` | Import path + remove sys.path.insert |
| `backend/tests/invariants/test_credit.py` | Import path + remove sys.path.insert |
| `backend/tests/invariants/test_statement.py` | Import path + remove sys.path.insert |
| `backend/tests/invariants/test_transaction.py` | Import path + remove sys.path.insert |
| `backend/tests/invariants/test_determinism.py` | Remove sys.path.insert |
| `backend/tests/invariants/test_reconciliation_determinism.py` | Remove sys.path.insert |
| `backend/tests/property/conftest.py` | Remove sys.path.insert |
| `backend/tests/capability/conftest.py` | Remove sys.path.insert |
| `backend/tests/conftest.py` | Remove sys.path.insert |
| `backend/tests/architecture/test_boundary.py` | Remove sys.path.insert |
| `backend/tests/integration/e2e/test_statement_upload_pipeline.py` | Remove sys.path.insert |
| `backend/tests/capability/*/test_capability.py` (all) | Remove sys.path.insert |
| `backend/tests/property/*/test_engine_properties.py` (all) | Remove sys.path.insert |
| `backend/tests/unit/engines/*/test_*.py` | Remove sys.path.insert |
| `backend/tests/unit/repositories/test_*.py` | Remove sys.path.insert |
| `backend/tests/unit/services/test_*.py` | Remove sys.path.insert |
| `backend/tests/meta/test_validation_orchestrator.py` | Remove sys.path.insert |
| `backend/tests/meta/test_contract_registry.py` | Remove sys.path.insert |
| `backend/tests/audits/test_audit_minimal.py` | Remove sys.path.insert |
| `backend/tests/migrations/test_migration_*.py` | Remove sys.path.insert |
| `backend/tests/contract/schema_providers.py` | Remove sys.path.insert |
| `backend/tests/contract/schema_validators.py` | Remove sys.path.insert |
| `backend/tools/check_coverage.py` | Fix CAPABILITIES_DIR + merge raw coverage |
| `backend/tools/selective_verify.py` | (no change needed — already uses singular `tests/capability/`) |
| `backend/tools/change_intelligence.py` | Fix `tests/capabilities/` → `tests/capability/` |
| `backend/tools/validation_audit.py` | Fix `tests/capabilities/` → `tests/capability/` |
| `backend/tools/mutation_discovery.py` | Fix `tests/capabilities/` → `tests/capability/` |
| `backend/tools/test_strength.py` | Fix `tests/capabilities/` → `tests/capability/` |
| `backend/tools/validation_orchestrator.py` | Fix `tests/capabilities/` → `tests/capability/` |
| `backend/tests/meta/test_selective_verify.py` | Fix test data paths |
| `backend/tests/generated/*` | Regenerated by `tools/check_coverage.py` — do not edit manually |
| `backend/pyproject.toml` | Add `tests` to `pythonpath` |
| `.github/workflows/quality.yml` | Add raw-coverage.json + check_coverage.py step |

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Directory rename breaks imports in non-test code | Low | Only test directories renamed; production `src/` unchanged |
| `sys.path.insert` removal reveals hidden import assumptions | Medium | Adding `tests` to `pythonpath` covers all cases |
| Tool references to `tests/capabilities/` missed | Medium | Use grep count validation step to confirm 0 matches |
| `capability-registry.yaml` has other path inconsistencies | Medium | `test_all_capability_references_exist` catches remaining issues |
| Coverage schema regression | Low | Acceptance test asserts required keys exist |
