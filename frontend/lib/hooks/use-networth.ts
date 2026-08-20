import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api/gateway';
import { z } from 'zod'


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
  const res = await apiFetch(`/api/networth`)
  if (!res.ok) throw new Error('Failed to fetch net worth')
  
  // This is unverified raw payload from the network
  const raw = await res.json()
  
  // Intercept and parse data before passing it to frontend state loaders
  const parsed = NetWorthSchema.safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Net worth API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
}

export function useNetWorth() {
  return useQuery({
    queryKey: ['networth'],
    queryFn: fetchNetWorth,
    staleTime: 2 * 60 * 1000,
  })
}