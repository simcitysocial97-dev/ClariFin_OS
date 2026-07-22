/**
 * Shared utilities for the Frontend Validation Framework
 */

import * as fs from 'fs'
import { execSync } from 'child_process'
import * as path from 'path'
import type { AuditIssue, AuditResult } from './types'

const FRONTEND_ROOT = path.resolve(__dirname, '..')

/** Resolve a path relative to the frontend root */
export function resolveFrontend(...segments: string[]): string {
  return path.resolve(FRONTEND_ROOT, ...segments)
}

/** Read a JSON file, returning null on failure */
export function readJsonFile(filePath: string): Record<string, unknown> | null {
  try {
    const content = fs.readFileSync(filePath, 'utf-8')
    return JSON.parse(content) as Record<string, unknown>
  } catch {
    return null
  }
}

/** Read a text file, returning null on failure */
export function readTextFile(filePath: string): string | null {
  try {
    return fs.readFileSync(filePath, 'utf-8')
  } catch {
    return null
  }
}

/** Walk a directory recursively, returning all file paths matching a filter */
export function walkDir(dir: string, filter?: (f: string) => boolean): string[] {
  const results: string[] = []
  if (!fs.existsSync(dir)) return results

  const entries = fs.readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      results.push(...walkDir(fullPath, filter))
    } else if (!filter || filter(fullPath)) {
      results.push(fullPath)
    }
  }
  return results
}

/** Get all TypeScript/TSX files in a directory recursively */
export function walkTsFiles(dir: string): string[] {
  return walkDir(dir, (f) => f.endsWith('.ts') || f.endsWith('.tsx'))
}

/** Create an AuditResult helper */
export function createResult(
  name: string,
  issues: AuditIssue[],
  startTime: number,
): AuditResult {
  const errors = issues.filter((i) => i.severity === 'error')
  const warnings = issues.filter((i) => i.severity === 'warning')
  return {
    name,
    pass: errors.length === 0,
    durationMs: Date.now() - startTime,
    issues,
    summary: `${errors.length} errors, ${warnings.length} warnings`,
  }
}

/** Format an AuditResult as a markdown section */
export function resultToMarkdown(result: AuditResult): string {
  const lines: string[] = []
  const status = result.pass ? '✅ PASS' : '❌ FAIL'
  lines.push(`## ${result.name}`)
  lines.push(`**Status:** ${status} | **Duration:** ${result.durationMs}ms`)
  lines.push(`**Summary:** ${result.summary}`)
  lines.push('')

  if (result.issues.length > 0) {
    lines.push('| Severity | File | Message |')
    lines.push('|----------|------|---------|')
    for (const issue of result.issues) {
      const icon = issue.severity === 'error' ? '🔴' : issue.severity === 'warning' ? '🟡' : '🔵'
      const fileRef = issue.file ? (issue.line ? `${issue.file}:${issue.line}` : issue.file) : '-'
      lines.push(`| ${icon} ${issue.severity} | ${fileRef} | ${issue.message} |`)
    }
    lines.push('')
  }

  return lines.join('\n')
}

/** Write a file, creating parent directories if needed */
export function writeFile(filePath: string, content: string): void {
  const dir = path.dirname(filePath)
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true })
  }
  fs.writeFileSync(filePath, content, 'utf-8')
}

/** Get git changed files (relative to frontend root) */
export function getChangedFiles(): string[] {
  try {
    const output = execSync('git diff --name-only HEAD', {
      cwd: FRONTEND_ROOT,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    })
    return output.split('\n').filter(Boolean)
  } catch {
    return []
  }
}

/** Determine audit strategy based on changed files */
export function determineStrategy(changedFiles: string[]): 'fast' | 'full' {
  const criticalPatterns = [
    /^app\//,
    /^components\//,
    /^lib\//,
    /^types\//,
    /package\.json$/,
    /tsconfig\.json$/,
    /next\.config\./,
  ]
  for (const file of changedFiles) {
    for (const pattern of criticalPatterns) {
      if (pattern.test(file)) return 'full'
    }
  }
  return 'fast'
}