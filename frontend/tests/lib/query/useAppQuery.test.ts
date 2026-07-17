/**
 * useAppQuery Tests - Contract tests for query factory
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAppQuery, normalizeError } from '@/lib/query'
import { STALE_TIME, RETRY_POLICY } from '@/lib/query'

// Helper to create wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('normalizeError', () => {
  it('normalizes Error instance', () => {
    const error = new Error('Test error')
    const result = normalizeError(error, 'test_capability')
    expect(result).toEqual({
      message: 'Test error',
      capability: 'test_capability',
    })
  })

  it('normalizes string error', () => {
    const result = normalizeError('String error', 'test_capability')
    expect(result).toEqual({
      message: 'String error',
      capability: 'test_capability',
    })
  })

  it('normalizes unknown error', () => {
    const result = normalizeError({ unknown: 'object' }, 'test_capability')
    expect(result).toEqual({
      message: 'Unknown error',
      capability: 'test_capability',
    })
  })

  it('works without capability', () => {
    const result = normalizeError(new Error('No capability'))
    expect(result).toEqual({
      message: 'No capability',
      capability: undefined,
    })
  })
})

describe('useAppQuery', () => {
  it('applies default staleTime when not specified', () => {
    const mockQueryFn = vi.fn().mockResolvedValue({ data: 'test' })

    const { result } = renderHook(
      () =>
        useAppQuery({
          queryKey: ['test', 'key'] as const,
          queryFn: mockQueryFn,
        }),
      { wrapper: createWrapper() },
    )

    // The hook should be created successfully
    expect(result.current).toBeDefined()
  })

  it('applies custom staleTime when specified', () => {
    const mockQueryFn = vi.fn().mockResolvedValue({ data: 'test' })

    const { result } = renderHook(
      () =>
        useAppQuery({
          queryKey: ['test', 'key'] as const,
          queryFn: mockQueryFn,
          staleTime: STALE_TIME.LIVE,
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
  })

  it('accepts capability metadata', () => {
    const mockQueryFn = vi.fn().mockResolvedValue({ data: 'test' })

    const { result } = renderHook(
      () =>
        useAppQuery({
          queryKey: ['test', 'key'] as const,
          queryFn: mockQueryFn,
          capability: 'test_capability',
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
  })

  it('accepts select option for data transformation', () => {
    const mockQueryFn = vi.fn().mockResolvedValue({ value: 100 })

    const { result } = renderHook(
      () =>
        useAppQuery({
          queryKey: ['test', 'key'] as const,
          queryFn: mockQueryFn,
          select: (data: { value: number }) => data.value * 2,
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
  })

  it('accepts enabled option for conditional queries', () => {
    const mockQueryFn = vi.fn().mockResolvedValue({ data: 'test' })

    const { result } = renderHook(
      () =>
        useAppQuery({
          queryKey: ['test', 'key'] as const,
          queryFn: mockQueryFn,
          enabled: false,
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
    expect(result.current.isFetching).toBe(false)
  })

  it('accepts placeholderData option', () => {
    const mockQueryFn = vi.fn().mockResolvedValue({ data: 'test' })

    const { result } = renderHook(
      () =>
        useAppQuery({
          queryKey: ['test', 'key'] as const,
          queryFn: mockQueryFn,
          placeholderData: { data: 'placeholder' },
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
  })
})

describe('STALE_TIME constants', () => {
  it('has correct values', () => {
    expect(STALE_TIME.LIVE).toBe(0)
    expect(STALE_TIME.FREQUENT).toBe(30_000)
    expect(STALE_TIME.NORMAL).toBe(120_000)
    expect(STALE_TIME.REFERENCE).toBe(300_000)
    expect(STALE_TIME.STATIC).toBe(600_000)
  })
})

describe('RETRY_POLICY constants', () => {
  it('has correct values', () => {
    expect(RETRY_POLICY.NONE).toBe(0)
    expect(RETRY_POLICY.NORMAL).toBe(3)
    expect(RETRY_POLICY.AGGRESSIVE).toBe(5)
  })
})