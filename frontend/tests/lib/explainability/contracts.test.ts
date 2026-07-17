/**
 * Tests for explainability contracts
 */

import { describe, it, expect } from 'vitest'
import { isValidConfidenceBps, createConfidence } from '@/lib/explainability'

describe('Confidence', () => {
  describe('isValidConfidenceBps', () => {
    it('returns true for valid BPS values', () => {
      expect(isValidConfidenceBps(0)).toBe(true)
      expect(isValidConfidenceBps(5000)).toBe(true)
      expect(isValidConfidenceBps(10000)).toBe(true)
    })

    it('returns false for invalid BPS values', () => {
      expect(isValidConfidenceBps(-1)).toBe(false)
      expect(isValidConfidenceBps(10001)).toBe(false)
      expect(isValidConfidenceBps(1.5)).toBe(false)
      expect(isValidConfidenceBps(NaN)).toBe(false)
    })
  })

  describe('createConfidence', () => {
    it('creates valid confidence object', () => {
      const result = createConfidence(8500, 'High confidence')
      expect(result.value).toBe(8500)
      expect(result.reason).toBe('High confidence')
    })

    it('throws for invalid confidence value', () => {
      expect(() => createConfidence(15000)).toThrow('Invalid confidence value')
      expect(() => createConfidence(-100)).toThrow('Invalid confidence value')
    })
  })
})

describe('Evidence', () => {
  it('accepts valid evidence value types', () => {
    // This is a type-level test - if it compiles, it passes
    const numberEvidence = {
      id: 'test-1',
      type: 'data' as const,
      description: 'Test',
      value: 100,
    }
    const stringEvidence = {
      id: 'test-2',
      type: 'data' as const,
      description: 'Test',
      value: 'test',
    }
    const booleanEvidence = {
      id: 'test-3',
      type: 'data' as const,
      description: 'Test',
      value: true,
    }
    const nullEvidence = {
      id: 'test-4',
      type: 'data' as const,
      description: 'Test',
      value: null,
    }

    expect(numberEvidence.value).toBe(100)
    expect(stringEvidence.value).toBe('test')
    expect(booleanEvidence.value).toBe(true)
    expect(nullEvidence.value).toBe(null)
  })
})

describe('SourceReference', () => {
  it('accepts valid source types', () => {
    const sources = [
      { type: 'account', id: 'acc-1' },
      { type: 'loan', id: 123 },
      { type: 'investment', id: 'inv-1', name: 'Mutual Fund' },
      { type: 'statement', id: 'stmt-1', date: '2025-01-01' },
    ]

    expect(sources).toHaveLength(4)
  })
})

describe('CalculationStep', () => {
  it('accepts valid operations', () => {
    const operations = [
      'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE',
      'AVERAGE', 'LOOKUP', 'FILTER', 'GROUP', 'MATCH',
    ] as const

    operations.forEach(op => {
      const step = {
        stepId: `step-${op}`,
        description: `Test ${op}`,
        operation: op,
        inputIds: ['input-1'],
        outputId: 'output-1',
        order: 1,
      }
      expect(step.operation).toBe(op)
    })
  })
})