# Change Confidence Pipeline — ClariFin_OS

> **Staged Validation Approach** — Choose verification level based on change impact.

---

## Overview

The Change Confidence Pipeline provides three verification levels, reusing existing validation tooling:

| Level | Name | When to Use | Validation Scope |
|-------|------|-------------|------------------|
| A | Current Files | Docs, config, non-code changes | Fast: ruff + mypy (backend only) |
| B | Affected Capability | Engine changes, API modifications | Selective: impacted capability tests |
| C | Full Validation | Schema changes, layer boundaries | Full: all test suites + all stages |

---

## Level A: Current Files

### Trigger
- Documentation changes (`.md`, `.txt`)
- Configuration updates (`.json`, `.yaml`, `.toml`)
- Non-executable files

### Commands
```bash
# Backend only (no source changes)
cd backend && ./venv/bin/python3 -m ruff check . && ./venv/bin/python3 -m mypy .
```

### Tool Used
- **Validation Orchestrator**: `scripts/verify-fast.sh` (delegates to `./venv/bin/python3 -m ruff check . && mypy .`)

---

## Level B: Affected Capability

### Trigger
- Changes to engines, services, repositories
- API endpoint modifications
- Test file updates

### Commands
```bash
# Run selective verification
VERIFY_MODE=selective ./scripts/verify-local.sh
```

### Tool Chain
1. **Change Intelligence Framework (CIF)**: `backend/tools/change_intelligence.py`
   - Analyzes git diff for changed files
   - Maps files to capabilities via `capability-registry.yaml`
   - Computes risk levels (LOW/MEDIUM/HIGH/CRITICAL)

2. **Selective Verification Framework (SVF)**: `backend/tools/selective_verify.py`
   - Receives capability list from CIF
   - Runs only affected capability tests
   - Generates change report in `memory-bank/generated/change-report.json`

3. **Validation Orchestrator (VOF)**: Reuses stages
   - Fast stage (ruff + mypy)
   - Change intelligence stage
   - Mutation readiness stage
   - Affected capability tests

---

## Level C: Full Validation

### Trigger
- Database schema migrations
- New layer files (router, service, engine, repository)
- Financial invariant changes
- Any change affecting multiple capabilities

### Commands
```bash
# Full verification
./scripts/verify-local.sh
# Or: VERIFY_MODE=full ./scripts/verify-local.sh
```

### Tool Chain
1. **Validation Orchestrator (VOF)**: Full pipeline
   - fast → coverage → change_intelligence → mutation_readiness → architecture → capability → property → golden → contract → meta

2. **All Test Suites**:
   - `pytest tests/architecture/` - Architecture validation
   - `pytest tests/capabilities/` - Business capability smoke tests
   - `pytest tests/contracts/` - API/OpenAPI validation
   - `pytest tests/properties/` - Property-based tests
   - `pytest tests/golden/` - Golden master tests
   - `pytest tests/meta/` - Meta tests

---

## Tool Reuse Matrix

| Functionality | Tool | Path |
|--------------|------|------|
| Linting | ruff | Built-in |
| Type checking | mypy | Built-in |
| Coverage check | check_coverage.py | `backend/tools/check_coverage.py` |
| Change analysis | change_intelligence.py | `backend/tools/change_intelligence.py` |
| Selective verification | selective_verify.py | `backend/tools/selective_verify.py` |
| Test strength analysis | test_strength.py | `backend/tools/test_strength.py` |
| Mutation discovery | mutation_discovery.py | `backend/tools/mutation_discovery.py` |
| Full orchestration | validation_orchestrator.py | `backend/tools/validation_orchestrator.py` |

---

## Risk Classification Rules

From `change_intelligence.py`:

| Path Pattern | Risk Level | Confidence |
|-------------|------------|------------|
| `.md`, `.txt`, `.rst` | LOW | HIGH |
| `/routers/` | MEDIUM | HIGH |
| `/services/` | MEDIUM | HIGH |
| `/repositories/` | HIGH | HIGH |
| `/engines/cashflow`, `loan`, `credit_card`, `behaviour` | CRITICAL | HIGH |
| Other `/engines/` | HIGH | MEDIUM |
| Schema, migrations | HIGH | HIGH |
| Unknown | LOW | LOW |

---

## Confidence Scoring

### Risk Weight Mapping
- LOW = 1
- MEDIUM = 2
- HIGH = 4
- CRITICAL = 8

### Confidence Levels
- LOW: Uncertain impact, needs manual review
- MEDIUM: Some ambiguity in capability mapping
- HIGH: Confident in impact assessment

---

## Workflow Example

```bash
# 1. Make changes to a file
# 2. Run change detection
cd backend && ./venv/bin/python3 tools/change_intelligence.py

# 3. Review generated change-report.json
# 4. Run appropriate verification level
VERIFY_MODE=selective ./scripts/verify-local.sh

# 5. Check results
cat memory-bank/generated/validation-manifest.json
```

---

## No Duplication Policy

This pipeline **REUSES** existing tooling:

- ✅ Uses `validation_orchestrator.py` for all stages
- ✅ Uses `change_intelligence.py` for file analysis
- ✅ Uses `selective_verify.py` for selective testing
- ✅ Uses `scripts/verify-local.sh` wrapper
- ❌ Does NOT duplicate FVF (Fast Verification Framework)
- ❌ Does NOT replace existing VOF stages

---

*Version: 1.0 (Stage 0)*  
*Validates changes through existing tooling chain.*