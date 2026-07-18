/**
 * Overview Hook - Fetches and transforms overview data
 *
 * Pipeline: API → Contract Validation → Mapper → Model
 * Uses shared query runtime for consistent behavior.
 */

import { useAppQuery } from '@/lib/query'
import { queryKeys } from '@/lib/query'
import { STALE_TIME } from '@/lib/query'
import { fetchOverview } from '../services/api'
import { mapOverviewDtoToModel } from '../mappers/mapper'

export function useOverview() {
  return useAppQuery({
    queryKey: queryKeys.analytics.overview(),
    queryFn: async () => {
      const dto = await fetchOverview()
      return mapOverviewDtoToModel(dto)
    },
    capability: 'overview',
    staleTime: STALE_TIME.REFERENCE,
  })
}
