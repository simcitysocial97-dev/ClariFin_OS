import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useCallback } from 'react'
import { DashboardMetricsSchema, type DashboardMetrics } from '@/lib/schemas/dashboard-metrics'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface HookState<T> {
  data: T | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
  dataUpdatedAt: number
}

// 🛡️ Data fetching function utilizing Zod runtime parsing
async function fetchDashboardSummary(): Promise<DashboardMetrics> {
  const res = await fetch(`${API_BASE}/api/dashboard/summary`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  
  // This is unverified raw payload from the network
  const raw = await res.json()
  
  // Intercept and parse data before passing it to frontend state loaders
  const parsed = DashboardMetricsSchema.safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Dashboard metrics API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
}

export function useDashboardMetrics(): HookState<DashboardMetrics> {
  const queryClient = useQueryClient()
  
  const result = useQuery<DashboardMetrics, Error>({
    queryKey: ['dashboard', 'summary'],
    queryFn: fetchDashboardSummary,
    staleTime: 30_000,
  })

  const refetch = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ['dashboard', 'summary'] })
  }, [queryClient])

  return useMemo(() => ({
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    refetch,
    dataUpdatedAt: result.dataUpdatedAt,
  }), [result, refetch])
}
