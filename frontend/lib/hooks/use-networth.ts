/**
 * NetWorth Hook - Fetches and transforms net worth data
 *
 * Pipeline: API → Contract Validation → Mapper → Model
 * Uses shared query runtime for consistent behavior.
 */

import { useAppQuery } from '@/lib/query'
import { queryKeys } from '@/lib/query'
import { STALE_TIME } from '@/lib/query'
import { NetWorthResponseSchema } from '../contracts/api/networth'
import { mapNetworthToModel } from '../mappers/networth'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

async function fetchNetworthDto() {
  const res = await fetch(`${API_BASE}/api/networth`)
  if (!res.ok) throw new Error('Failed to fetch net worth')
  return NetWorthResponseSchema.parse(await res.json())
}

export function useNetWorth() {
  return useAppQuery({
    queryKey: queryKeys.networth.current(),
    queryFn: async () => {
      const dto = await fetchNetworthDto()
      return mapNetworthToModel(dto)
    },
    capability: 'account_management',
    staleTime: STALE_TIME.NORMAL,
  })
}