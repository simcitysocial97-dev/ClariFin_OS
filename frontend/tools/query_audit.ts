/**
 * Phase 5 — React Query Audit
 *
 * Validates TanStack Query usage:
 * - Duplicate query keys
 * - Invalid invalidation patterns
 * - Stale time vs gc time misuse
 * - Mutation onSuccess correctness
 * - Suspense mode compatibility
 */

import * as path from 'path'
import type { AuditIssue, AuditResult } from './types'
import { walkTsFiles, resolveFrontend, createResult, readTextFile } from './utils'

interface QueryKeyInfo {
  key: string
  file: string
  line: number
  type: 'query' | 'mutation' | 'invalidation'
}

export async function runQueryAudit(): Promise<AuditResult> {
  const start = Date.now()
  const issues: AuditIssue[] = []

  const allFiles = walkTsFiles(resolveFrontend())
    .filter((f) =>
      !f.includes('node_modules') &&
      !f.includes('.next') &&
      !f.includes('generated') &&
      !f.includes('tools') // Don't audit the tools themselves
    )

  const queryKeys: QueryKeyInfo[] = []
  const mutationInvalidations: Array<{ key: string; file: string; line: number }> = []

  for (const filePath of allFiles) {
    const content = readTextFile(filePath)
    if (!content) continue
    const relativePath = path.relative(resolveFrontend(), filePath)

    // Skip files that don't use React Query
    if (!content.includes('useQuery') && !content.includes('useMutation') && !content.includes('queryKey') && !content.includes('invalidateQueries')) {
      continue
    }

    // Extract query keys from useQuery calls using regex
    const queryKeyRegex = /queryKey:\s*\[([^\]]+)\]/g
    let match: RegExpExecArray | null
    while ((match = queryKeyRegex.exec(content)) !== null) {
      const keyContent = match[1]?.trim() ?? ''
      const lineNumber = content.substring(0, match.index).split('\n').length
      queryKeys.push({
        key: keyContent,
        file: relativePath,
        line: lineNumber,
        type: 'query',
      })
    }

    // Extract invalidation patterns
    const invalidateRegex = /invalidateQueries\(\{?\s*queryKey:\s*\[([^\]]+)\]/g
    while ((match = invalidateRegex.exec(content)) !== null) {
      const keyContent = match[1]?.trim() ?? ''
      const lineNumber = content.substring(0, match.index).split('\n').length
      mutationInvalidations.push({
        key: keyContent,
        file: relativePath,
        line: lineNumber,
      })
    }
  }

  // Check 1: Duplicate query keys (deduplicated - one issue per unique key)
  const seenKeys = new Map<string, { count: number; file: string; line: number }>()
  for (const qk of queryKeys) {
    const normalizedKey = qk.key.replace(/\s+/g, ' ')
    const existing = seenKeys.get(normalizedKey)
    if (!existing) {
      seenKeys.set(normalizedKey, { count: 1, file: qk.file, line: qk.line })
    } else {
      seenKeys.set(normalizedKey, { count: existing.count + 1, file: existing.file, line: existing.line })
    }
  }
  for (const [key, { count, file, line }] of Array.from(seenKeys.entries())) {
    if (count > 1) {
      issues.push({
        severity: 'warning',
        code: 'DUPLICATE_QUERY_KEY',
        file,
        line,
        message: `Query key [${key}] is used ${count} times across the codebase. Duplicate keys can cause cache collisions.`,
        suggestion: 'Use unique query keys or namespace them (e.g., ["dashboard", "summary"] vs ["accounts", "list"]).',
      })
    }
  }

  // Check 2: Invalidations that don't match any query key
  for (const inv of mutationInvalidations) {
    const normalizedInvKey = inv.key.replace(/\s+/g, ' ')
    const matchingQuery = Array.from(seenKeys.keys()).some((qk) => qk.replace(/\s+/g, ' ') === normalizedInvKey)
    if (!matchingQuery) {
      issues.push({
        severity: 'warning',
        code: 'INVALIDATION_NO_MATCHING_QUERY',
        file: inv.file,
        line: inv.line,
        message: `invalidateQueries([${inv.key}]) does not match any defined queryKey. This invalidation has no effect.`,
        suggestion: 'Verify the query key matches exactly with the useQuery call it should invalidate.',
      })
    }
  }

  // Check 3: staleTime > gcTime (misconfiguration)
  for (const filePath of allFiles) {
    const content = readTextFile(filePath)
    if (!content) continue
    const relativePath = path.relative(resolveFrontend(), filePath)

    const staleTimeMatch = content.match(/staleTime:\s*(\d+)/)
    const gcTimeMatch = content.match(/gcTime:\s*(\d+)/)
    if (staleTimeMatch && gcTimeMatch) {
      const staleTime = parseInt(staleTimeMatch[1] ?? '0', 10)
      const gcTime = parseInt(gcTimeMatch[1] ?? '0', 10)
      if (staleTime > gcTime) {
        issues.push({
          severity: 'error',
          code: 'STALE_TIME_EXCEEDS_GC_TIME',
          file: relativePath,
          message: `staleTime (${staleTime}ms) exceeds gcTime (${gcTime}ms). Data will be garbage collected before it can be reused.`,
          suggestion: 'Set gcTime to be greater than staleTime (typically 5x the staleTime).',
        })
      }
    }

    // Note: Removed QUERY_IN_EVENT_HANDLER check as regex-based detection has too many false positives
    // Static analysis cannot reliably detect useQuery calls inside event handlers without AST parsing

    // Check 4: Suspense misuse
    if (content.includes('suspense: true') && content.includes('useQuery')) {
      const hasErrorBoundary = content.includes('ErrorBoundary') || content.includes('error.tsx')
      if (!hasErrorBoundary) {
        issues.push({
          severity: 'warning',
          code: 'SUSPENSE_WITHOUT_ERROR_BOUNDARY',
          file: relativePath,
          message: 'Query uses suspense: true but no ErrorBoundary is detected in the file. Suspense queries need error boundaries.',
          suggestion: 'Wrap the component in an ErrorBoundary or add an error.tsx in the route segment.',
        })
      }
    }
  }

  // Check 6: Mutation onSuccess should invalidate related queries
  for (const filePath of allFiles) {
    const content = readTextFile(filePath)
    if (!content || !content.includes('useMutation')) continue

    const relativePath = path.relative(resolveFrontend(), filePath)
    const hasOnSuccess = content.includes('onSuccess')
    const hasInvalidation = content.includes('invalidateQueries')

    if (hasOnSuccess && !hasInvalidation) {
      const lineNumber = content.split('\n').findIndex((l) => l.includes('useMutation')) + 1
      issues.push({
        severity: 'warning',
        code: 'MUTATION_NO_INVALIDATION',
        file: relativePath,
        line: lineNumber,
        message: 'Mutation has onSuccess handler but does not invalidate any queries. Data may become stale.',
        suggestion: 'Add queryClient.invalidateQueries() in the onSuccess callback.',
      })
    }
  }

  return createResult('React Query Audit', issues, start)
}