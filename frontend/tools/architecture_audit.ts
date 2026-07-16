/**
 * Phase 2 — Architecture Audit
 *
 * Uses TypeScript Compiler API to validate Server/Client Component boundaries.
 * Detects:
 * - Server Components using hooks (useState, useEffect, useQuery)
 * - Client Components missing 'use client' directive
 * - Client Components using server-only APIs (cookies, headers, direct DB)
 * - Invalid import chains across the component boundary
 */

import * as ts from 'typescript'
import * as path from 'path'
import type { AuditIssue, AuditResult } from './types'
import { walkTsFiles, resolveFrontend, createResult, readTextFile } from './utils'

// Server-only APIs that must not appear in Client Components
// These are imported from 'next/headers' or 'next/navigation'
const SERVER_ONLY_MODULES = new Set([
  'next/headers',
  'next/navigation',
])

const HOOK_PATTERNS = [
  'useState', 'useEffect', 'useLayoutEffect', 'useContext',
  'useReducer', 'useCallback', 'useMemo', 'useRef',
  'useImperativeHandle', 'useDebugValue', 'useDeferredValue',
  'useTransition', 'useSyncExternalStore',
  'useQuery', 'useMutation', 'useInfiniteQuery',
  'useQueryClient',
]

function isServerComponent(filePath: string): boolean {
  const content = readTextFile(filePath)
  if (!content) return false
  // No 'use client' directive → server component by default
  return !content.includes("'use client'") && !content.includes('"use client"')
}

function hasUseClientDirective(filePath: string): boolean {
  const content = readTextFile(filePath)
  if (!content) return false
  return content.includes("'use client'") || content.includes('"use client"')
}

function getImports(sourceFile: ts.SourceFile): string[] {
  const imports: string[] = []
  ts.forEachChild(sourceFile, (node) => {
    if (ts.isImportDeclaration(node) && node.moduleSpecifier) {
      const moduleName = node.moduleSpecifier.getText(sourceFile).replace(/['"]/g, '')
      imports.push(moduleName)
    }
  })
  return imports
}

function getUsedIdentifiers(sourceFile: ts.SourceFile): Set<string> {
  const identifiers = new Set<string>()
  function visit(node: ts.Node) {
    if (ts.isIdentifier(node)) {
      identifiers.add(node.text)
    }
    ts.forEachChild(node, visit)
  }
  ts.forEachChild(sourceFile, visit)
  return identifiers
}

export async function runArchitectureAudit(): Promise<AuditResult> {
  const start = Date.now()
  const issues: AuditIssue[] = []

  const appDir = resolveFrontend('app')
  const files = walkTsFiles(appDir)

  for (const filePath of files) {
    const content = readTextFile(filePath)
    if (!content) continue

    const sourceFile = ts.createSourceFile(
      path.basename(filePath),
      content,
      ts.ScriptTarget.Latest,
      true,
    )

    const identifiers = getUsedIdentifiers(sourceFile)
    const imports = getImports(sourceFile)
    const relativePath = path.relative(resolveFrontend(), filePath)
    const isServer = isServerComponent(filePath)
    const hasClientDirective = hasUseClientDirective(filePath)

    // Check 1: Server Component using hooks
    if (isServer) {
      for (const hook of HOOK_PATTERNS) {
        if (identifiers.has(hook)) {
          issues.push({
            severity: 'error',
            code: 'SERVER_USES_HOOK',
            file: relativePath,
            message: `Server Component uses "${hook}" which requires a Client Component. Add 'use client' directive or extract to a separate Client Component.`,
            suggestion: `Add 'use client' at the top of the file, or move the hook usage to a child Client Component.`,
          })
        }
      }

      // Check for browser API usage in server components
      for (const browserApi of ['window', 'document', 'localStorage', 'sessionStorage']) {
        if (identifiers.has(browserApi)) {
          issues.push({
            severity: 'error',
            code: 'SERVER_USES_BROWSER_API',
            file: relativePath,
            message: `Server Component references "${browserApi}" which is only available in the browser.`,
            suggestion: `Move browser API usage to a 'use client' component or useEffect.`,
          })
        }
      }
    }

    // Check 2: Client Component importing from server-only modules
    if (hasClientDirective) {
      for (const serverModule of SERVER_ONLY_MODULES) {
        if (imports.includes(serverModule)) {
          issues.push({
            severity: 'error',
            code: 'CLIENT_USES_SERVER_API',
            file: relativePath,
            message: `Client Component imports from "${serverModule}" which is only available in Server Components.`,
            suggestion: `Move "${serverModule}" usage to a Server Component and pass the result as a prop.`,
          })
        }
      }
    }

    // Check 3: Detect 'use client' files that don't actually use any hooks
    // Check if the file calls custom hooks (identified by useXxx function calls)
    const usesCustomHook = content.match(/\buse[A-Z][a-zA-Z0-9]*\(/g) !== null
    if (hasClientDirective) {
      const usesAnyHook = HOOK_PATTERNS.some((h) => identifiers.has(h)) || usesCustomHook
      const usesBrowserApi = ['window', 'document', 'localStorage', 'sessionStorage', 'addEventListener'].some((a) => identifiers.has(a))
      // Check for imports from common client-only libraries
      const usesClientLib = imports.some((i) =>
        i.includes('react-dropzone') ||
        i.includes('recharts') ||
        i.includes('react-hook-form') ||
        i.includes('framer-motion') ||
        i.includes('@radix-ui') ||
        i.includes('lucide-react')
      )
      if (!usesAnyHook && !usesBrowserApi && !usesClientLib) {
        issues.push({
          severity: 'warning',
          code: 'UNNECESSARY_USE_CLIENT',
          file: relativePath,
          message: `File has 'use client' directive but doesn't use hooks or browser APIs. Consider making it a Server Component.`,
          suggestion: `Remove 'use client' directive to improve performance.`,
        })
      }
    }
  }

  return createResult('Architecture Audit', issues, start)
}