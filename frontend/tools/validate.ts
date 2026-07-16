#!/usr/bin/env npx tsx
/**
 * Phase 8 — Frontend Validation Orchestrator
 *
 * Entry point for all validation phases.
 * Features:
 * - Mode selection (--fast, --architecture, --types, --api, --query, --imports, --build, --all)
 * - Error loop detection (compares with previous runs)
 * - Change intelligence (selects phases based on changed files)
 * - Validation manifest generation
 * - History tracking (last 100 runs)
 */

import * as fs from 'fs'
import type { AuditResult, ValidationManifest, ValidationHistoryEntry, AuditMode } from './types'
import { getChangedFiles, determineStrategy, resolveFrontend, writeFile, resultToMarkdown } from './utils'
import { runToolchainLock } from './lock_toolchain'
import { runArchitectureAudit } from './architecture_audit'
import { runTypeReactAudit } from './type_react_audit'
import { runGeneratedApiAudit } from './generated_api_audit'
import { runQueryAudit } from './query_audit'
import { runImportAudit } from './import_audit'
// Build audit is imported dynamically to avoid slow startup

const HISTORY_FILE = resolveFrontend('generated', 'validation-history.json')
const REPORT_FILE = resolveFrontend('generated', 'validation-report.md')
const MANIFEST_FILE = resolveFrontend('generated', 'validation-manifest.json')

interface Stage {
  name: string
  key: string
  run: () => Promise<AuditResult>
}

function parseMode(): AuditMode {
  const args = process.argv.slice(2)
  if (args.includes('--fast')) return 'fast'
  if (args.includes('--architecture')) return 'architecture'
  if (args.includes('--types')) return 'types'
  if (args.includes('--api')) return 'api'
  if (args.includes('--query')) return 'query'
  if (args.includes('--imports')) return 'imports'
  if (args.includes('--build')) return 'build'
  return 'all'
}

function getStagesForMode(mode: AuditMode, changedFiles: string[]): Stage[] {
  const allStages: Stage[] = [
    { name: 'Toolchain Lock', key: 'toolchain', run: runToolchainLock },
    { name: 'Architecture Audit', key: 'architecture', run: runArchitectureAudit },
    { name: 'Type & React Audit', key: 'types', run: runTypeReactAudit },
    { name: 'Generated API Audit', key: 'api', run: runGeneratedApiAudit },
    { name: 'React Query Audit', key: 'query', run: runQueryAudit },
    { name: 'Import Graph Audit', key: 'imports', run: runImportAudit },
  ]

  // Build audit is special - it runs shell commands
  const buildStage: Stage = {
    name: 'Build Validation',
    key: 'build',
    run: async () => {
      const { runBuildAudit } = await import('./build_audit')
      return runBuildAudit()
    },
  }

  if (mode === 'all') {
    return [...allStages, buildStage]
  }

  if (mode === 'fast') {
    // Fast mode: only toolchain + build
    return [allStages[0]!, buildStage]
  }

  // Change intelligence: determine stages from changed files
  const modeStageMap: Record<AuditMode, string[]> = {
    'fast': ['toolchain'],
    'architecture': ['architecture'],
    'types': ['types'],
    'api': ['api'],
    'query': ['query'],
    'imports': ['imports'],
    'build': [],
    'all': [],
  }

  const selectedKeys = new Set(modeStageMap[mode] ?? [])
  const stageMap = new Map(allStages.map((s) => [s.key, s]))

  // Change intelligence: if files in components/ changed, run architecture + types + api
  const hasComponentChanges = changedFiles.some((f) => f.startsWith('components/'))
  const hasHookChanges = changedFiles.some((f) => f.startsWith('lib/hooks/'))
  const hasTypeChanges = changedFiles.some((f) => f.startsWith('types/'))
  const hasAppChanges = changedFiles.some((f) => f.startsWith('app/'))

  if (hasComponentChanges) {
    selectedKeys.add('architecture')
    selectedKeys.add('types')
    selectedKeys.add('api')
  }
  if (hasHookChanges) {
    selectedKeys.add('types')
    selectedKeys.add('api')
    selectedKeys.add('query')
  }
  if (hasTypeChanges) {
    selectedKeys.add('api')
    selectedKeys.add('types')
  }
  if (hasAppChanges) {
    selectedKeys.add('architecture')
    selectedKeys.add('types')
  }

  const selected = [...selectedKeys].map((key) => stageMap.get(key)).filter((s): s is Stage => s !== undefined)
  selected.push(buildStage)
  return selected
}

