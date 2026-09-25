import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api/gateway';
import { z } from 'zod'


const LoanSchema = z.object({
  id: z.number(),
  name: z.string(),
  lender: z.string().nullable(),
  loan_type: z.string().nullable(),
  principal_paise: z.number().int(),
  rate_bps: z.number().int(),
  tenure_months: z.number().int(),
  emi_paise: z.number().int().nullable(),
  disbursed_date: z.string().nullable(),
  outstanding_paise: z.number().int().nullable(),
})

export type Loan = z.infer<typeof LoanSchema>

export interface CreateLoanInput {
  name: string
  lender: string
  loan_type: string
  principal_paise: number
  rate_bps: number
  tenure_months: number
  disbursed_date: string
  emi_paise?: number
  outstanding_paise?: number
}

export interface UpdateLoanInput {
  outstanding_paise?: number
  rate_bps?: number
  tenure_months?: number
  emi_paise?: number
  notes?: string
}

async function fetchLoans() {
  const res = await apiFetch(`/api/v1/loans`)
  if (!res.ok) throw new Error('Failed to fetch loans')
  
  // This is unverified raw payload from the network
  const raw = await res.json()
  
  // Intercept and parse data before passing it to frontend state loaders
  const parsed = z.array(LoanSchema).safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Loans API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
}

async function fetchLoanSchedule(loanId: string) {
  const res = await apiFetch(`/api/v1/loans/${loanId}/schedule`)
  if (!res.ok) throw new Error('Failed to fetch schedule')
  return res.json()
}

async function simulatePrepayment(
  loanId: string,
  prepaymentPaise: number,
  mode: 'reduce_tenure' | 'reduce_emi'
) {
  const res = await apiFetch(`/api/v1/loans/${loanId}/prepayment-simulation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount_paise: prepaymentPaise, mode }),
  })
  if (!res.ok) throw new Error('Failed to simulate prepayment')
  return res.json()
}

async function createLoan(input: CreateLoanInput) {
  const res = await apiFetch(`/api/v1/loans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to create loan')
  return res.json()
}

async function updateLoan(id: string, input: UpdateLoanInput) {
  const res = await apiFetch(`/api/v1/loans/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to update loan')
  return res.json()
}

async function deleteLoan(id: string) {
  const res = await apiFetch(`/api/v1/loans/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete loan')
  return res.json()
}

export function useLoans() {
  return useQuery({
    queryKey: ['loans'],
    queryFn: fetchLoans,
    staleTime: 5 * 60 * 1000,
  })
}

export function useLoanSchedule(loanId: string | null) {
  return useQuery({
    queryKey: ['loans', loanId, 'schedule'],
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
    queryKey: ['loans', loanId, 'prepayment', prepaymentPaise, mode],
    queryFn: () => simulatePrepayment(loanId!, prepaymentPaise, mode),
    enabled: !!loanId && prepaymentPaise > 0,
    staleTime: 0,
  })
}

export function useCreateLoan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createLoan,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['loans'] }),
  })
}

export function useUpdateLoan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...input }: { id: string } & UpdateLoanInput) =>
      updateLoan(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['loans'] }),
  })
}

export function useDeleteLoan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteLoan,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['loans'] }),
  })
}
