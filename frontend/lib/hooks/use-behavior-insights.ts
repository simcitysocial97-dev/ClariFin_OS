import { useQuery } from '@tanstack/react-query'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Types based on ACTUAL /api/behavior/insights response
interface BehaviorInsight {
  type: 'warning' | 'positive' | 'info'
  title: string
  message: string
  metric: string
  value: number | boolean
}

interface Nudge {
  type: string
  title: string
  message: string
  priority: number
}

interface BehaviorInsightsData {
  insights: BehaviorInsight[]
  nudges: Nudge[]
  top_nudge: Nudge | null
  summary: string
  financial_health_score: number
  confidence: number
}

async function fetchBehaviorInsights(): Promise<BehaviorInsightsData> {
  const response = await fetch(`${API_BASE}/api/behavior/insights`)
  if (!response.ok) throw new Error(`Behavior insights fetch failed: ${response.status}`)
  return response.json()
}

export function useBehaviorInsights() {
  return useQuery({
    queryKey: ['behavior', 'insights'],
    queryFn: fetchBehaviorInsights,
    staleTime: 10 * 60 * 1000,
  })
}