/**
 * Cashflow Hook
 * Fetches monthly cashflow data from the backend API with Zod runtime validation
 */

import { useQuery } from '@tanstack/react-query'
import { CashflowResponseSchema, type CashflowResponse } from '@/lib/schemas/cashflow'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// 🛡️ Data fetching function utilizing Zod runtime parsing
async function fetchCashflow(months: number = 6): Promise<CashflowResponse> {
  const response = await fetch(`${API_BASE}/api/cashflow/monthly?months=${months}`)
  
  if (!response.ok) {
    throw new Error(`Cashflow fetch failed: ${response.status}`)
  }
  
  // This is unverified raw payload from the network
  const raw = await response.json()
    
  // Intercept and parse data before passing it to frontend state loaders
  const parsed = CashflowResponseSchema.safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Cashflow API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
    
  return parsed.data
}

export function useCashflow(months: number = 6) {
  return useQuery({
    queryKey: ['cashflow', 'monthly', months],
    queryFn: () => fetchCashflow(months),
    staleTime: 5 * 60 * 1000,
  })
}
