/**
 * Accounts API Service - Data fetching functions
 *
 * All API requests for the Accounts capability are centralized here.
 * Uses Zod for runtime validation of API responses.
 */

import { AccountsResponseSchema, type AccountsResponseDto } from '../contracts/api'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

/**
 * Fetch accounts summary from the backend API
 *
 * @returns Validated AccountsResponseDto
 */
export async function fetchManagedAccounts(): Promise<AccountsResponseDto> {
  const response = await fetch(`${API_BASE}/api/v1/accounts/summary`)

  if (!response.ok) {
    throw new Error(`Accounts fetch failed: ${response.status}`)
  }

  // This is unverified raw payload from the network
  const raw = await response.json()

  // Parse and validate with Zod
  const parsed = AccountsResponseSchema.safeParse(raw)

  if (!parsed.success) {
    console.error('❌ Accounts API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }

  return parsed.data
}
