/**
 * Tests for React Query adapter
 */

import { describe, it, expect } from 'vitest'
import { fromQuery } from '@/lib/runtime'

// Mock UseQueryResult
function createMockQuery<T>(overrides: Partial<any> = {}): any {
  return {
    data: undefined,
    error: null,
    isLoading: false,
    isFetching: false,
    isError: false,
    dataUpdatedAt: 0,
    refetch: () => Promise.resolve(),
    ...overrides,
  }
}

describe('fromQuery adapter', () => {
  it('returns loading state when isLoading is true', () => {
    const query = createMockQuery({ isLoading: true })
    const result = fromQuery(query)
    expect(result.state).toBe('loading')
  })

  it('returns loading state when isFetching and no data', () => {
    const query = createMockQuery({ isFetching: true, data: undefined })
    const result = fromQuery(query)
    expect(result.state).toBe('loading')
  })

  it('returns error state when error exists', () => {
    const error = new Error('Test error')
    const query = createMockQuery({ error, isError: true })
    const result = fromQuery(query)
    expect(result.state).toBe('error')
    expect(result.error).toBe(error)
  })

  it('returns offline state for offline error', () => {
    const error = new Error('offline: no connection')
    const query = createMockQuery({ error, isError: true })
    const result = fromQuery(query)
    expect(result.state).toBe('offline')
  })

  it('returns stale state when fetching with data', () => {
    const query = createMockQuery({
      isFetching: true,
      data: { value: 100 },
      dataUpdatedAt: 1234567890,
    })
    const result = fromQuery(query)
    expect(result.state).toBe('stale')
    expect(result.data).toEqual({ value: 100 })
    expect(result.lastUpdated).toBe(1234567890)
  })

  it('returns success state when data exists', () => {
    const data = { value: 100 }
    const query = createMockQuery({ data })
    const result = fromQuery(query)
    expect(result.state).toBe('success')
    expect(result.data).toEqual(data)
  })

  it('returns empty state when isEmpty returns true', () => {
    const data = []
    const query = createMockQuery({ data })
    const result = fromQuery(query, { isEmpty: (d) => Array.isArray(d) && d.length === 0 })
    expect(result.state).toBe('empty')
  })

  it('returns success state when data exists and isEmpty returns false', () => {
    const data = [1, 2, 3]
    const query = createMockQuery({ data })
    const result = fromQuery(query, { isEmpty: (d) => Array.isArray(d) && d.length === 0 })
    expect(result.state).toBe('success')
  })

  it('returns loading state as default fallback', () => {
    const query = createMockQuery()
    const result = fromQuery(query)
    expect(result.state).toBe('loading')
  })
})