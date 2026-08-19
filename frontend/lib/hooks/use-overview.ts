import { useQuery } from '@tanstack/react-query'
import { OverviewSchema, type Overview } from '@/lib/schemas/overview'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 🛡️ Data fetching function utilizing Zod runtime parsing
async function fetchOverview(): Promise<Overview> {
  const response = await fetch(`${API_BASE}/api/overview`)
  if (!response.ok) throw new Error(`Overview fetch failed: ${response.status}`)

  // This is unverified raw payload from the network
  const raw = await response.json()

  // Intercept and parse data before passing it to frontend state loaders
  const parsed = OverviewSchema.safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Overview API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
}

export function useOverview() {
  return useQuery({
    queryKey: ['overview'],
    queryFn: fetchOverview,
    staleTime: 5 * 60 * 1000,
  })
}
