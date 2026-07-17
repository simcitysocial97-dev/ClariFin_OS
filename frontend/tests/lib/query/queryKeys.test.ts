/**
 * Query Keys Tests - Contract tests for query key factory
 */

import { describe, it, expect } from 'vitest'
import { queryKeys } from '@/lib/query'

describe('queryKeys', () => {
  describe('networth', () => {
    it('returns readonly tuple for current', () => {
      const key = queryKeys.networth.current()
      expect(key).toEqual(['networth', 'current'])
      expect(Object.isFrozen(key)).toBe(true)
    })

    it('is deterministic - same input returns same key', () => {
      const key1 = queryKeys.networth.current()
      const key2 = queryKeys.networth.current()
      expect(key1).toEqual(key2)
    })
  })

  describe('accounts', () => {
    it('returns readonly tuple for managed', () => {
      const key = queryKeys.accounts.managed()
      expect(key).toEqual(['accounts', 'managed'])
    })

    it('returns readonly tuple for computed', () => {
      const key = queryKeys.accounts.computed()
      expect(key).toEqual(['accounts', 'computed'])
    })
  })

  describe('loans', () => {
    it('returns readonly tuple for list', () => {
      const key = queryKeys.loans.list()
      expect(key).toEqual(['loans', 'list'])
    })

    it('returns readonly tuple for schedule with id', () => {
      const key = queryKeys.loans.schedule('123')
      expect(key).toEqual(['loans', 'schedule', '123'])
    })

    it('returns readonly tuple for schedule with null', () => {
      const key = queryKeys.loans.schedule(null)
      expect(key).toEqual(['loans', 'schedule', null])
    })

    it('returns readonly tuple for prepayment', () => {
      const key = queryKeys.loans.prepayment('123', 10000, 'reduce_tenure')
      expect(key).toEqual(['loans', 'prepayment', '123', 10000, 'reduce_tenure'])
    })
  })

  describe('cards', () => {
    it('returns readonly tuple for list', () => {
      const key = queryKeys.cards.list()
      expect(key).toEqual(['cards', 'list'])
    })
  })

  describe('cashflow', () => {
    it('returns readonly tuple for monthly with default months', () => {
      const key = queryKeys.cashflow.monthly()
      expect(key).toEqual(['cashflow', 'monthly', 6])
    })

    it('returns readonly tuple for monthly with custom months', () => {
      const key = queryKeys.cashflow.monthly(12)
      expect(key).toEqual(['cashflow', 'monthly', 12])
    })
  })

  describe('reconciliation', () => {
    it('returns readonly tuple for pending', () => {
      const key = queryKeys.reconciliation.pending()
      expect(key).toEqual(['reconciliation', 'pending'])
    })

    it('returns readonly tuple for list', () => {
      const key = queryKeys.reconciliation.list()
      expect(key).toEqual(['reconciliation', 'list'])
    })

    it('returns readonly tuple for scan', () => {
      const key = queryKeys.reconciliation.scan()
      expect(key).toEqual(['reconciliation', 'scan'])
    })
  })

  describe('behavior', () => {
    it('returns readonly tuple for score', () => {
      const key = queryKeys.behavior.score()
      expect(key).toEqual(['behavior', 'score'])
    })

    it('returns readonly tuple for insights', () => {
      const key = queryKeys.behavior.insights()
      expect(key).toEqual(['behavior', 'insights'])
    })
  })

  describe('analytics', () => {
    it('returns readonly tuple for overview', () => {
      const key = queryKeys.analytics.overview()
      expect(key).toEqual(['analytics', 'overview'])
    })
  })

  describe('investments', () => {
    it('returns readonly tuple for list', () => {
      const key = queryKeys.investments.list()
      expect(key).toEqual(['investments', 'list'])
    })
  })

  describe('overview (legacy)', () => {
    it('returns readonly tuple with params', () => {
      const key = queryKeys.overview({ exclude_transfers: true })
      expect(key).toEqual(['overview', { exclude_transfers: true }])
    })

    it('returns readonly tuple without params', () => {
      const key = queryKeys.overview()
      expect(key).toEqual(['overview', undefined])
    })
  })
})