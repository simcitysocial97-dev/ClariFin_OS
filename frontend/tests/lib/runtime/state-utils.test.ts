/**
 * Tests for state utilities
 */

import { describe, it, expect } from 'vitest'
import {
  createLoading,
  createSuccess,
  createEmpty,
  createError,
  createOffline,
  createPermission,
  createStale,
  isTerminalState,
  isLoadingState,
  hasDataState,
} from '@/lib/runtime'

describe('state-utils', () => {
  describe('createLoading', () => {
    it('creates a loading state with no data', () => {
      const result = createLoading()
      expect(result.state).toBe('loading')
      expect(result.data).toBeUndefined()
      expect(result.error).toBeUndefined()
    })
  })

  describe('createSuccess', () => {
    it('creates a success state with data', () => {
      const data = { value: 100 }
      const result = createSuccess(data)
      expect(result.state).toBe('success')
      expect(result.data).toEqual(data)
    })
  })

  describe('createEmpty', () => {
    it('creates an empty state with title and description', () => {
      const result = createEmpty('No items', 'There are no items to display')
      expect(result.state).toBe('empty')
      expect(result.title).toBe('No items')
      expect(result.description).toBe('There are no items to display')
    })

    it('creates an empty state with action', () => {
      const onClick = () => {}
      const result = createEmpty('No items', 'Description', { label: 'Refresh', onClick })
      expect(result.state).toBe('empty')
      expect(result.retry).toBe(onClick)
    })
  })

  describe('createError', () => {
    it('creates an error state with error', () => {
      const error = new Error('Test error')
      const result = createError(error)
      expect(result.state).toBe('error')
      expect(result.error).toBe(error)
      expect(result.title).toBe('Something went wrong')
    })

    it('creates an error state with custom title', () => {
      const error = new Error('Test error')
      const result = createError(error, 'Custom error title')
      expect(result.title).toBe('Custom error title')
    })

    it('creates an error state with retry', () => {
      const error = new Error('Test error')
      const retry = () => {}
      const result = createError(error, undefined, retry)
      expect(result.retry).toBe(retry)
    })
  })

  describe('createOffline', () => {
    it('creates an offline state with defaults', () => {
      const result = createOffline()
      expect(result.state).toBe('offline')
      expect(result.title).toBe('You are offline')
      expect(result.description).toBe('Check your connection and try again')
    })

    it('creates an offline state with custom values', () => {
      const retry = () => {}
      const result = createOffline('Custom offline', 'Custom description', retry)
      expect(result.title).toBe('Custom offline')
      expect(result.description).toBe('Custom description')
      expect(result.retry).toBe(retry)
    })
  })

  describe('createPermission', () => {
    it('creates a permission state with defaults', () => {
      const result = createPermission()
      expect(result.state).toBe('permission')
      expect(result.title).toBe('Access denied')
    })

    it('creates a permission state with custom values', () => {
      const result = createPermission('Custom permission', 'Custom description')
      expect(result.title).toBe('Custom permission')
      expect(result.description).toBe('Custom description')
    })
  })

  describe('createStale', () => {
    it('creates a stale state with data and timestamp', () => {
      const data = { value: 100 }
      const result = createStale(data, 1234567890)
      expect(result.state).toBe('stale')
      expect(result.data).toEqual(data)
      expect(result.lastUpdated).toBe(1234567890)
    })
  })

  describe('isTerminalState', () => {
    it('returns true for error state', () => {
      expect(isTerminalState('error')).toBe(true)
    })

    it('returns true for offline state', () => {
      expect(isTerminalState('offline')).toBe(true)
    })

    it('returns true for permission state', () => {
      expect(isTerminalState('permission')).toBe(true)
    })

    it('returns false for loading state', () => {
      expect(isTerminalState('loading')).toBe(false)
    })

    it('returns false for success state', () => {
      expect(isTerminalState('success')).toBe(false)
    })

    it('returns false for empty state', () => {
      expect(isTerminalState('empty')).toBe(false)
    })

    it('returns false for stale state', () => {
      expect(isTerminalState('stale')).toBe(false)
    })
  })

  describe('isLoadingState', () => {
    it('returns true for loading state', () => {
      expect(isLoadingState('loading')).toBe(true)
    })

    it('returns true for stale state', () => {
      expect(isLoadingState('stale')).toBe(true)
    })

    it('returns false for success state', () => {
      expect(isLoadingState('success')).toBe(false)
    })

    it('returns false for error state', () => {
      expect(isLoadingState('error')).toBe(false)
    })
  })

  describe('hasDataState', () => {
    it('returns true for success state', () => {
      expect(hasDataState('success')).toBe(true)
    })

    it('returns true for stale state', () => {
      expect(hasDataState('stale')).toBe(true)
    })

    it('returns false for loading state', () => {
      expect(hasDataState('loading')).toBe(false)
    })

    it('returns false for empty state', () => {
      expect(hasDataState('empty')).toBe(false)
    })
  })
})