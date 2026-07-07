import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

const InvestmentSchema = z.object({
  id: z.number(),
  name: z.string(),
  investment_type: z.string(),
  platform: z.string().nullable(),
  invested_paise: z.number().int(),
  current_value_paise: z.number().int(),
  units: z.number().nullable(),
  buy_price_paise: z.number().int().nullable(),
  current_price_paise: z.number().int().nullable(),
  as_of_date: z.string().nullable(),
  is_active: z.boolean(),
  notes: z.string().nullable(),
  last_updated: z.string().optional(),
  created_at: z.string(),
})

const InvestmentSummarySchema = z.object({
  total_investments: z.number(),
  total_invested_paise: z.number().int(),
  total_current_value_paise: z.number().int(),
  total_gain_paise: z.number().int(),
  gain_percent: z.number(),
  allocation_by_type: z.record(z.string(), z.number().int()),
})

const InvestmentsResponseSchema = z.object({
  investments: z.array(InvestmentSchema),
  summary: InvestmentSummarySchema,
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
  const res = await fetch(`${API_BASE}/api/investments`)
  if (!res.ok) throw new Error('Failed to fetch investments')
  return InvestmentsResponseSchema.parse(await res.json())
}

async function createInvestment(input: CreateInvestmentInput) {
  const res = await fetch(`${API_BASE}/api/investments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to create investment')
  return res.json()
}

async function updateInvestment(id: string, input: Partial<CreateInvestmentInput>) {
  const res = await fetch(`${API_BASE}/api/investments/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to update investment')
  return res.json()
}

async function deleteInvestment(id: string) {
  const res = await fetch(`${API_BASE}/api/investments/${id}`, { method: 'DELETE' })
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