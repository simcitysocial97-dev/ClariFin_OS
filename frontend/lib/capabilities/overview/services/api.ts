/**
 * Overview API Service - Data fetching functions
 *
 * All API requests for the Overview capability are centralized here.
 * Uses Zod for runtime validation of API responses.
 */

import { OverviewResponseSchema, type OverviewResponseDto } from '../contracts/api'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

/**
 * Fetch overview from the backend API
 *
 * @returns Validated OverviewResponseDto
 */
export async function fetchOverview(): Promise<OverviewResponseDto> {
  const response = await fetch(`${API_BASE}/api/overview`)

  if (!response.ok) {
    throw new Error(`Overview fetch failed: ${response.status}`)
  }

  // This is unverified raw payload from the network
  const raw = await response.json()

  // Parse and validate with Zod
  const parsed = OverviewResponseSchema.safeParse(raw)

  if (!parsed.success) {
    console.error('❌ Overview API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }

  return parsed.data
}