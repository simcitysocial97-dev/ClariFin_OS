/**
 * useAppMutation Tests - Contract tests for mutation factory
 */

import { describe, it, expect, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAppMutation } from '@/lib/query'
import { queryKeys } from '@/lib/query'

// Helper to create wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      mutations: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useAppMutation', () => {
  it('creates mutation with mutationFn', () => {
    const mockMutationFn = vi.fn().mockResolvedValue({ success: true })

    const { result } = renderHook(
      () =>
        useAppMutation({
          mutationFn: mockMutationFn,
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
    expect(result.current.mutate).toBeDefined()
    expect(result.current.mutateAsync).toBeDefined()
  })

  it('accepts capability metadata', () => {
    const mockMutationFn = vi.fn().mockResolvedValue({ success: true })

    const { result } = renderHook(
      () =>
        useAppMutation({
          mutationFn: mockMutationFn,
          capability: 'test_capability',
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
  })

  it('accepts beforeMutate hook that can cancel mutation', async () => {
    const mockMutationFn = vi.fn().mockResolvedValue({ success: true })
    const beforeMutate = vi.fn().mockResolvedValue(false)

    const { result } = renderHook(
      () =>
        useAppMutation({
          mutationFn: mockMutationFn,
          beforeMutate,
        }),
      { wrapper: createWrapper() },
    )

    // Mutate should be defined
    expect(result.current.mutate).toBeDefined()
  })

  it('accepts beforeMutate hook that allows mutation', async () => {
    const mockMutationFn = vi.fn().mockResolvedValue({ success: true })
    const beforeMutate = vi.fn().mockResolvedValue(true)

    const { result } = renderHook(
      () =>
        useAppMutation({
          mutationFn: mockMutationFn,
          beforeMutate,
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
  })

  it('accepts invalidate option as array', () => {
    const mockMutationFn = vi.fn().mockResolvedValue({ success: true })

    const { result } = renderHook(
      () =>
        useAppMutation({
          mutationFn: mockMutationFn,
          invalidate: [queryKeys.accounts.managed()],
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
  })

  it('accepts invalidate option as function', () => {
    const mockMutationFn = vi.fn().mockResolvedValue({ success: true })

    const { result } = renderHook(
      () =>
        useAppMutation({
          mutationFn: mockMutationFn,
          invalidate: () => [queryKeys.accounts.managed()],
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
  })

  it('accepts onSuccess callback', () => {
    const mockMutationFn = vi.fn().mockResolvedValue({ success: true })
    const onSuccess = vi.fn()

    const { result } = renderHook(
      () =>
        useAppMutation({
          mutationFn: mockMutationFn,
          onSuccess,
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
  })

  it('accepts onError callback', () => {
    const mockMutationFn = vi.fn().mockRejectedValue(new Error('Test error'))
    const onError = vi.fn()

    const { result } = renderHook(
      () =>
        useAppMutation({
          mutationFn: mockMutationFn,
          onError,
        }),
      { wrapper: createWrapper() },
    )

    expect(result.current).toBeDefined()
  })
})