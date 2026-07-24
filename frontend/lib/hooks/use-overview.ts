import { useQuery } from '@tanstack/react-query'
import { OverviewSchema, type Overview } from '@/lib/schemas/overview'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Convert rupees to paise at the hook boundary
function rupeesToPaise(rupees: number): number {
  return Math.round(rupees * 100)
}

// 🛡️ Data fetching function utilizing Zod runtime parsing
async function fetchOverview(): Promise<Overview> {
  const response = await fetch(`${API_BASE}/api/overview`)
  if (!response.ok) throw new Error(`Overview fetch failed: ${response.status}`)
  
  // This is unverified raw payload from the network
  const raw = await response.json()
  
  // Convert category_chart values from rupees to paise (canonical)
  const category_chart = (raw.category_chart || []).map((item: { name: string; value: number }) => ({
    name: item.name,
    value: rupeesToPaise(item.value),
  }))
  
  // Convert monthly_chart values from rupees to paise (canonical)
  const monthly_chart = (raw.monthly_chart || []).map((item: { month: string; amount: number }) => ({
    month: item.month,
    amount: rupeesToPaise(item.amount),
  }))
  
  const converted = {
    ...raw,
    category_chart,
    monthly_chart,
  }
  
  // Intercept and parse data before passing it to frontend state loaders
  const parsed = OverviewSchema.safeParse(converted)
  
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
