import { useQuery } from '@tanstack/react-query'

import { WellnessScoreResponseSchema } from '../contracts/api/behavior'
import { mapWellnessScoreToModel } from '../mappers/behavior'
import type { WellnessScoreModel } from '../models/behavior'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

async function fetchWellnessScore(): Promise<WellnessScoreModel> {
  const response = await fetch(`${API_BASE}/api/v1/behaviour/wellness-score`)
  if (!response.ok) throw new Error(`Wellness score fetch failed: ${response.status}`)
  const dto = WellnessScoreResponseSchema.parse(await response.json())
  return mapWellnessScoreToModel(dto)
}

export function useBehaviorScore() {
  return useQuery({
    queryKey: ['behavior', 'score'],
    queryFn: fetchWellnessScore,
    staleTime: 10 * 60 * 1000,
  })
}
