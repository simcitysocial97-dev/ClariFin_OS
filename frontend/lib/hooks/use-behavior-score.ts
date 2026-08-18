import { useQuery } from '@tanstack/react-query'
import { BehaviorScoreSchema, type BehaviorScore } from '@/lib/schemas/behavior-score'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 🛡️ Data fetching function utilizing Zod runtime parsing
async function fetchBehaviorScore(): Promise<BehaviorScore> {
  const response = await fetch(`${API_BASE}/api/v1/behaviour/wellness-score`)
  if (!response.ok) throw new Error(`Behavior score fetch failed: ${response.status}`)
  
  // This is unverified raw payload from the network
  const raw = await response.json()
  
  // Intercept and parse data before passing it to frontend state loaders
  const parsed = BehaviorScoreSchema.safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Behavior score API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
}

export function useBehaviorScore() {
  return useQuery({
    queryKey: ['behavior', 'score'],
    queryFn: fetchBehaviorScore,
    staleTime: 10 * 60 * 1000,
  })
}
