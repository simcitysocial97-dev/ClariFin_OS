# GitHub Actions Scripts

These scripts are called by workflow YAML files.

Keeping logic in scripts (not YAML) means:
- You can test them locally before pushing
- They are readable and maintainable
- You can run them manually for debugging

## Scripts

| Script | Purpose | Called By |
|--------|---------|-----------|
| `run_fast_checks.sh` | Fast lint + unit tests | quality.yml |
| `run_contract_tests.sh` | Contract test runner | backend.yml |
| `run_mutation_selective.sh` | Selective mutation | mutation.yml |
| `check_coverage_threshold.py` | Coverage gate | quality.yml, backend.yml |
| `generate_mutation_report.py` | Mutation report | mutation.yml |

## Running Locally

```bash
# Fast checks
bash .github/scripts/run_fast_checks.sh backend

# Contract tests  
bash .github/scripts/run_contract_tests.sh backend

# Check coverage (after running pytest with --cov)
python .github/scripts/check_coverage_threshold.py \
    --coverage-file backend/tests/generated/coverage.json \
    --phase 1
