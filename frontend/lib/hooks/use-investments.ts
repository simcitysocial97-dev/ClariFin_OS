import { useMutation, useQueryClient } from '@tanstack/react-query'

import { useAppQuery } from '@/lib/query'
import { queryKeys } from '@/lib/query'
import { STALE_TIME } from '@/lib/query'
import { InvestmentsResponseSchema } from '../contracts/api/investments'
import { mapInvestmentsToModel } from '../mappers/investments'
import type { InvestmentsModel } from '../models/investments'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

export type Investment = {
  id: number
  name: string
  investment_type: string
  platform: string | null
  invested_paise: number
  current_value_paise: number
  units: number | null
  buy_price_paise: number | null
  current_price_paise: number | null
  as_of_date: string | null
  is_active: boolean
  notes: string | null
  last_updated: string
  created_at: string
}

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

async function fetchInvestments(): Promise<InvestmentsModel> {
  const res = await fetch(`${API_BASE}/api/investments`)
  if (!res.ok) throw new Error('Failed to fetch investments')
  const dto = InvestmentsResponseSchema.parse(await res.json())
  return mapInvestmentsToModel(dto)
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
  return useAppQuery({
    queryKey: queryKeys.investments.list(),
    queryFn: fetchInvestments,
    capability: 'investments',
    staleTime: STALE_TIME.NORMAL,
  })
}

export function useCreateInvestment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createInvestment,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.investments.list() }),
  })
}

export function useUpdateInvestment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...input }: { id: string } & Partial<CreateInvestmentInput>) =>
      updateInvestment(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.investments.list() }),
  })
}

export function useDeleteInvestment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteInvestment,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.investments.list() }),
  })
}