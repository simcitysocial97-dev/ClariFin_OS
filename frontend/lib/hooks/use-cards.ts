import type { HookState } from './use-async-query';
import { apiFetch } from '@/lib/api/gateway';
import { useAsyncQuery } from './use-async-query'
import { CardsDataSchema, type CardsData, type CardSummary } from '@/lib/schemas/cards'


// 🛡️ Data fetching function utilizing Zod runtime parsing
async function fetchCards(): Promise<CardsData> {
  const response = await apiFetch(`/api/cards`)
  if (!response.ok) throw new Error(`Cards fetch failed: ${response.status}`)

  // This is unverified raw payload from the network
  const raw = await response.json()

  // Intercept and parse data before passing it to frontend state loaders
  const parsed = CardsDataSchema.safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Cards API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
}

export function useCards(): HookState<CardsData> {
  return useAsyncQuery(
    ['cards'],
    fetchCards
  )
}

// Re-export types for backward compatibility
export type { CardSummary, CardsData }
