# Validation Workflows

Developer guide for using the Validation Orchestrator Framework (VOF).

## Quick Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `--auto` | Auto-determine strategy | Daily coding, before every commit |
| `--fast` | Lint/type checks only | Quick pre-commit check |
| `--selective` | Targeted test verification | Before push, focused changes |
| `--full` | Full verification pipeline | Before merge, CI runs |
| `--coverage` | Coverage scan | Auditing capability maturity |
| `--plan` | Generate plan without running | Understanding impact |
| `--explain` | Decision tree explanation | Debugging strategy selection |

## Daily Coding

Run after every change to get immediate feedback:

```bash
python backend/tools/validation_orchestrator.py --auto
```

The orchestrator analyzes changed files and selects the appropriate validation strategy.

## Before Commit

Before committing, run selective verification to ensure your changes don't break affected tests:

```bash
python backend/tools/validation_orchestrator.py --selective
```

This runs only tests impacted by your changes.

## Before Merge

Run the full pipeline before merging to main:

```bash
python backend/tools/validation_orchestrator.py --full
```

Or use the shell wrapper:

```bash
./scripts/verify-local.sh
```

## Coverage Audit

Check capability maturity and detect orphan modules:

```bash
python backend/tools/validation_orchestrator.py --coverage --plan
```

## Understanding Decision Logic

### The Decision Tree

The orchestrator uses `risk-rules.yaml` to determine validation strategy:

```
Changed Files → Pattern Match → Risk Level → Strategy
```

### Strategy Selection

| Risk Level | Strategy | Stages |
|------------|----------|--------|
| LOW | fast | fast |
| MEDIUM | selective | fast, coverage, change_intelligence |
| HIGH | selective | fast, coverage, change_intelligence |
| CRITICAL | full | all stages |

### Pattern Examples

```yaml
# Documentation changes - minimal risk
- pattern: "**/*.md"
  strategy: fast
  risk: LOW

# Router/service changes - selective
- pattern: "backend/src/routers/**"
  strategy: selective
  risk: MEDIUM

# Engine/repository changes - selective (high risk)
- pattern: "backend/src/engines/**"
  strategy: selective
  risk: HIGH

# Model/schema changes - full
- pattern: "backend/src/models/**"
  strategy: full
  risk: CRITICAL
```

## Explain Mode

To understand why a particular strategy was chosen:

```bash
python backend/tools/validation_orchestrator.py --explain
```

Output example:

```
Changed files
  - backend/src/engines/cashflow_engine.py

Capability
  - household_cashflow

Risk
HIGH

Selected Strategy
SELECTIVE

Stages
  ✔ fast
  ✔ coverage
  ✔ change_intelligence

Skipped
  ✘ architecture
  ✘ capability
  ✘ property
  ✘ golden
  ✘ meta
```

## Machine-Readable Output

Use `--json` for CI/CD integration:

```bash
python backend/tools/validation_orchestrator.py --auto --json
```

Returns:
```json
{
  "strategy": "selective",
  "runtime_seconds": 45.2,
  "result": "PASS",
  "metrics": {
    "changed_files": ["backend/src/engines/cashflow_engine.py"],
    "stages": ["fast", "coverage", "change_intelligence"],
    ...
  }
}
```

## Artifacts

After each run, the following artifacts are generated:

| File | Purpose |
|------|---------|
| `validation-manifest.json` | Single-run metadata (strategy, files, stages) |
| `validation-metrics.json` | Per-stage timing and status |
| `validation-history.json` | History of last 200 runs |
| `validation-cache.json` | Cache in `.memory-cache/` for identical runs |

## Extending the Orchestrator

To add a new validation stage:

1. Create a class extending `ValidationStage`
2. Implement `stage_id`, `plan()`, and `execute()` methods
3. Register in `ValidationGraph._register_default_stages()`

Example:

```python
class PerformanceStage(ValidationStage):
    @property
    def stage_id(self) -> str:
        return "performance"

    def plan(self, manifest: ValidationManifest) -> None:
        manifest.commands_executed.append("pytest tests/performance")

    def execute(self) -> tuple[int, ValidationMetrics]:
        # Run performance tests
        ...
```

## Troubleshooting

### Unknown capability detected

If you see "Unknown capability detected - falling back to full verification", it means:
- A changed file is not tracked in any capability manifest
- Solution: Add the file to an appropriate capability in `memory-bank/capabilities/`

### Cache miss

The cache is invalidated when:
- Git SHA changes
- File list changes
- Manual cache deletion

To bypass cache: delete `.memory-cache/validation-cache.json`