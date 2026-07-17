/**
 * Accounts Hook - Fetches and transforms accounts data
 *
 * Pipeline: API → Contract Validation → Mapper → Model
 * Uses shared query runtime for consistent behavior.
 */

import { useAppQuery } from '@/lib/query'
import { queryKeys } from '@/lib/query'
import { STALE_TIME } from '@/lib/query'
import { fetchManagedAccounts } from '../services/api'
import { mapAccountsDtoToModel } from '../mappers/mapper'

export function useManagedAccounts() {
  return useAppQuery({
    queryKey: queryKeys.accounts.managed(),
    queryFn: async () => {
      const dto = await fetchManagedAccounts()
      return mapAccountsDtoToModel(dto)
    },
    capability: 'accounts',
    staleTime: STALE_TIME.REFERENCE,
  })
}