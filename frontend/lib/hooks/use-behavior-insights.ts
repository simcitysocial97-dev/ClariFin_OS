import { useQuery } from '@tanstack/react-query'

import { BehaviorInsightsResponseSchema } from '../contracts/api/behavior'
import { mapBehaviorInsightsToModel } from '../mappers/behavior'
import type { BehaviorInsightsModel } from '../models/behavior'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

async function fetchBehaviorInsights(): Promise<BehaviorInsightsModel> {
  const response = await fetch(`${API_BASE}/api/behavior/insights`)
  if (!response.ok) throw new Error(`Behavior insights fetch failed: ${response.status}`)
  const dto = BehaviorInsightsResponseSchema.parse(await response.json())
  return mapBehaviorInsightsToModel(dto)
}

export function useBehaviorInsights() {
  return useQuery({
    queryKey: ['behavior', 'insights'],
    queryFn: fetchBehaviorInsights,
    staleTime: 10 * 60 * 1000,
  })
}
