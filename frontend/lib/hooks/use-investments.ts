import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api/gateway';
import { z } from 'zod'


const InvestmentSchema = z.object({
  id: z.union([z.string(), z.number()]),
  name: z.string(),
  type: z.string(),
  institution: z.string(),
  current_value_paise: z.number().int(),
  invested_paise: z.number().int(),
  returns_paise: z.number().int(),
  returns_percentage: z.number(),
  returns_ytd_bps: z.number().int(),
  status: z.enum(['active', 'closed', 'matured']),
})

const InvestmentsResponseSchema = z.object({
  investments: z.array(InvestmentSchema),
  total_value_paise: z.number().int(),
  total_invested_paise: z.number().int(),
  total_returns_paise: z.number().int(),
  investment_count: z.number().int().nonnegative(),
  insights: z.array(z.record(z.string(), z.unknown())),
  evidence_chain: z.unknown().nullable(),
})

export type Investment = z.infer<typeof InvestmentSchema>

export interface CreateInvestmentInput {
  name: string
  investment_type: string
  invested_paise: number
  current_value_paise: number
  as_of_date: string
  platform?: string
  units?: number
  buy_price_paise?: number
  current_price_paise?: number
  notes?: string
}

async function fetchInvestments() {
  const res = await apiFetch(`/api/v1/investments`)
  if (!res.ok) throw new Error('Failed to fetch investments')
  
  // This is unverified raw payload from the network
  const raw = await res.json()
  
  // Intercept and parse data before passing it to frontend state loaders
  const parsed = InvestmentsResponseSchema.safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Investments API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
}

async function createInvestment(input: CreateInvestmentInput) {
  const res = await apiFetch(`/api/v1/investments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to create investment')
  return res.json()
}

async function updateInvestment(id: string, input: Partial<CreateInvestmentInput>) {
  const res = await apiFetch(`/api/v1/investments/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to update investment')
  return res.json()
}

async function deleteInvestment(id: string) {
  const res = await apiFetch(`/api/v1/investments/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete investment')
  return res.json()
}

export function useInvestments() {
  return useQuery({
    queryKey: ['investments'],
    queryFn: fetchInvestments,
    staleTime: 5 * 60 * 1000,
  })
}

export function useCreateInvestment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createInvestment,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['investments'] }),
  })
}

export function useUpdateInvestment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...input }: { id: string } & Partial<CreateInvestmentInput>) =>
      updateInvestment(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['investments'] }),
  })
}

export function useDeleteInvestment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteInvestment,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['investments'] }),
  })
}