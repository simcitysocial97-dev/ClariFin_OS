# Toolchain Verification Policy Classification

## Tool Classification

| Tool | Classification | Profile(s) | Gate Type | Notes |
|------|----------------|------------|-----------|-------|
| pytest (backend unit) | **QUALITY_GATE** | quick, backend, full | Mandatory | Blocks on any failure (-x) |
| pytest (backend integration) | **QUALITY_GATE** | backend, full | Mandatory | Blocks on any failure |
| pytest (backend contract/invariants/properties/engines) | **QUALITY_GATE** | backend, full | Mandatory | Parallel, all must pass |
| pytest (runtime tests) | **QUALITY_GATE** | runtime | Mandatory | Run via run_runtime_verification.sh |
| pytest (mutation smoke) | **SUPPORTING_VERIFICATION** | mutation-smoke | Diagnostic | Infra health only, no quality gate |
| pytest (mutation target/full) | **QUALITY_GATE** | mutation (full) | Mandatory | 80% threshold (Gate C) |
| ruff (backend/src) | **QUALITY_GATE** | quick, backend, full, fast-checks | Mandatory | Blocks on any lint error |
| ruff (repo-wide) | **QUALITY_GATE** | fast-checks | Mandatory | Consolidated config |
| black (backend/src, runtime/) | **QUALITY_GATE** | quick, backend, full | Mandatory | Blocks on formatting diff |
| black (repo-wide) | **QUALITY_GATE** | fast-checks | Mandatory | --check --diff |
| mypy (backend/src) | **QUALITY_GATE** | quick, backend, full, fast-checks | Mandatory | Strict mode, --ignore-missing-imports |
| mypy (runtime/) | **DIAGNOSTIC** | N/A | Advisory | Basic config, not enforced in profiles |
| coverage | **SUPPORTING_VERIFICATION** | backend (aggregate) | Advisory | Reports only, no threshold gate |
| mutation (smoke) | **SUPPORTING_VERIFICATION** | mutation-smoke | Diagnostic | Infra health check only (Gate A/B) |
| mutation (target) | **SUPPORTING_VERIFICATION** | mutation (target) | Diagnostic | Dev subset, no quality gate |
| mutation (full) | **QUALITY_GATE** | mutation (full) | Mandatory | 80% threshold (Gate C) |
| Playwright (chromium, mobile-chrome) | **QUALITY_GATE** | playwright, full | Mandatory | E2E browser tests, matrix |
| npm/eslint | **QUALITY_GATE** | frontend, full | Mandatory | Blocks on lint errors |
| npx tsc --noEmit | **QUALITY_GATE** | frontend, full | Mandatory | Blocks on type errors |
| npm run build | **QUALITY_GATE** | frontend, full | Mandatory | Production build must succeed |
| npx vitest run | **QUALITY_GATE** | frontend, full | Mandatory | Unit/component tests |
| schemathesis | **QUALITY_GATE** (when installed) | backend, contracts, full | Mandatory | Contract tests, guarded by availability |
| pip-audit | **SUPPORTING_VERIFICATION** | dependency-update | Advisory | Reports vulnerabilities, non-blocking |
| npm audit | **SUPPORTING_VERIFICATION** | dependency-update | Advisory | Reports vulnerabilities, non-blocking |

## Policy Rules

1. **QUALITY_GATE** — Failure blocks verification profile (exit ≠ 0). Profile cannot pass if any quality gate fails.
2. **DIAGNOSTIC** — Failure reported but does not block profile. Used for advisory information.
3. **SUPPORTING_VERIFICATION** — Required for profile completeness but not a standalone gate. Failure may degrade profile but not necessarily fail it.

## Enforcement

- All QUALITY_GATE tools run with `-x` / `--fail-under` / `--check` flags to ensure immediate failure on violations
- DIAGNOSTIC tools run without `-x` and failures are logged but profile continues
- SUPPORTING_VERIFICATION tools are required for evidence completeness but profile pass/fail determined by quality gates

## Tool Version Pinning

All tools pinned in root pyproject.toml [project.optional-dependencies.verification]:
- pytest==9.1.1
- ruff==0.15.20
- black==26.5.1
- mypy==2.1.0
- mutmut==3.7.0 (contractual pin - trampoline shim depends on internals)
- schemathesis==4.17.0 (optional [contract] extra)

---

*This policy is enforced by verification profiles in runtime/foundation/verification/profiles.py*