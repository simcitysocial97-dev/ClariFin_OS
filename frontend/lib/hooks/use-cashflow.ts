/**
 * Cashflow Hook - Fetches and transforms cashflow data
 *
 * Pipeline: API → Contract Validation → Mapper → Model
 * Uses shared query runtime for consistent behavior.
 */

import { useAppQuery } from '@/lib/query'
import { queryKeys } from '@/lib/query'
import { STALE_TIME } from '@/lib/query'
import { fetchCashflow } from '@/lib/capabilities/cashflow/services/api'
import { mapCashflowDtoToModel } from '@/lib/capabilities/cashflow/mappers/mapper'

export function useCashflow(months: number = 6) {
  return useAppQuery({
    queryKey: queryKeys.cashflow.monthly(months),
    queryFn: async () => {
      const dto = await fetchCashflow(months)
      return mapCashflowDtoToModel(dto)
    },
    capability: 'cashflow',
    staleTime: STALE_TIME.REFERENCE,
  })
}