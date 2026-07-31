# Implementation Plan: Verification Infrastructure Foundation

## Goal
Audit existing GitHub Actions infrastructure and implement safe infrastructure improvements (composite actions, standardized caches, artifacts, job summaries) plus create verification runtime folder.

---

## Phase 1: Create Composite Actions

### 1.1 setup-node-env Composite Action
**File:** `.github/actions/setup-node-env/action.yml`

```yaml
name: "Setup Node.js Environment"
description: "Installs Node.js, caches npm dependencies"
inputs:
  node-version:
    description: "Node.js version"
    required: false
    default: "20"
  working-directory:
    description: "Directory containing package.json"
    required: false
    default: "frontend"
  cache-key-suffix:
    description: "Additional cache key suffix"
    required: false
    default: ""
runs:
  using: "composite"
  steps:
    - name: Setup Node.js ${{ inputs.node-version }}
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'
        cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json
    - name: Configure npm
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: |
        npm config set fetch-retry-maxtimeout 120000
        npm config set fetch-retries 5
```

### 1.2 setup-playwright Composite Action
**File:** `.github/actions/setup-playwright/action.yml`

```yaml
name: "Setup Playwright"
description: "Installs Playwright browsers with caching"
inputs:
  working-directory:
    description: "Directory containing package.json"
    required: false
    default: "frontend"
  browsers:
    description: "Browsers to install"
    required: false
    default: "chromium"
runs:
  using: "composite"
  steps:
    - name: Cache Playwright browsers
      uses: actions/cache@v4
      with:
        path: ~/.cache/ms-playwright
        key: playwright-${{ runner.os }}-${{ hashFiles(format('{0}/package-lock.json', inputs.working-directory)) }}-${{ inputs.browsers }}
        restore-keys: |
          playwright-${{ runner.os }}-
    - name: Install Playwright browsers
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: npx playwright install --with-deps ${{ inputs.browsers }}
```

### 1.3 upload-test-artifacts Composite Action
**File:** `.github/actions/upload-test-artifacts/action.yml`

```yaml
name: "Upload Test Artifacts"
description: "Standardized artifact upload with retention"
inputs:
  name:
    description: "Artifact name prefix"
    required: true
  path:
    description: "Path to upload"
    required: true
  retention-days:
    description: "Retention in days"
    required: false
    default: "30"
  if-condition:
    description: "Condition for upload"
    required: false
    default: "always()"
runs:
  using: "composite"
  steps:
    - name: Upload ${{ inputs.name }}
      if: ${{ inputs.if-condition }}
      uses: actions/upload-artifact@v4
      with:
        name: ${{ inputs.name }}-${{ github.sha }}
        path: ${{ inputs.path }}
        retention-days: ${{ inputs.retention-days }}
```

### 1.4 job-summary Composite Action
**File:** `.github/actions/job-summary/action.yml`

```yaml
name: "Generate Job Summary"
description: "Creates standardized GitHub Job Summary"
inputs:
  title:
    description: "Summary title"
    required: true
  status:
    description: "Job status (success/failure/cancelled)"
    required: true
  details:
    description: "Additional markdown details"
    required: false
    default: ""
  artifacts:
    description: "Comma-separated artifact names to link"
    required: false
    default: ""
runs:
  using: "composite"
  steps:
    - name: Generate Job Summary
      shell: bash
      run: |
        cat >> $GITHUB_STEP_SUMMARY << 'EOF'
        # ${{ inputs.title }}
        
        **Status:** ${{ inputs.status }}
        
        **Workflow:** ${{ github.workflow }}
        **Run:** #${{ github.run_number }} (${{ github.run_id }})
        **Commit:** ${{ github.sha }}
        **Branch:** ${{ github.ref_name }}
        
        ${{ inputs.details }}
        
        ---
        *Generated at $(date -u +"%Y-%m-%d %H:%M:%S UTC")*
        EOF
```

---

## Phase 2: Update Workflows to Use Composite Actions

### 2.1 quality.yml - Update lint job
- Use `setup-python-env` (already used)
- Add `job-summary` at end of each job

### 2.2 backend.yml - All Python jobs
- Use `setup-python-env` (already used)
- Add `job-summary` at end of each job
- Add `upload-test-artifacts` for consistent uploads

### 2.3 frontend-build.yml
- Replace inline `setup-node` with `setup-node-env`
- Add `job-summary`

### 2.4 playwright.yml
- Replace inline `setup-node` + `setup-python` + browser install with `setup-node-env` + `setup-playwright`
- Add `job-summary`

### 2.5 mutation.yml
- Add `job-summary` to each job
- Use `upload-test-artifacts` for mutation results

### 2.6 golden.yml
- Add `job-summary` to each job
- Use `upload-test-artifacts`

### 2.7 nightly-property-tests.yml
- Replace inline setups with composite actions
- Add `job-summary`

