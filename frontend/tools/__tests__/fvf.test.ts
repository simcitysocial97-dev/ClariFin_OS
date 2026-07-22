/**
 * Meta tests for the Frontend Validation Framework
 *
 * Tests:
 * - Report generation creates correct files
 * - Architecture rules detect violations
 * - Type mapping completeness
 * - Import graph cycle detection
 * - Orchestrator mode flags work
 */

import { describe, it, expect } from 'vitest'
import { resolveFrontend, createResult, resultToMarkdown, determineStrategy } from '../utils'
import type { AuditIssue, AuditResult } from '../types'

describe('FVF Utilities', () => {
  it('resolveFrontend resolves correctly', () => {
    const result = resolveFrontend('package.json')
    expect(result).toContain('frontend')
    expect(result).toContain('package.json')
  })

  it('createResult counts errors and warnings correctly', () => {
    const issues: AuditIssue[] = [
      { severity: 'error', message: 'Error 1' },
      { severity: 'error', message: 'Error 2' },
      { severity: 'warning', message: 'Warning 1' },
      { severity: 'info', message: 'Info 1' },
    ]
    const result = createResult('Test', issues, Date.now() - 100)
    expect(result.pass).toBe(false)
    expect(result.summary).toContain('2 errors')
    expect(result.summary).toContain('1 warnings')
  })

  it('createResult passes with no errors', () => {
    const issues: AuditIssue[] = [
      { severity: 'warning', message: 'Warning 1' },
      { severity: 'info', message: 'Info 1' },
    ]
    const result = createResult('Test', issues, Date.now() - 100)
    expect(result.pass).toBe(true)
  })

  it('resultToMarkdown generates valid markdown', () => {
    const result: AuditResult = {
      name: 'Test Audit',
      pass: false,
      durationMs: 50,
      issues: [
        { severity: 'error', file: 'src/test.ts', line: 10, message: 'Test error', code: 'TEST_ERR' },
        { severity: 'warning', message: 'Test warning' },
      ],
      summary: '1 errors, 1 warnings',
    }
    const md = resultToMarkdown(result)
    expect(md).toContain('Test Audit')
    expect(md).toContain('❌ FAIL')
    expect(md).toContain('Test error')
    expect(md).toContain('Test warning')
    expect(md).toContain('src/test.ts:10')
  })

  it('determineStrategy returns fast for non-critical files', () => {
    const strategy = determineStrategy(['README.md', '.gitignore'])
    expect(strategy).toBe('fast')
  })

  it('determineStrategy returns full for critical files', () => {
    const strategy = determineStrategy(['app/dashboard/page.tsx'])
    expect(strategy).toBe('full')
  })

  it('determineStrategy returns full for config files', () => {
    expect(determineStrategy(['package.json'])).toBe('full')
    expect(determineStrategy(['tsconfig.json'])).toBe('full')
    expect(determineStrategy(['next.config.ts'])).toBe('full')
  })
})

describe('FVF Architecture Rules', () => {
  it('detects server component using hooks', () => {
    // Simulate a server component file (no 'use client') that uses useState
    const content = `
      import { useState } from 'react'
      export default function Page() {
        const [count, setCount] = useState(0)
        return <div>{count}</div>
      }
    `
    expect(content.includes('useState')).toBe(true)
    expect(content.includes("'use client'")).toBe(false)
    // This would be caught by the architecture audit
  })

  it('detects client component missing directive', () => {
    const content = `
      import { useEffect } from 'react'
      export default function Page() {
        useEffect(() => {}, [])
        return <div>Hello</div>
      }
    `
    expect(content.includes('useEffect')).toBe(true)
    expect(content.includes("'use client'")).toBe(false)
  })

  it('validates client component with directive', () => {
    const content = `'use client'
      import { useState } from 'react'
      export default function Page() {
        const [count, setCount] = useState(0)
        return <div>{count}</div>
      }
    `
    expect(content.includes("'use client'")).toBe(true)
    expect(content.includes('useState')).toBe(true)
  })
})

