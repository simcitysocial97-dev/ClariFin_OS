# Frontend Validation Report

**Timestamp:** 2026-07-16T04:45:28.324Z
**Strategy:** fast
**Duration:** 374.9s
**Status:** ⚠️ PARTIAL
**Errors:** 1 | **Warnings:** 6

## ⚠️ AI Error Loop Detected

**Repeated failures in:** Build Validation

**Suggestion:** The following stages have failed for 5 consecutive runs: Build Validation. Consider reverting recent changes instead of continuing incremental fixes.

## Summary

| Stage | Status | Duration | Summary |
|-------|--------|----------|---------|
| ✅ Toolchain Lock | PASS | 6ms | 0 errors, 6 warnings |
| ❌ Build Validation | FAIL | 374767ms | 1 errors, 0 warnings |

## Detailed Results

## Toolchain Lock
**Status:** ✅ PASS | **Duration:** 6ms
**Summary:** 0 errors, 6 warnings

| Severity | File | Message |
|----------|------|---------|
| 🟡 warning | - | typescript uses floating version range "^5". Pin to exact version for reproducibility. |
| 🟡 warning | - | @tanstack/react-query uses floating version range "^5.101.2". Pin to exact version for reproducibility. |
| 🟡 warning | - | tailwindcss uses floating version range "^4". Pin to exact version for reproducibility. |
| 🟡 warning | - | zod uses floating version range "^4.4.3". Pin to exact version for reproducibility. |
| 🟡 warning | - | zustand uses floating version range "^5.0.11". Pin to exact version for reproducibility. |
| 🟡 warning | - | recharts uses floating version range "^3.7.0". Pin to exact version for reproducibility. |


## Build Validation
**Status:** ❌ FAIL | **Duration:** 374767ms
**Summary:** 1 errors, 0 warnings

| Severity | File | Message |
|----------|------|---------|
| 🔴 error | - | ESLint failed with 0 error(s) and 0 warning(s) |

