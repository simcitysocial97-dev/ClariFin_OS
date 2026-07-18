import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { useAppQuery } from '@/lib/query'
import { queryKeys } from '@/lib/query'
import { STALE_TIME } from '@/lib/query'
import { LoansResponseSchema } from '../contracts/api/loans'
import { mapLoansToModel } from '../mappers/loans'
import type { LoansModel } from '../models/loans'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Types based on /api/loans response
export interface Loan {
  id: number
  name: string
  lender: string
  loan_type: string
  principal_paise: number
  outstanding_paise: number
  interest_rate: number
  tenure_months: number | null
  emi_paise: number | null
  disbursed_date: string
  next_emi_date: string | null
  gold_weight_grams: number | null
  gold_purity: string | null
  interest_type: string
  is_active: boolean
  notes: string | null
  created_at: string
  updated_at: string
}

export interface CreateLoanInput {
  name: string
  lender: string
  loan_type: string
  principal_paise: number
  outstanding_paise: number
  interest_rate: number
  disbursed_date: string
  tenure_months?: number
  emi_paise?: number
  next_emi_date?: string
  gold_weight_grams?: number
  gold_purity?: string
  interest_type?: string
  notes?: string
}

async function fetchLoans(): Promise<LoansModel> {
  const res = await fetch(`${API_BASE}/api/loans`)
  if (!res.ok) throw new Error('Failed to fetch loans')
  const dto = LoansResponseSchema.parse(await res.json())
  return mapLoansToModel(dto)
}

async function fetchLoanSchedule(loanId: string) {
  const res = await fetch(`${API_BASE}/api/loans/${loanId}/schedule`)
  if (!res.ok) throw new Error('Failed to fetch schedule')
  return res.json()
}

async function simulatePrepayment(
  loanId: string,
  prepaymentPaise: number,
  mode: 'reduce_tenure' | 'reduce_emi'
) {
  const res = await fetch(`${API_BASE}/api/loans/${loanId}/prepayment-simulation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prepayment_paise: prepaymentPaise, mode }),
  })
  if (!res.ok) throw new Error('Failed to simulate prepayment')
  return res.json()
}

async function createLoan(input: CreateLoanInput) {
  const res = await fetch(`${API_BASE}/api/loans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to create loan')
  return res.json()
}

async function updateLoan(id: string, input: Partial<CreateLoanInput>) {
  const res = await fetch(`${API_BASE}/api/loans/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to update loan')
  return res.json()
}

async function deleteLoan(id: string) {
  const res = await fetch(`${API_BASE}/api/loans/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete loan')
  return res.json()
}

export function useLoans() {
  return useAppQuery({
    queryKey: queryKeys.loans.list(),
    queryFn: fetchLoans,
    capability: 'loans',
    staleTime: STALE_TIME.NORMAL,
  })
}

export function useLoanSchedule(loanId: string | null) {
  return useQuery({
    queryKey: queryKeys.loans.schedule(loanId),
    queryFn: () => fetchLoanSchedule(loanId!),
    enabled: !!loanId,
    staleTime: 10 * 60 * 1000,
  })
}

export function usePrepaymentSimulation(
  loanId: string | null,
  prepaymentPaise: number,
  mode: 'reduce_tenure' | 'reduce_emi'
) {
  return useQuery({
    queryKey: queryKeys.loans.prepayment(loanId, prepaymentPaise, mode),
    queryFn: () => simulatePrepayment(loanId!, prepaymentPaise, mode),
    enabled: !!loanId && prepaymentPaise > 0,
    staleTime: 0,
  })
}

export function useCreateLoan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createLoan,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.loans.list() }),
  })
}

export function useUpdateLoan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...input }: { id: string } & Partial<CreateLoanInput>) =>
      updateLoan(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.loans.list() }),
  })
}

export function useDeleteLoan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteLoan,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.loans.list() }),
  })
}