### 2.8 ci.yml (retired)
- Add clear deprecation notice at top
- Keep for reference

### 2.9 full-validation.yml (retired)
- Add clear deprecation notice at top

---

## Phase 3: Create Verification Runtime Folder

### 3.1 verification/runtime/cli.py
```python
#!/usr/bin/env python3
"""Verification Runtime CLI - Entry point for verification orchestration."""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        prog="verification-runtime",
        description="ClariFin OS Verification Runtime"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # verify command
    verify_parser = subparsers.add_parser("verify", help="Run verification")
    verify_parser.add_argument("--config", type=Path, default=Path("verification.yaml"))
    verify_parser.add_argument("--target", choices=["backend", "frontend", "all"], default="all")
    
    # ci-targets command (delegates to existing backend/tests/runtime/ci_targets.py)
    ci_parser = subparsers.add_parser("ci-targets", help="Derive CI test targets")
    ci_parser.add_argument("--property", action="store_true")
    ci_parser.add_argument("--contract", action="store_true")
    ci_parser.add_argument("--capability", action="store_true")
    ci_parser.add_argument("--invariant", action="store_true")
    ci_parser.add_argument("--golden", action="store_true")
    ci_parser.add_argument("--mutation", action="store_true")
    ci_parser.add_argument("--all", action="store_true")
    ci_parser.add_argument("--json", action="store_true")
    
    # intelligence command
    intel_parser = subparsers.add_parser("intelligence", help="Run verification intelligence")
    intel_parser.add_argument("--selective", action="store_true")
    intel_parser.add_argument("--json", action="store_true")
    
    args = parser.parse_args()
    
    if args.command == "ci-targets":
        # Delegate to existing module
        sys.path.insert(0, str(Path("backend/tests/runtime")))
        from ci_targets import main as ci_targets_main
        sys.argv = ["ci_targets"] + [k for k, v in vars(args).items() if v and k != "command"]
        return ci_targets_main()
    
    elif args.command == "intelligence":
        # Delegate to existing module
        sys.path.insert(0, str(Path("backend/src/verification")))
        from verification_intelligence import main as intel_main
        return intel_main()
    
    elif args.command == "verify":
        print(f"Verification runtime - config: {args.config}, target: {args.target}")
        # Placeholder for Program 2
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### 3.2 verification/runtime/orchestrator.py
```python
"""Verification Runtime Orchestrator - Coordinates verification workflows."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VerificationConfig:
    """Configuration for verification runtime."""
    backend_enabled: bool = True
    frontend_enabled: bool = True
    e2e_enabled: bool = True
    mutation_enabled: bool = False
    golden_enabled: bool = False
    intelligence_enabled: bool = True
    
    # Thresholds
    coverage_threshold: int = 60
    mutation_threshold: int = 60
    
    # Paths
    config_path: Path = Path("verification.yaml")
    backend_path: Path = Path("backend")
    frontend_path: Path = Path("frontend")
    
    @classmethod
    def load(cls, path: Path) -> "VerificationConfig":
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            return cls(**data)
        return cls()


@dataclass
class VerificationResult:
    """Result of a verification run."""
    success: bool
    stage: str
    duration_seconds: float
    artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class VerificationOrchestrator:
    """Orchestrates the verification pipeline."""
    
    def __init__(self, config: VerificationConfig):
        self.config = config
        self.results: list[VerificationResult] = []
    
    def run_stage(self, name: str, cmd: list[str], cwd: Path | None = None) -> VerificationResult:
        """Run a verification stage and capture result."""
        import time
        start = time.time()
        cwd = cwd or Path.cwd()
        
        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, timeout=3600
            )
            success = result.returncode == 0
            errors = [result.stderr] if result.stderr and not success else []
        except subprocess.TimeoutExpired:
            success = False
            errors = ["Stage timed out after 1 hour"]
        except Exception as e:
            success = False
            errors = [str(e)]
        
        duration = time.time() - start
        vr = VerificationResult(success=success, stage=name, duration_seconds=duration, errors=errors)
        self.results.append(vr)
        return vr
    
    def run_verification(self) -> bool:
        """Run full verification pipeline."""
        all_success = True
        
        if self.config.backend_enabled:
            # Backend static analysis
            self.run_stage("backend-lint", ["ruff", "check", "."], self.config.backend_path)
            self.run_stage("backend-format", ["black", "--check", "."], self.config.backend_path)
            self.run_stage("backend-typecheck", ["mypy", "src/", "--ignore-missing-imports"], self.config.backend_path)
            
            # Backend tests
            self.run_stage("backend-unit-tests", [
                "pytest", "tests/unit/", "-x", "--timeout=30", "-q", "-n", "auto"
            ], self.config.backend_path)
            
            # Architecture tests
            self.run_stage("backend-architecture", [
                "pytest", "tests/architecture/", "--timeout=30", "-q"
            ], self.config.backend_path)
        
        if self.config.frontend_enabled:
            # Frontend static analysis
            self.run_stage("frontend-typecheck", ["npx", "tsc", "--noEmit"], self.config.frontend_path)
            self.run_stage("frontend-lint", ["npm", "run", "lint"], self.config.frontend_path)
            self.run_stage("frontend-build", ["npm", "run", "build"], self.config.frontend_path)
        
        if self.config.e2e_enabled:
            self.run_stage("e2e-tests", ["npx", "playwright", "test"], self.config.frontend_path)
        
        # Print summary
        print("\n=== VERIFICATION SUMMARY ===")
        for r in self.results:
            status = "✅ PASS" if r.success else "❌ FAIL"
            print(f"  {status} | {r.stage:25s} | {r.duration_seconds:.1f}s")
            if r.errors:
                for e in r.errors:
                    print(f"    ERROR: {e[:200]}")
            all_success = all_success and r.success
        
        return all_success


def main():
    config = VerificationConfig.load(Path("verification.yaml"))
    orchestrator = VerificationOrchestrator(config)
    success = orchestrator.run_verification()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
```

### 3.3 verification/verification.yaml (Placeholder)
```yaml
# Verification Runtime Configuration
# This file will be expanded in Program 2 (Evidence Runtime)

backend_enabled: true
frontend_enabled: true
e2e_enabled: true
mutation_enabled: false
golden_enabled: false
intelligence_enabled: true

# Coverage thresholds (Phase 1)
coverage_threshold: 60
mutation_threshold: 60

# Paths
backend_path: "backend"
frontend_path: "frontend"

# Intelligence settings
intelligence:
  selective_mode: true
  risk_threshold: "high"
  cache_ttl_hours: 24

# Artifact settings
artifacts:
  retention_days: 30
  upload_coverage: true
  upload_mutation: true
  upload_e2e_report: true

# Notification settings
notifications:
  pr_comment: true
  commit_status: true
  slack_webhook: ""  # Optional
```

---

## Phase 4: Validation

### 4.1 Syntax Validation
- YAML lint all workflow files
- Python syntax check on new .py files
- Composite action YAML validation

### 4.2 Workflow Trigger Test
- Create test branch
- Push to trigger workflows
- Verify all workflows complete successfully

### 4.3 Composite Action Test
- Verify each composite action works in isolation
- Check cache keys are valid
- Verify artifact uploads work

---

## Files to Create (7)

| File | Phase |
|------|-------|
| `.github/actions/setup-node-env/action.yml` | 1 |
| `.github/actions/setup-playwright/action.yml` | 1 |
| `.github/actions/upload-test-artifacts/action.yml` | 1 |
| `.github/actions/job-summary/action.yml` | 1 |
| `verification/runtime/cli.py` | 3 |
| `verification/runtime/orchestrator.py` | 3 |
| `verification/verification.yaml` | 3 |

## Files to Modify (10)

| File | Changes |
|------|---------|
| `.github/workflows/quality.yml` | Add job summaries, verify composite action usage |
| `.github/workflows/backend.yml` | Add job summaries, use upload-test-artifacts |
| `.github/workflows/frontend-build.yml` | Use setup-node-env, add job summary |
| `.github/workflows/playwright.yml` | Use setup-node-env + setup-playwright, add job summary |
| `.github/workflows/mutation.yml` | Add job summaries, use upload-test-artifacts |
| `.github/workflows/golden.yml` | Add job summaries, use upload-test-artifacts |
| `.github/workflows/nightly-property-tests.yml` | Use composite actions, add job summaries |
| `.github/workflows/ci.yml` | Add deprecation notice |
| `.github/workflows/full-validation.yml` | Add deprecation notice |
| `.github/workflows/frontend.yml` | Add job summary |

---

## Risk Mitigation

1. **Test composite actions in isolation** before integrating
2. **Keep original workflows as backup** during transition
3. **Use `workflow_dispatch`** to test manually before enabling triggers
4. **Monitor cache hit rates** after cache key changes
5. **Verify artifact paths** match existing expectations

---

## Success Criteria

- [ ] All 4 composite actions created and valid YAML
- [ ] All 10 workflows updated to use composite actions where applicable
- [ ] All workflows have GitHub Job Summaries
- [ ] Verification runtime folder created with 3 files
- [ ] Existing CI triggers unchanged
- [ ] No test behavior modifications
- [ ] Manual workflow_dispatch tests pass

---

## Next Steps (Program 2)

After this foundation is in place:
1. Implement Evidence Runtime (verification.yaml config-driven)
2. Add selective test execution based on intelligence layer
3. Implement artifact provenance tracking
4. Add GitHub App integration for PR comments