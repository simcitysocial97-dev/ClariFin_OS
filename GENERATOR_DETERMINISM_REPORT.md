# Generator Determinism Report

## Summary

| Generator | Deterministic | Issue |
|-----------|---------------|-------|
| Contract Test Generator | **NO** | Timestamps in generated files |
| Verification Intelligence | **YES** (excluding timestamps) | `generated_at` field differs |
| Selective Verification | **YES** | No issues |
| CI Targets | **YES** | No issues |

---

## 1. Contract Test Generator

**File:** `backend/tools/generate_contract_tests.py`

### Determinism Test

```bash
cd backend && python tools/generate_contract_tests.py --all
git diff --stat tests/contract/generated/
```

**Result:** 21 files changed, 1182 insertions(+), 1534 deletions(-)

### Root Cause

The generator embeds `datetime.now().isoformat()` in each test file header:

```python
# Generated: 2026-07-25T16:41:44.408454
# Generated: 2026-07-28T09:26:05.725129  # <-- Changes every run
```

### Impact

1. **Git noise:** Every regeneration produces a diff even when API hasn't changed
2. **CI brittleness:** Jobs that regenerate and commit contract tests will have spurious changes
3. **Verification failure:** "git diff must be empty" checks fail for non-semantic changes

### Recommended Fix

Replace timestamp with deterministic content hash:

```python
import hashlib

def generate_timestamp() -> str:
    return datetime.now().isoformat()

def generate_content_hash(router_name: str, method: str, path: str) -> str:
    content = f"{router_name}:{method}:{path}"
    return hashlib.sha256(content.encode()).hexdigest()[:12]
```

Or remove timestamp entirely (preferred for generated files).

---

## 2. Verification Intelligence

**Files:**
- `backend/src/verification/intelligence/dependency_engine.py`
- `backend/src/verification/intelligence/selective_engine.py`
- `backend/src/verification/intelligence/coverage_engine.py`
- `backend/src/verification/intelligence/impact_engine.py`
- `backend/src/verification/intelligence/risk_engine.py`
- `backend/src/verification/intelligence/evidence_engine.py`
- `backend/src/verification/intelligence/report_engine.py`

### Determinism Test

```python
from verification.intelligence.dependency_engine import DependencyEngine
engine = DependencyEngine()
graph1 = engine.discover().to_dict()
graph2 = engine.discover().to_dict()
# Compare without generated_at
g1 = {k: v for k, v in graph1.items() if k != 'generated_at'}
g2 = {k: v for k, v in graph2.items() if k != 'generated_at'}
assert json.dumps(g1, sort_keys=True) == json.dumps(g2, sort_keys=True)
```

**Result:** PASS (excluding `generated_at` timestamp)

### Issue

`DependencyGraph` includes `generated_at` timestamp:

```python
class DependencyGraph:
    def __init__(self):
        self.edges = []
        self.capabilities = {}
        self.generated_at = datetime.now(UTC).isoformat()
```

### Impact

Low — timestamp is metadata only, not used for comparison in verification.

### Recommended Fix

Remove `generated_at` or make it optional/omitted from serialization.

---

## 3. Selective Verification

**File:** `backend/tools/selective_verify.py`

### Determinism Test

```python
from tools.selective_verify import build_selective_plan, load_change_report
report = load_change_report()
plan1 = build_selective_plan(report)
plan2 = build_selective_plan(report)
assert plan1.changed_files == plan2.changed_files
assert plan1.capability_tests == plan2.capability_tests
# ... all fields equal
```

**Result:** PASS

### Issue

None found.

---

## 4. CI Targets

**File:** `backend/tests/runtime/ci_targets.py`

### Determinism Test

```python
from tests.runtime.ci_targets import get_property_targets, get_contract_targets
assert get_property_targets() == get_property_targets()
assert get_contract_targets() == get_contract_targets()
```

**Result:** PASS

### Issue

None found.

---

## 5. Fix Priority

| Generator | Fix Priority | Effort |
|-----------|-------------|--------|
| Contract Test Generator | **High** | Low — remove timestamp from template |
| Verification Intelligence | **Low** | Low — remove/omit `generated_at` |
| Selective Verification | None | — |
| CI Targets | None | — |

---

## 6. Action Items

1. **[High] Fix contract generator template** — Remove `datetime.now().isoformat()` from Jinja2 template in `tools/generate_contract_tests.py`
2. **[Low] Fix DependencyGraph timestamp** — Remove or make optional `generated_at` in `dependency_engine.py`
3. **[Medium] Add determinism tests to CI** — Add a CI job that runs each generator twice and asserts `git diff` is empty
