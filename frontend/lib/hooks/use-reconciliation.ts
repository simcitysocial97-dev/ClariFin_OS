import type { HookState } from './use-async-query';
import { useAsyncQuery } from './use-async-query'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { mapReconciliationToModel } from '../mappers/reconciliation'
import type { ReconciliationModel } from '../models/reconciliation'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Types based on /api/reconciliations response
export interface TransactionDetail {
  id: number
  date: string
  date_iso: string
  description: string
  amount_paise: number
  type: 'debit' | 'credit'
  bank: string
}

export interface ReconciliationMatch {
  id: number
  debit_txn_id: number
  credit_txn_id: number
  debit_account_id: string
  credit_account_id: string
  amount: number  // in rupees
  date_diff_days: number
  match_confidence: number  // 0.0-1.0
  match_type: 'exact' | 'window' | 'fuzzy' | 'manual'
  status: 'pending' | 'confirmed' | 'rejected'
  created_at: string
  confirmed_at: string | null
  // Transaction details from join
  debit_date: string
  debit_date_iso: string
  debit_description: string
  debit_amount_paise: number
  debit_bank: string
  credit_date: string
  credit_date_iso: string
  credit_description: string
  credit_amount_paise: number
  credit_bank: string
}

export interface ReconciliationsData {
  reconciliations: ReconciliationMatch[]
}

async function fetchReconciliations(): Promise<ReconciliationsData> {
  const response = await fetch(`${API_BASE}/api/reconciliations`)
  if (!response.ok) throw new Error(`Reconciliations fetch failed: ${response.status}`)
  return response.json()
}

async function fetchPendingReconciliations(): Promise<ReconciliationsData> {
  const response = await fetch(`${API_BASE}/api/reconciliations/pending`)
  if (!response.ok) throw new Error(`Pending reconciliations fetch failed: ${response.status}`)
  return response.json()
}

async function fetchScanReconciliations(): Promise<ReconciliationModel> {
  const response = await fetch(`${API_BASE}/api/reconciliations/scan`)
  if (!response.ok) throw new Error(`Scan reconciliations failed: ${response.status}`)
  const dto = await response.json()
  return mapReconciliationToModel(dto)
}

async function confirmReconciliation(id: number): Promise<{ success: boolean; status: string }> {
  const response = await fetch(`${API_BASE}/api/reconciliations/${id}/confirm`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Confirm reconciliation failed: ${response.status}`)
  return response.json()
}

async function rejectReconciliation(id: number): Promise<{ success: boolean; status: string }> {
  const response = await fetch(`${API_BASE}/api/reconciliations/${id}/reject`, {
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

export function useScanReconciliations(): HookState<ReconciliationModel> {
  return useAsyncQuery(
    ['reconciliations', 'scan'],
    fetchScanReconciliations
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