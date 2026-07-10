import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

const NetWorthSchema = z.object({
  net_worth_paise: z.number().int(),
  assets: z.object({
    total_paise: z.number().int(),
    accounts_paise: z.number().int(),
    investments_paise: z.number().int(),
    account_count: z.number(),
    investment_count: z.number(),
  }),
  liabilities: z.object({
    total_paise: z.number().int(),
    loans_paise: z.number().int(),
    cards_paise: z.number().int(),
    loan_count: z.number(),
    card_count: z.number(),
  }),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
})

export type NetWorth = z.infer<typeof NetWorthSchema>

async function fetchNetWorth() {
  const res = await fetch(`${API_BASE}/api/networth`)
  if (!res.ok) throw new Error('Failed to fetch net worth')
  return NetWorthSchema.parse(await res.json())
}

export function useNetWorth() {
  return useQuery({
    queryKey: ['networth'],
    queryFn: fetchNetWorth,
    staleTime: 2 * 60 * 1000,
  })
}