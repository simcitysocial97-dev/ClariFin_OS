/**
 * Tests for explainability utilities
 */

import { describe, it, expect } from 'vitest'
import { mergeEvidence, sortEvidence, confidenceToBadge, groupEvidence } from '@/lib/explainability'
import type { Evidence } from '@/lib/explainability'

describe('mergeEvidence', () => {
  it('merges multiple evidence arrays', () => {
    const e1: Evidence[] = [
      { id: 'a', type: 'data', description: 'A', value: 100 },
    ]
    const e2: Evidence[] = [
      { id: 'b', type: 'data', description: 'B', value: 200 },
    ]
    const e3: Evidence[] = [
      { id: 'c', type: 'data', description: 'C', value: 300 },
    ]

    const result = mergeEvidence(e1, e2, e3)
    expect(result).toHaveLength(3)
  })

  it('deduplicates by id', () => {
    const e1: Evidence[] = [
      { id: 'a', type: 'data', description: 'A', value: 100 },
    ]
    const e2: Evidence[] = [
      { id: 'a', type: 'data', description: 'A duplicate', value: 200 },
      { id: 'b', type: 'data', description: 'B', value: 200 },
    ]

    const result = mergeEvidence(e1, e2)
    expect(result).toHaveLength(2)
    expect(result[0].id).toBe('a')
    expect(result[0].value).toBe(100) // First one wins
  })
})

describe('sortEvidence', () => {
  it('sorts by type priority', () => {
    const evidence: Evidence[] = [
      { id: '1', type: 'source', description: 'Source', value: null },
      { id: '2', type: 'calculation', description: 'Calc', value: 100 },
      { id: '3', type: 'data', description: 'Data', value: 200 },
    ]

    const result = sortEvidence(evidence)
    expect(result[0].type).toBe('calculation')
    expect(result[1].type).toBe('data')
    expect(result[2].type).toBe('source')
  })

  it('returns a new array (immutable)', () => {
    const evidence: Evidence[] = [
      { id: '1', type: 'data', description: 'A', value: 100 },
    ]

    const result = sortEvidence(evidence)
    expect(result).not.toBe(evidence)
  })
})

describe('confidenceToBadge', () => {
  it('returns low for 0-3300', () => {
    expect(confidenceToBadge(0)).toBe('low')
    expect(confidenceToBadge(1000)).toBe('low')
    expect(confidenceToBadge(3300)).toBe('low')
  })

  it('returns medium for 3301-6600', () => {
    expect(confidenceToBadge(3301)).toBe('medium')
    expect(confidenceToBadge(5000)).toBe('medium')
    expect(confidenceToBadge(6600)).toBe('medium')
  })

  it('returns high for 6601-10000', () => {
    expect(confidenceToBadge(6601)).toBe('high')
    expect(confidenceToBadge(8500)).toBe('high')
    expect(confidenceToBadge(10000)).toBe('high')
  })
})

describe('groupEvidence', () => {
  it('groups evidence by type', () => {
    const evidence: Evidence[] = [
      { id: '1', type: 'data', description: 'Data', value: 100 },
      { id: '2', type: 'calculation', description: 'Calc', value: 200 },
      { id: '3', type: 'data', description: 'Data2', value: 300 },
      { id: '4', type: 'source', description: 'Source', value: null },
    ]

    const result = groupEvidence(evidence)
    expect(result.data).toHaveLength(2)
    expect(result.calculation).toHaveLength(1)
    expect(result.source).toHaveLength(1)
  })
})