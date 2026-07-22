/**
 * Phase 7 — Build Validation
 *
 * Runs each build step independently:
 * 1. tsc --noEmit (type checking)
 * 2. eslint (linting)
 * 3. next build (production build)
 *
 * Collects results separately so one failure doesn't mask the others.
 */

import { execSync } from 'child_process'
import type { AuditIssue, AuditResult } from './types'
import { resolveFrontend, createResult, writeFile } from './utils'

interface BuildStepResult {
  name: string
  pass: boolean
  durationMs: number
  stdout: string
  stderr: string
  errorCount: number
  warningCount: number
}

function runCommand(cmd: string, cwd: string, timeoutMs = 120_000): { stdout: string; stderr: string; code: number } {
  try {
    const output = execSync(cmd, {
      cwd,
      encoding: 'utf-8',
      timeout: timeoutMs,
      stdio: ['pipe', 'pipe', 'pipe'],
      maxBuffer: 10 * 1024 * 1024, // 10MB
    })
    return { stdout: output?.toString() ?? '', stderr: '', code: 0 }
  } catch (err: unknown) {
    const execErr = err as { stdout?: Buffer | string; stderr?: Buffer | string; status?: number }
    return {
      stdout: execErr.stdout?.toString() ?? '',
      stderr: execErr.stderr?.toString() ?? '',
      code: execErr.status ?? 1,
    }
  }
}

function parseTscErrors(stdout: string, stderr: string): { errorCount: number; warningCount: number } {
  const combined = stdout + '\n' + stderr
  const errorLines = combined.split('\n').filter((l) => l.includes('error TS'))
  const warningLines = combined.split('\n').filter((l) => l.includes('warning TS'))
  return {
    errorCount: errorLines.length,
    warningCount: warningLines.length,
  }
}

function parseEslintErrors(stdout: string, stderr: string): { errorCount: number; warningCount: number } {
  const combined = stdout + '\n' + stderr
  const errorLines = combined.split('\n').filter((l) => l.includes('error') && !l.includes('warning'))
  const warningLines = combined.split('\n').filter((l) => l.includes('warning'))
  return {
    errorCount: errorLines.length,
    warningCount: warningLines.length,
  }
}

function parseBuildErrors(stdout: string, stderr: string): { errorCount: number; warningCount: number; bundleSize?: string; buildTime?: string } {
  const combined = stdout + '\n' + stderr
  const errors = combined.split('\n').filter((l) => l.toLowerCase().includes('error')).length
  const warnings = combined.split('\n').filter((l) => l.toLowerCase().includes('warn')).length

  // Extract build time and bundle size
  const buildTimeMatch = combined.match(/(?:Compiled|Build completed)\s+in\s+([\d.]+)\s*(ms|s|m)/)
  const buildTime = buildTimeMatch ? buildTimeMatch[0] : undefined

  const sizeMatch = combined.match(/(?:size|Total)\s*(?:of|:)?\s*([\d.]+)\s*(KB|MB|kB)/)
  const bundleSize = sizeMatch ? `${sizeMatch[1]} ${sizeMatch[2]}` : undefined

  return { errorCount: errors, warningCount: warnings, bundleSize, buildTime }
}

export async function runBuildAudit(): Promise<AuditResult> {
  const start = Date.now()
  const issues: AuditIssue[] = []
  const results: BuildStepResult[] = []
  const frontendRoot = resolveFrontend()

  // Step 1: TypeScript check
  if (process.argv.includes('--skip-tsc')) {
    results.push({ name: 'TypeScript', pass: true, durationMs: 0, stdout: '', stderr: '', errorCount: 0, warningCount: 0 })
  } else {
    const tsStart = Date.now()
    const { stdout, stderr, code } = runCommand('npx tsc --noEmit', frontendRoot)
    const { errorCount, warningCount } = parseTscErrors(stdout, stderr)
    results.push({
      name: 'TypeScript',
      pass: code === 0,
      durationMs: Date.now() - tsStart,
      stdout: stdout.slice(0, 2000),
      stderr: stderr.slice(0, 2000),
      errorCount,
      warningCount,
    })
    if (code !== 0) {
      issues.push({
        severity: 'error',
        code: 'TSC_ERRORS',
        message: `TypeScript compilation failed with ${errorCount} error(s) and ${warningCount} warning(s)`,
      })
    }
  }

  // Step 2: ESLint check
  const lintStart = Date.now()
  const { stdout: lintStdout, stderr: lintStderr, code: lintCode } = runCommand('npx eslint . --max-warnings 0', frontendRoot)
  const { errorCount: lintErrors, warningCount: lintWarnings } = parseEslintErrors(lintStdout, lintStderr)
  results.push({
    name: 'ESLint',
    pass: lintCode === 0,
    durationMs: Date.now() - lintStart,
    stdout: lintStdout.slice(0, 2000),
    stderr: lintStderr.slice(0, 2000),
    errorCount: lintErrors,
    warningCount: lintWarnings,
  })
  if (lintCode !== 0) {
    issues.push({
      severity: 'error',
      code: 'ESLINT_ERRORS',
      message: `ESLint failed with ${lintErrors} error(s) and ${lintWarnings} warning(s)`,
      suggestion: 'Run `npm run lint` locally to see detailed errors.',
    })
  }

  // Step 3: Next.js build
  const buildStart = Date.now()
  const { stdout: buildStdout, stderr: buildStderr, code: buildCode } = runCommand('npx next build', frontendRoot, 300_000)
  const { errorCount: buildErrors, warningCount: buildWarnings, bundleSize, buildTime } = parseBuildErrors(buildStdout, buildStderr)
  results.push({
    name: 'Next.js Build',
    pass: buildCode === 0,
    durationMs: Date.now() - buildStart,
    stdout: buildStdout.slice(0, 2000),
    stderr: buildStderr.slice(0, 2000),
    errorCount: buildErrors,
    warningCount: buildWarnings,
  })
  if (buildCode !== 0) {
    issues.push({
      severity: 'error',
      code: 'BUILD_ERRORS',
      message: `Next.js build failed with ${buildErrors} error(s) and ${buildWarnings} warning(s)`,
      suggestion: 'Check the build output above for specific error messages.',
    })
  } else if (buildErrors > 0) {
    issues.push({
      severity: 'warning',
      code: 'BUILD_WARNINGS',
      message: `Build succeeded but with ${buildWarnings} warning(s)`,
    })
  }

  // Generate build report
  const buildReport = {
    timestamp: new Date().toISOString(),
    duration: Date.now() - start,
    bundleSize,
    buildTime,
    steps: results.map((r) => ({
      name: r.name,
      pass: r.pass,
      durationMs: r.durationMs,
      errorCount: r.errorCount,
      warningCount: r.warningCount,
    })),
    allPassed: results.every((r) => r.pass),
  }

  writeFile(resolveFrontend('generated', 'build-report.json'), JSON.stringify(buildReport, null, 2))

  return createResult('Build Validation', issues, start)
}