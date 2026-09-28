import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api/gateway';
import { z } from 'zod'


const NetWorthBreakdownItemSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.string(),
  balance_paise: z.number().int(),
  percentage: z.number(),
  contribution_paise: z.number().int(),
})

const NetWorthSchema = z.object({
  total_net_worth_paise: z.number().int(),
  total_assets_paise: z.number().int(),
  total_liabilities_paise: z.number().int(),
  composition: z.object({
    total_assets_paise: z.number().int(),
    total_liabilities_paise: z.number().int(),
    asset_breakdown: z.array(NetWorthBreakdownItemSchema),
    liability_breakdown: z.array(NetWorthBreakdownItemSchema),
  }),
  trend: z.object({
    direction: z.enum(['up', 'down', 'flat']),
    percentage_change: z.number(),
    period: z.string(),
  }).nullable().optional(),
  insights: z.array(z.object({
    type: z.enum(['positive', 'warning', 'info', 'alert']),
    severity: z.enum(['low', 'medium', 'high']),
    message: z.string(),
    action_url: z.string().optional(),
  })),
  evidence_chain: z.object({
    summary: z.string(),
    evidence: z.array(z.object({
      type: z.string(),
      summary: z.string(),
      source: z.string(),
      confidence: z.number().optional(),
    })),
    calculation_steps: z.array(z.object({
      name: z.string(),
      description: z.string(),
      inputs: z.record(z.string(), z.unknown()),
      outputs: z.record(z.string(), z.unknown()),
    })),
    source_references: z.array(z.string()),
    confidence_score: z.number(),
  }).nullable().optional(),
})

export type NetWorth = z.infer<typeof NetWorthSchema>

async function fetchNetWorth() {
  const res = await apiFetch(`/api/v1/net-worth`)
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