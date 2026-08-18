import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const LoanSchema = z.object({
  id: z.number(),
  name: z.string(),
  lender: z.string(),
  loan_type: z.string(),
  principal_paise: z.number().int(),
  outstanding_paise: z.number().int(),
  interest_rate: z.number(),
  tenure_months: z.number().int().nullable(),
  emi_paise: z.number().int().nullable(),
  disbursed_date: z.string(),
  next_emi_date: z.string().nullable(),
  gold_weight_grams: z.number().nullable(),
  gold_purity: z.string().nullable(),
  interest_type: z.string(),
  is_active: z.boolean(),
  notes: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

const LoanSummarySchema = z.object({
  total_loans: z.number(),
  total_outstanding_paise: z.number().int(),
  total_principal_paise: z.number().int(),
  total_monthly_emi_paise: z.number().int(),
})

const LoansResponseSchema = z.object({
  loans: z.array(LoanSchema),
  summary: LoanSummarySchema,
})

export type Loan = z.infer<typeof LoanSchema>

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

async function fetchLoans() {
  const res = await fetch(`${API_BASE}/api/loans`)
  if (!res.ok) throw new Error('Failed to fetch loans')
  
  // This is unverified raw payload from the network
  const raw = await res.json()
  
  // Intercept and parse data before passing it to frontend state loaders
  const parsed = LoansResponseSchema.safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Loans API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
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
    mutationFn: ({ id, ...input }: { id: string } & Partial<CreateLoanInput>) =>
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