function loadHistory(): ValidationHistoryEntry[] {
  try {
    const data = fs.readFileSync(HISTORY_FILE, 'utf-8')
    return JSON.parse(data) as ValidationHistoryEntry[]
  } catch {
    return []
  }
}

function saveHistory(history: ValidationHistoryEntry[]): void {
  // Keep only last 100 entries
  const trimmed = history.slice(-100)
  writeFile(HISTORY_FILE, JSON.stringify(trimmed, null, 2))
}

function detectErrorLoops(history: ValidationHistoryEntry[]): { errors: string[]; suggestion: string } | null {
  // Look at last N runs for the same error patterns
  const recentRuns = history.slice(-5)
  if (recentRuns.length < 3) return null

  // Check if same stage is failing repeatedly
  const stageResults = recentRuns.map((r) => r.stageResults)
  const persistentFailures: string[] = []
  for (const stageName of Object.keys(stageResults[0] ?? {})) {
    const fails = stageResults.filter((sr) => {
      const stage = sr[stageName]
      return stage && !stage.pass
    })
    if (fails.length >= 3) {
      persistentFailures.push(stageName)
    }
  }

  if (persistentFailures.length > 0) {
    return {
      errors: persistentFailures,
      suggestion: `The following stages have failed for ${Math.min(recentRuns.length, 5)} consecutive runs: ${persistentFailures.join(', ')}. Consider reverting recent changes instead of continuing incremental fixes.`,
    }
  }

  return null
}

function generateManifest(
  changedFiles: string[],
  strategy: 'fast' | 'full',
  stages: string[],
  results: AuditResult[],
  durationMs: number,
): ValidationManifest {
  const errors = results.filter((r) => !r.pass)
  return {
    timestamp: new Date().toISOString(),
    changedFiles,
    strategy,
    stages,
    durationMs,
    status: errors.length === 0 ? 'PASS' : errors.length === results.length ? 'FAIL' : 'PARTIAL',
    errorCount: results.reduce((sum, r) => sum + r.issues.filter((i) => i.severity === 'error').length, 0),
    warningCount: results.reduce((sum, r) => sum + r.issues.filter((i) => i.severity === 'warning').length, 0),
  }
}

function generateReport(_stages: string[], results: AuditResult[], manifest: ValidationManifest, errorLoop: { errors: string[]; suggestion: string } | null): string {
  const lines: string[] = []
  lines.push('# Frontend Validation Report')
  lines.push('')
  lines.push(`**Timestamp:** ${manifest.timestamp}`)
  lines.push(`**Strategy:** ${manifest.strategy}`)
  lines.push(`**Duration:** ${(manifest.durationMs / 1000).toFixed(1)}s`)
  lines.push(`**Status:** ${manifest.status === 'PASS' ? '✅ PASS' : manifest.status === 'FAIL' ? '❌ FAIL' : '⚠️ PARTIAL'}`)
  lines.push(`**Errors:** ${manifest.errorCount} | **Warnings:** ${manifest.warningCount}`)
  lines.push('')

  // Error loop detection
  if (errorLoop) {
    lines.push('## ⚠️ AI Error Loop Detected')
    lines.push('')
    lines.push(`**Repeated failures in:** ${errorLoop.errors.join(', ')}`)
    lines.push('')
    lines.push(`**Suggestion:** ${errorLoop.suggestion}`)
    lines.push('')
  }

  // Summary table
  lines.push('## Summary')
  lines.push('')
  lines.push('| Stage | Status | Duration | Summary |')
  lines.push('|-------|--------|----------|---------|')
  for (const result of results) {
    const icon = result.pass ? '✅' : '❌'
    lines.push(`| ${icon} ${result.name} | ${result.pass ? 'PASS' : 'FAIL'} | ${result.durationMs}ms | ${result.summary} |`)
  }
  lines.push('')

  // Detailed results
  lines.push('## Detailed Results')
  lines.push('')
  for (const result of results) {
    lines.push(resultToMarkdown(result))
    lines.push('')
  }

  return lines.join('\n')
}

