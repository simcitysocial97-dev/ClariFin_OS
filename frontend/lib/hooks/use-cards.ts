import { useAsyncQuery, HookState } from './use-async-query'
import { CardsDataSchema, type CardsData, type CardSummary } from '@/lib/schemas/cards'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Convert rupees to paise at the hook boundary
function rupeesToPaise(rupees: number): number {
  return Math.round(rupees * 100)
}

// 🛡️ Data fetching function utilizing Zod runtime parsing
async function fetchCards(): Promise<CardsData> {
  const response = await fetch(`${API_BASE}/api/cards`)
  if (!response.ok) throw new Error(`Cards fetch failed: ${response.status}`)
  
  // This is unverified raw payload from the network
  const raw = await response.json()
  
  // Convert all monetary values from rupees to paise (canonical)
  const cards = (raw.cards || []).map((card: any) => ({
    ...card,
    credit_limit: rupeesToPaise(card.credit_limit || 0),
    current_outstanding: rupeesToPaise(card.current_outstanding || 0),
    minimum_due: rupeesToPaise(card.minimum_due || 0),
  }))
  
  const converted = {
    ...raw,
    cards,
    total_outstanding: rupeesToPaise(raw.total_outstanding || 0),
    total_credit_limit: rupeesToPaise(raw.total_credit_limit || 0),
  }
  
  // Intercept and parse data before passing it to frontend state loaders
  const parsed = CardsDataSchema.safeParse(converted)
  
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
