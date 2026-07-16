/**
 * Phase 6 — Import Graph Audit
 *
 * Uses TypeScript Compiler API to analyze the import graph:
 * - Circular dependencies
 * - Deep dependency chains
 * - Forbidden layer violations
 * - Shared module boundary checks
 */

import * as ts from 'typescript'
import * as path from 'path'
import type { AuditIssue, AuditResult } from './types'
import { walkTsFiles, resolveFrontend, createResult, readTextFile } from './utils'

interface ImportEdge {
  from: string
  to: string
  isExternal: boolean
}

// Layer rules: which directories can import from which
const LAYER_RULES: Array<{
  from: RegExp
  allowedTargets: RegExp[]
  forbiddenTargets: RegExp[]
  message: string
}> = [
  {
    from: /^app\//,
    allowedTargets: [/^components\//, /^lib\//, /^hooks\//],
    forbiddenTargets: [/^types\//],
    message: 'app/ should not directly import from types/. Use hooks that wrap types.',
  },
  {
    from: /^components\//,
    allowedTargets: [/^components\//, /^lib\//, /^hooks\//],
    forbiddenTargets: [/^types\//, /^lib\/parser\//],
    message: 'components/ should not import from types/ or lib/parser/ directly.',
  },
  {
    from: /^hooks\//,
    allowedTargets: [/^lib\//, /^types\//],
    forbiddenTargets: [/^app\//, /^components\//],
    message: 'hooks/ should not import from app/ or components/.',
  },
  {
    from: /^lib\//,
    allowedTargets: [/^lib\//, /^types\//],
    forbiddenTargets: [/^app\//, /^components\//, /^hooks\//],
    message: 'lib/ should not import from app/, components/, or hooks/.',
  },
]

function normalizeImportPath(importerPath: string, importPath: string): string {
  const importerDir = path.dirname(importerPath)
  const absolutePath = path.resolve(importerDir, importPath)
  const frontendRoot = resolveFrontend()
  const relativePath = path.relative(frontendRoot, absolutePath)
  return relativePath.replace(/\\/g, '/')
}

function getLayer(filePath: string): string | null {
  const normalized = filePath.replace(/\\/g, '/')
  const layers = ['app', 'components', 'hooks', 'lib', 'types', 'tools']
  for (const layer of layers) {
    if (normalized.startsWith(layer + '/') || normalized.startsWith(layer + '\\')) {
      return layer
    }
  }
  return null
}

export async function runImportAudit(): Promise<AuditResult> {
  const start = Date.now()
  const issues: AuditIssue[] = []

  const allFiles = walkTsFiles(resolveFrontend())
    .filter((f) =>
      !f.includes('node_modules') &&
      !f.includes('.next') &&
      !f.includes('generated') &&
      !f.includes('dist') &&
      !f.includes('tests')
    )

  const edges: ImportEdge[] = []
  const fileMap = new Map<string, string>()

  // Build the import graph
  for (const filePath of allFiles) {
    const content = readTextFile(filePath)
    if (!content) continue

    const relativePath = path.relative(resolveFrontend(), filePath).replace(/\\/g, '/')
    fileMap.set(relativePath, content)

    const sourceFile = ts.createSourceFile(
      path.basename(filePath),
      content,
      ts.ScriptTarget.Latest,
      true,
    )

    ts.forEachChild(sourceFile, (node) => {
      if (ts.isImportDeclaration(node) && node.moduleSpecifier) {
        const moduleName = node.moduleSpecifier.getText(sourceFile).replace(/['"]/g, '')

        // Skip external imports (node_modules)
        if (!moduleName.startsWith('.') && !moduleName.startsWith('/')) {
          edges.push({ from: relativePath, to: moduleName, isExternal: true })
          return
        }

        // Resolve relative path to normalized path
        const resolvedPath = normalizeImportPath(filePath, moduleName)
        edges.push({ from: relativePath, to: resolvedPath, isExternal: false })
      }
    })
  }

  // Check 1: Circular dependencies using DFS
  const visited = new Set<string>()
  const inStack = new Set<string>()
  const cycles: string[][] = []

  function dfs(node: string, stack: string[]): void {
    if (inStack.has(node)) {
      const cycleStart = stack.indexOf(node)
      if (cycleStart >= 0) {
        cycles.push([...stack.slice(cycleStart), node])
      }
      return
    }
    if (visited.has(node)) return

    visited.add(node)
    inStack.add(node)
    stack.push(node)

    const outgoing = edges.filter((e) => e.from === node && !e.isExternal)
    for (const edge of outgoing) {
      dfs(edge.to, stack)
    }

    stack.pop()
    inStack.delete(node)
  }

  // Only check files in our project - convert Set to Array
  const projectFiles = Array.from(new Set(edges.filter((e) => !e.isExternal).map((e) => e.from)))
  projectFiles.forEach((f) => dfs(f, []))

  // Deduplicate cycles (keep unique cycles)
  const uniqueCycles = new Set<string>()
  for (const cycle of cycles) {
    const normalized = cycle.join(' -> ')
    if (!uniqueCycles.has(normalized)) {
      uniqueCycles.add(normalized)
      issues.push({
        severity: 'error',
        code: 'CIRCULAR_DEPENDENCY',
        file: cycle[0],
        message: `Circular dependency detected: ${cycle.join(' -> ')}`,
        suggestion: 'Extract the shared dependency into a separate module or use dependency inversion.',
      })
    }
  }

  // Check 2: Deep dependency chains (depth > 5)
  const depths = new Map<string, number>()
  function calculateDepth(node: string): number {
    if (depths.has(node)) return depths.get(node)!
    const outgoing = edges.filter((e) => e.from === node && !e.isExternal)
    if (outgoing.length === 0) {
      depths.set(node, 0)
      return 0
    }
    let maxDepth = 0
    for (const edge of outgoing) {
      const depth = calculateDepth(edge.to) + 1
      maxDepth = Math.max(maxDepth, depth)
    }
    depths.set(node, maxDepth)
    return maxDepth
  }

  for (const file of projectFiles) {
    calculateDepth(file)
  }

  const deepFiles = Array.from(depths.entries())
    .filter(([, depth]) => depth > 5)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)

  for (const entry of deepFiles) {
    const file = entry[0]
    const depth = entry[1]
    issues.push({
      severity: 'warning',
      code: 'DEEP_DEPENDENCY_CHAIN',
      file,
      message: `File has deep dependency chain (depth: ${depth}). Consider refactoring to reduce coupling.`,
      suggestion: 'Break the file into smaller modules or use composition over deep inheritance.',
    })
  }

  // Check 3: Layer violations
  for (const edge of edges) {
    if (edge.isExternal) continue

    const fromLayer = getLayer(edge.from)
    const toLayer = getLayer(edge.to)

    if (fromLayer && toLayer) {
      for (const rule of LAYER_RULES) {
        if (rule.from.test(fromLayer + '/')) {
          for (const forbidden of rule.forbiddenTargets) {
            if (forbidden.test(edge.to)) {
              issues.push({
                severity: 'error',
                code: 'LAYER_VIOLATION',
                file: edge.from,
                message: `${fromLayer}/ imports from ${toLayer}/ (${edge.to}). ${rule.message}`,
                suggestion: 'Restructure imports to respect the layer hierarchy.',
              })
              break
            }
          }
        }
      }
    }
  }

  // Check 4: Export depth analysis (top 5 deepest files)
  const sortedByDepth = Array.from(depths.entries())
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)

  if (sortedByDepth.length > 0) {
    issues.push({
      severity: 'info',
      code: 'DEEPEST_IMPORT_CHAINS',
      message: `Deepest import chains:\n${sortedByDepth.map(([f, d]) => `  - ${f} (depth: ${d})`).join('\n')}`,
    })
  }

  return createResult('Import Graph Audit', issues, start)
}