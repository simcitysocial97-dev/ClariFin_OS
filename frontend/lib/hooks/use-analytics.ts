import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api/gateway';
import { AnalyticsSchema, type Analytics } from '@/lib/schemas/analytics'


// 🛡️ Data fetching function utilizing Zod runtime parsing
async function fetchAnalytics(): Promise<Analytics> {
  const response = await apiFetch(`/api/analytics`)
  if (!response.ok) throw new Error(`Analytics fetch failed: ${response.status}`)
  
  // This is unverified raw payload from the network
  const raw = await response.json()
  
  // Intercept and parse data before passing it to frontend state loaders
  const parsed = AnalyticsSchema.safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Analytics API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
}

export function useAnalytics() {
  return useQuery({
    queryKey: ['analytics'],
    queryFn: fetchAnalytics,
    staleTime: 10 * 60 * 1000,
  })
}
