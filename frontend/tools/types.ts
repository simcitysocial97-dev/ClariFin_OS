/**
 * Shared types for the Frontend Validation Framework (FVF)
 */

export interface AuditResult {
  pass: boolean
  name: string
  durationMs: number
  issues: AuditIssue[]
  summary: string
}

export interface AuditIssue {
  severity: 'error' | 'warning' | 'info'
  file?: string
  line?: number
  code?: string
  message: string
  suggestion?: string
}

export interface ValidationManifest {
  timestamp: string
  changedFiles: string[]
  strategy: 'fast' | 'full'
  stages: string[]
  durationMs: number
  status: 'PASS' | 'FAIL' | 'PARTIAL'
  errorCount: number
  warningCount: number
}

export interface ValidationHistoryEntry {
  timestamp: string
  manifest: ValidationManifest
  stageResults: Record<string, { pass: boolean; issues: number }>
}

export interface ChangedFileInfo {
  path: string
  directory: string
  extension: string
}

export type AuditMode = 'fast' | 'architecture' | 'types' | 'api' | 'query' | 'imports' | 'build' | 'all'