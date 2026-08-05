# GitHub Actions Architecture

Generated: 2026-08-05

## Overview

This document describes the consolidated CI/CD architecture for the ClariFin OS Engineering Platform.

## Workflow Responsibilities

### backend-verify.yml
**Purpose:** Backend verification via the autonomous runtime orchestrator.

**Triggers:**
- Push to any branch (paths: `backend/**`)
- Pull request to main/develop (paths: `backend/**`)
- Manual dispatch

**Jobs:**
- `verify` - Runs `python runtime/verify.py backend` profile

**Artifacts:**
- `cross-layer-map` - Shared architecture map
- `verification-report` - Markdown verification report
- `verification-cache` - Cache for intelligent verification
- `evidence-backend-{run_id}` - Execution evidence

### frontend-verify.yml
**Purpose:** Frontend verification via the autonomous runtime orchestrator.

**Triggers:**
- Push to any branch (paths: `frontend/**`, `backend/src/routers/**`, `backend/src/mappers/**`)
- Pull request to main/develop (paths: `frontend/**`, `backend/src/routers/**`, `backend/src/mappers/**`)
- Manual dispatch

**Jobs:**
- `verify` - Runs `python runtime/verify.py frontend` profile

**Artifacts:**
- `cross-layer-map` - Shared architecture map
- `verification-report` - Markdown verification report
- `verification-cache` - Cache for intelligent verification

### verification-runtime.yml
**Purpose:** Runtime self-validation (Programs 7-11 validation).

**Triggers:**
- Push to any branch (paths: `runtime/**`, `backend/src/engines/**`, `backend/src/routers/**`, `backend/src/mappers/**`)
- Pull request to main/develop (same paths)
- Manual dispatch

**Jobs:**
- `verify-runtime` - Runs runtime tests and verification profiles

**Artifacts:**
- `verification-quality` - Quality report
- `verification-performance` - Performance metrics
- `observability-artifacts` - Engineering events and analytics

### quality.yml
**Purpose:** Fast quality gate running on every push.

**Triggers:**
- Push to any branch
- Pull request to main/develop

**Jobs:**
- `lint` - Ruff, Black, import sort
- `unit-tests` - Unit tests with coverage
- `architecture` - Architecture boundary tests
- `meta` - Registry tests
- `intelligence-quality` - Selective verification analysis
- `quality-gate` - Summary gate

**Artifacts:**
- `coverage-unit-{sha}` - Coverage reports

### golden.yml
**Purpose:** Nightly golden dataset regression tests.

**Triggers:**
- Schedule: Daily at 3 AM UTC
- Manual dispatch

**Jobs:**
- `golden` - Golden regression tests
- `regression` - Regression comparison

**Artifacts:**
- `golden-results-{run_id}` - Regression test results

### mutation.yml
**Purpose:** Nightly mutation testing for test effectiveness.

**Triggers:**
- Schedule: Daily at 2 AM UTC
- Manual dispatch

**Jobs:**
- `discover` - Discover mutation targets
- `mutation` - Run mutation testing per-engine
- `report` - Aggregate mutation report

**Artifacts:**
- `mutation-{engine}-{run_id}` - Per-engine mutation logs
- `mutation-report-{run_id}` - Aggregated report

### playwright.yml
**Purpose:** End-to-end browser tests.

**Triggers:**
- Push to main, master, develop
- Pull request to main, master, develop
- Manual dispatch

**Jobs:**
- `test` - Playwright E2E tests

**Artifacts:**
- `playwright-report` - HTML test report
- `test-results` - Raw test results

### release.yml
**Purpose:** Future releases only.

**Triggers:**
- Release published
- Manual dispatch

**Jobs:**
- `build` - Build and package release

**Artifacts:**
- `frontend-dist-{version}` - Frontend distribution
- `release-notes` - Release documentation

### dependency-update.yml
**Purpose:** Scheduled dependency maintenance.

**Triggers:**
- Schedule: Every Monday at 4 AM UTC
- Manual dispatch

**Jobs:**
- `update-backend` - Python dependency checks
- `update-frontend` - npm dependency checks
- `generate-report` - Summary report

**Artifacts:**
- `python-dependencies` - Python dependency reports
- `npm-dependencies` - npm dependency reports
- `dependency-health` - Health summary

## Artifact Flow

The canonical artifact pipeline:

```
Cross-layer map
       ↓
Verification Planner
       ↓
Verification Runtime
       ↓
Evidence
       ↓
Observability
       ↓
Knowledge Index
       ↓
Engineering Reports
```

Each workflow generates its required artifacts independently for maximum resilience.

## Triggers

| Workflow | Push | Pull Request | Schedule | Manual |
|----------|------|--------------|----------|--------|
| backend-verify.yml | ✅ (backend/**) | ✅ (main/develop) | - | ✅ |
| frontend-verify.yml | ✅ (frontend/**) | ✅ (main/develop) | - | ✅ |
| verification-runtime.yml | ✅ (runtime/**) | ✅ (main/develop) | - | ✅ |
| quality.yml | ✅ (all) | ✅ (main/develop) | - | - |
| golden.yml | - | - | ✅ (daily) | ✅ |
| mutation.yml | - | - | ✅ (daily) | ✅ |
| playwright.yml | ✅ (main/master/develop) | ✅ (main/master/develop) | - | ✅ |
| release.yml | - | - | - | ✅ |
| dependency-update.yml | - | - | ✅ (weekly) | ✅ |

## Branch Strategy

- **main** - Production branch (protected)
- **develop** - Integration branch (protected)
- **feature/** - Feature branches
- **release/** - Release preparation branches

Branch protection rules should require:
- `quality-gate` success
- `backend-verify.yml` success (for backend changes)
- `frontend-verify.yml` success (for frontend changes)

## Engineering Runtime Integration

Verification workflows integrate with the Engineering Platform Runtime:

1. **Verification Orchestrator** - Manages verification plans
2. **Evidence Aggregator** - Collects verification results
3. **Observability Layer** - Publishes to engineering-event-bus
4. **Knowledge Index** - Enables impact analysis
5. **Analytics Engine** - Provides metrics and health reports

## Naming Conventions

### Job Names
- Lowercase with hyphens: `verify`, `test`, `lint`, `golden`
- Contextual: `verify-runtime`, `update-backend`

### Step Names
- Capital case: `Checkout code`, `Setup Python`, `Run tests`
- Action descriptions: `Upload cross-layer map`, `Job Summary`

### Artifact Names
- Dash-separated: `cross-layer-map`, `verification-report`, `mutation-report-{run_id}`
- Unique per run: Include `${{ github.run_id }}` for run-specific artifacts

### Concurrency Groups
- `${{ github.workflow }}-${{ github.ref }}` pattern
- Allows cancelling in-progress on same ref

## Configuration

All workflows use:
- `actions/checkout@v4` with `fetch-depth: 0`
- `actions/upload-artifact@v4`
- `retention-days: 30` for most artifacts (90 for mutation/golden)
- Standard Python 3.12 environment

Reusable actions in `.github/actions/`:
- `setup-python-env` - Python environment setup
- `setup-node-env` - Node.js environment setup
- `setup-playwright` - Playwright browser setup
- `upload-test-artifacts` - Test artifact upload
- `job-summary` - Summary generation