// eslint-disable-next-line no-console -- CLI tool output
async function main(): Promise<void> {
  const overallStart = Date.now()
  const mode = parseMode()
  const changedFiles = getChangedFiles()
  const strategy = determineStrategy(changedFiles)

  console.log(`\n🔍 Frontend Validation Framework`)
  console.log(`   Mode: ${mode}`)
  console.log(`   Strategy: ${strategy}`)
  console.log(`   Changed files: ${changedFiles.length > 0 ? changedFiles.length : 'none (full scan)'}`)
  console.log('')

  const stages = getStagesForMode(mode, changedFiles)

  if (stages.length === 0) {
    console.error('No stages selected for mode:', mode)
    process.exit(1)
  }

  console.log(`Running ${stages.length} stage(s):`)
  for (const stage of stages) {
    console.log(`  - ${stage.name}`)
  }
  console.log('')

  const results: AuditResult[] = []

  for (const stage of stages) {
    const stageStart = Date.now()
    process.stdout.write(`  [ ] ${stage.name}...`)

    try {
      const result = await stage.run()
      results.push(result)
      const duration = Date.now() - stageStart
      process.stdout.write(`\r  ${result.pass ? '✅' : '❌'} ${stage.name} (${duration}ms) - ${result.summary}\n`)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err)
      process.stdout.write(`\r  ❌ ${stage.name} - CRASHED: ${errorMsg}\n`)
      results.push({
        name: stage.name,
        pass: false,
        durationMs: Date.now() - stageStart,
        issues: [{ severity: 'error', message: `Stage crashed: ${errorMsg}` }],
        summary: 'Crashed',
      })
    }
  }

  const overallDuration = Date.now() - overallStart

  // Load history and detect error loops
  const history = loadHistory()
  const errorLoop = detectErrorLoops(history)

  // Generate manifest
  const manifest = generateManifest(
    changedFiles,
    strategy,
    stages.map((s) => s.key),
    results,
    overallDuration,
  )

  // Generate report
  const report = generateReport(
    stages.map((s) => s.name),
    results,
    manifest,
    errorLoop,
  )

  // Write outputs
  writeFile(REPORT_FILE, report)
  writeFile(MANIFEST_FILE, JSON.stringify(manifest, null, 2))

  // Save history entry
  const historyEntry: ValidationHistoryEntry = {
    timestamp: manifest.timestamp,
    manifest,
    stageResults: Object.fromEntries(
      results.map((r) => [r.name, { pass: r.pass, issues: r.issues.length }]),
    ),
  }
  history.push(historyEntry)
  saveHistory(history)

  // Print summary
  console.log('\n' + '='.repeat(50))
  console.log(`Total: ${(overallDuration / 1000).toFixed(1)}s`)
  console.log(`Status: ${manifest.status === 'PASS' ? '✅ ALL PASSED' : manifest.status === 'FAIL' ? '❌ FAILED' : '⚠️ PARTIAL'}`)
  console.log(`Errors: ${manifest.errorCount} | Warnings: ${manifest.warningCount}`)
  console.log(`Report: ${REPORT_FILE}`)
  console.log(`Manifest: ${MANIFEST_FILE}`)
  console.log('')

  if (errorLoop) {
    console.log('⚠️  AI ERROR LOOP DETECTED')
    console.log(`  Repeated: ${errorLoop.errors.join(', ')}`)
    console.log(`  ${errorLoop.suggestion}`)
    console.log('')
  }

  process.exit(manifest.status === 'PASS' ? 0 : 1)
}

main().catch((err) => {
  console.error('FATAL:', err)
  process.exit(1)
})