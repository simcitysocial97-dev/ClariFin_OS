/**
 * Phase 1 — Toolchain Lock
 *
 * Audits package.json, tsconfig.json, next.config.ts, eslint config
 * Records exact versions, detects duplicates, incompatible ranges, deprecated packages
 */

import type { AuditIssue, AuditResult } from './types'
import { readJsonFile, readTextFile, resolveFrontend, createResult, writeFile } from './utils'

interface ToolchainSnapshot {
  timestamp: string
  versions: Record<string, string>
  issues: string[]
  configs: {
    packageJson: Record<string, unknown> | null
    tsconfig: Record<string, unknown> | null
    nextConfig: string | null
  }
}

const KNOWN_DEPRECATED: Set<string> = new Set([
  '@types/react@<18',
  'moment',
  'recompose',
  'redux-form',
  'react-router-dom@<6',
  'styled-components@<6',
  'uuid',
  'axios',
])

const REACT_19_COMPATIBLE: Record<string, string> = {
  'react': '>=19.0.0',
  'react-dom': '>=19.0.0',
  '@types/react': '>=19.0.0',
  '@types/react-dom': '>=19.0.0',
  'next': '>=15.0.0',
  '@tanstack/react-query': '>=5.0.0',
  'zustand': '>=5.0.0',
  'recharts': '>=2.15.0',
}

function checkFloatingRange(version: string): boolean {
  return version.startsWith('^') || version.startsWith('~') || version.startsWith('>') || version.startsWith('<')
}

function extractExactVersion(versionSpec: string): string {
  return versionSpec.replace(/^[\^~>=<\s]+/, '').split(' ')[0]?.split('||')[0]?.trim() ?? versionSpec
}

export async function runToolchainLock(): Promise<AuditResult> {
  const start = Date.now()
  const issues: AuditIssue[] = []
  const versions: Record<string, string> = {}
  const lockIssues: string[] = []

  // Read package.json
  const pkg = readJsonFile(resolveFrontend('package.json'))
  if (!pkg) {
    issues.push({ severity: 'error', message: 'package.json not found or unreadable' })
    return createResult('Toolchain Lock', issues, start)
  }

  const deps = { ...(pkg.dependencies as Record<string, string> ?? {}), ...(pkg.devDependencies as Record<string, string> ?? {}) }

  // Extract all versions
  const criticalPkgs = ['next', 'react', 'react-dom', 'typescript', '@tanstack/react-query', 'tailwindcss', 'zod', 'zustand', 'recharts']
  for (const pkgName of criticalPkgs) {
    if (deps[pkgName]) {
      versions[pkgName] = deps[pkgName]
    }
  }

  // Also get @types
  for (const key of Object.keys(deps)) {
    if (key.startsWith('@types/')) {
      versions[key] = deps[key]
    }
  }

  // Check for floating ranges in critical packages
  for (const pkgName of criticalPkgs) {
    const ver = deps[pkgName]
    if (ver && checkFloatingRange(ver)) {
      issues.push({
        severity: 'warning',
        code: 'FLOATING_VERSION',
        message: `${pkgName} uses floating version range "${ver}". Pin to exact version for reproducibility.`,
        suggestion: `Replace "${ver}" with "${extractExactVersion(ver)}"`,
      })
      lockIssues.push(`Floating version: ${pkgName}@${ver}`)
    }
  }

  // Check React 19 compatibility of major deps
  for (const [pkgName, requiredVer] of Object.entries(REACT_19_COMPATIBLE)) {
    const installedVer = deps[pkgName]
    if (installedVer) {
      const exact = extractExactVersion(installedVer)
      const major = parseInt(exact.split('.')[0] ?? '0', 10)
      const requiredMajor = parseInt(requiredVer.replace('>=', '').split('.')[0] ?? '0', 10)
      if (major < requiredMajor) {
        issues.push({
          severity: 'error',
          code: 'INCOMPATIBLE_VERSION',
          message: `${pkgName}@${installedVer} may not be compatible with React 19 (need ${requiredVer})`,
        })
        lockIssues.push(`Incompatible: ${pkgName}@${installedVer}`)
      }
    }
  }

  // Check for deprecated packages
  for (const [pkgName, ver] of Object.entries(deps)) {
    const key = `${pkgName}@${extractExactVersion(ver)}`
    if (KNOWN_DEPRECATED.has(key) || KNOWN_DEPRECATED.has(pkgName)) {
      issues.push({
        severity: 'warning',
        code: 'DEPRECATED_PACKAGE',
        message: `${pkgName} is deprecated. Consider migrating to an alternative.`,
        suggestion: getDeprecationSuggestion(pkgName),
      })
      lockIssues.push(`Deprecated: ${pkgName}`)
    }
  }

  // Check for duplicate versions (same package in both deps and devDeps)
  const depPkgs = Object.keys(pkg.dependencies as Record<string, string> ?? {})
  const devDepPkgs = Object.keys(pkg.devDependencies as Record<string, string> ?? {})
  for (const pkgName of depPkgs) {
    if (devDepPkgs.includes(pkgName)) {
      issues.push({
        severity: 'warning',
        code: 'DUPLICATE_VERSION',
        message: `${pkgName} appears in both dependencies and devDependencies`,
      })
      lockIssues.push(`Duplicate: ${pkgName}`)
    }
  }

  // Read tsconfig.json
  const tsconfig = readJsonFile(resolveFrontend('tsconfig.json'))
  if (tsconfig) {
    const strict = (tsconfig.compilerOptions as Record<string, unknown>)?.strict
    if (strict === false || strict === undefined) {
      issues.push({
        severity: 'error',
        code: 'NON_STRICT_TSCONFIG',
        message: 'tsconfig.json should have strict: true',
      })
    }
  }

  // Read next.config.ts
  const nextConfig = readTextFile(resolveFrontend('next.config.ts'))

  // Generate snapshot
  const snapshot: ToolchainSnapshot = {
    timestamp: new Date().toISOString(),
    versions,
    issues: lockIssues,
    configs: {
      packageJson: pkg,
      tsconfig,
      nextConfig,
    },
  }

  writeFile(resolveFrontend('generated', 'toolchain-lock.json'), JSON.stringify(snapshot, null, 2))

  return createResult('Toolchain Lock', issues, start)
}

function getDeprecationSuggestion(pkgName: string): string | undefined {
  const map: Record<string, string> = {
    'moment': 'Use date-fns or dayjs instead',
    'recompose': 'Use React hooks instead',
    'redux-form': 'Use React Hook Form or Formik',
    'axios': 'Use native fetch or ky',
    'uuid': 'Use crypto.randomUUID()',
  }
  return map[pkgName]
}