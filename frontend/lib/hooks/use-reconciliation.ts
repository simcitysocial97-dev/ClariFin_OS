import type { HookState } from './use-async-query';
import { apiFetch } from '@/lib/api/gateway';
import { useAsyncQuery } from './use-async-query'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ReconciliationsDataSchema, type ReconciliationsData, type ReconciliationMatch, type TransactionDetail } from '@/lib/schemas/reconciliation'


// 🛡️ Data fetching function utilizing Zod runtime parsing
async function fetchReconciliations(): Promise<ReconciliationsData> {
  const response = await apiFetch(`/api/reconciliation`)
  if (!response.ok) throw new Error(`Reconciliations fetch failed: ${response.status}`)

  // This is unverified raw payload from the network
  const raw = await response.json()

  // Intercept and parse data before passing it to frontend state loaders
  const parsed = ReconciliationsDataSchema.safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Reconciliations API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
}

async function fetchPendingReconciliations(): Promise<ReconciliationsData> {
  const response = await apiFetch(`/api/reconciliation/pending`)
  if (!response.ok) throw new Error(`Pending reconciliations fetch failed: ${response.status}`)

  const raw = await response.json()

  const parsed = ReconciliationsDataSchema.safeParse(raw)
  
  if (!parsed.success) {
    console.error('❌ Pending reconciliations API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
}

async function scanReconciliations(): Promise<{ matches: ReconciliationMatch[]; count: number }> {
  const response = await apiFetch(`/api/reconciliation/scan`)
  if (!response.ok) throw new Error(`Scan reconciliations failed: ${response.status}`)

  const raw = await response.json()

  const matches = (raw.matches || []) as ReconciliationMatch[]

  return { matches, count: raw.count }
}

async function confirmReconciliation(id: number): Promise<{ success: boolean; status: string }> {
  const response = await apiFetch(`/api/reconciliation/${id}/confirm`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Confirm reconciliation failed: ${response.status}`)
  return response.json()
}

async function rejectReconciliation(id: number): Promise<{ success: boolean; status: string }> {
  const response = await apiFetch(`/api/reconciliation/${id}/reject`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Reject reconciliation failed: ${response.status}`)
  return response.json()
}

export function useReconciliations(): HookState<ReconciliationsData> {
  return useAsyncQuery(
    ['reconciliations'],
    fetchReconciliations
  )
}

export function usePendingReconciliations(): HookState<ReconciliationsData> {
  return useAsyncQuery(
    ['reconciliations', 'pending'],
    fetchPendingReconciliations
  )
}

export function useScanReconciliations(): HookState<{ matches: ReconciliationMatch[]; count: number }> {
  return useAsyncQuery(
    ['reconciliations', 'scan'],
    scanReconciliations
  )
}

export function useConfirmReconciliation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: confirmReconciliation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliations'] })
    },
  })
}

export function useRejectReconciliation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: rejectReconciliation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliations'] })
    },
  })
}

// Re-export types for backward compatibility
export type { ReconciliationsData, ReconciliationMatch, TransactionDetail }