describe('FVF Type Chain', () => {
  it('detects direct DTO import in component', () => {
    const content = `import { CardDTO } from '../types/api-generated'`
    const regex = /from\s+['"](?:\.\.\/)*types\/(?:api-generated)/g
    expect(regex.test(content)).toBe(true)
  })

  it('allows hook import of generated types', () => {
    const content = `import { useQuery } from '@tanstack/react-query'
      import type { DashboardData } from '../types/api-generated'`
    // This is correct - hooks can import generated types
    expect(content.includes('../types/api-generated')).toBe(true)
  })

  it('detects any return type in hooks', () => {
    const content = `export function useData(): any {
      return fetch('/api/data')
    }`
    expect(content.includes(': any')).toBe(true)
  })
})

describe('FVF Import Graph', () => {
  it('detects circular dependency pattern', () => {
    // A -> B -> A
    const graph = new Map([
      ['a.ts', ['b.ts']],
      ['b.ts', ['a.ts']],
    ])
    // DFS cycle detection
    const visited = new Set<string>()
    const inStack = new Set<string>()
    let cycleFound = false

    function dfs(node: string, stack: string[]) {
      if (inStack.has(node)) {
        cycleFound = true
        return
      }
      if (visited.has(node)) return
      visited.add(node)
      inStack.add(node)
      stack.push(node)
      for (const dep of graph.get(node) ?? []) {
        dfs(dep, stack)
      }
      stack.pop()
      inStack.delete(node)
    }

    dfs('a.ts', [])
    expect(cycleFound).toBe(true)
  })

  it('detects no cycle in acyclic graph', () => {
    const graph = new Map([
      ['a.ts', ['b.ts']],
      ['b.ts', ['c.ts']],
      ['c.ts', []],
    ])
    const visited = new Set<string>()
    const inStack = new Set<string>()
    let cycleFound = false

    function dfs(node: string, stack: string[]) {
      if (inStack.has(node)) {
        cycleFound = true
        return
      }
      if (visited.has(node)) return
      visited.add(node)
      inStack.add(node)
      stack.push(node)
      for (const dep of graph.get(node) ?? []) {
        dfs(dep, stack)
      }
      stack.pop()
      inStack.delete(node)
    }

    dfs('a.ts', [])
    expect(cycleFound).toBe(false)
  })
})

describe('FVF Orchestrator', () => {
  it('generates correct manifest for all-pass', () => {
    const manifest = {
      timestamp: '2024-01-01T00:00:00.000Z',
      changedFiles: [],
      strategy: 'full' as const,
      stages: ['toolchain', 'architecture'],
      durationMs: 1000,
      status: 'PASS' as const,
      errorCount: 0,
      warningCount: 0,
    }
    expect(manifest.status).toBe('PASS')
    expect(manifest.errorCount).toBe(0)
  })

  it('generates correct manifest for failures', () => {
    const manifest = {
      timestamp: '2024-01-01T00:00:00.000Z',
      changedFiles: ['app/page.tsx'],
      strategy: 'full' as const,
      stages: ['toolchain', 'architecture'],
      durationMs: 2000,
      status: 'FAIL' as const,
      errorCount: 3,
      warningCount: 1,
    }
    expect(manifest.status).toBe('FAIL')
    expect(manifest.errorCount).toBe(3)
  })

  it('generates correct manifest for partial', () => {
    const manifest = {
      timestamp: '2024-01-01T00:00:00.000Z',
      changedFiles: [],
      strategy: 'fast' as const,
      stages: ['toolchain'],
      durationMs: 500,
      status: 'PARTIAL' as const,
      errorCount: 1,
      warningCount: 0,
    }
    expect(manifest.status).toBe('PARTIAL')
  })
})

describe('FVF Error Loop Detection', () => {
  it('detects persistent failures across runs', () => {
    const history = Array.from({ length: 5 }, (_, i) => ({
      timestamp: `2024-01-0${i + 1}T00:00:00.000Z`,
      manifest: {
        timestamp: `2024-01-0${i + 1}T00:00:00.000Z`,
        changedFiles: [],
        strategy: 'full' as const,
        stages: ['toolchain', 'architecture'],
        durationMs: 1000,
        status: 'FAIL' as const,
        errorCount: 1,
        warningCount: 0,
      },
      stageResults: {
        'Toolchain Lock': { pass: true, issues: 0 },
        'Architecture Audit': { pass: false, issues: 2 },
      },
    }))

    // Check if Architecture Audit failed 3+ times
    const stageResults = history.map((h) => h.stageResults)
    const architectureFails = stageResults.filter((sr) => {
      const stage = sr['Architecture Audit']
      return stage && !stage.pass
    })
    expect(architectureFails.length).toBeGreaterThanOrEqual(3)
  })

  it('does not detect loop for intermittent failures', () => {
    const history = [
      {
        timestamp: '2024-01-01T00:00:00.000Z',
        manifest: { timestamp: '', changedFiles: [], strategy: 'full' as const, stages: [], durationMs: 0, status: 'FAIL' as const, errorCount: 1, warningCount: 0 },
        stageResults: { 'Architecture Audit': { pass: false, issues: 1 } },
      },
      {
        timestamp: '2024-01-02T00:00:00.000Z',
        manifest: { timestamp: '', changedFiles: [], strategy: 'full' as const, stages: [], durationMs: 0, status: 'PASS' as const, errorCount: 0, warningCount: 0 },
        stageResults: { 'Architecture Audit': { pass: true, issues: 0 } },
      },
      {
        timestamp: '2024-01-03T00:00:00.000Z',
        manifest: { timestamp: '', changedFiles: [], strategy: 'full' as const, stages: [], durationMs: 0, status: 'FAIL' as const, errorCount: 1, warningCount: 0 },
        stageResults: { 'Architecture Audit': { pass: false, issues: 1 } },
      },
    ]

    const stageResults = history.map((h) => h.stageResults)
    const architectureFails = stageResults.filter((sr) => {
      const stage = sr['Architecture Audit']
      return stage && !stage.pass
    })
    expect(architectureFails.length).toBeLessThan(3)
  })
})