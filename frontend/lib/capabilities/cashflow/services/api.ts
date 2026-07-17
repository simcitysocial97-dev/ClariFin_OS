/**
 * Cashflow API Service - Data fetching functions
 *
 * All API requests for the Cashflow capability are centralized here.
 * Uses Zod for runtime validation of API responses.
 */

import { CashflowResponseSchema, type CashflowResponseDto } from '../contracts/api'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

/**
 * Fetch monthly cashflow data from the backend API
 *
 * @param months - Number of months to fetch (1-12)
 * @returns Validated CashflowResponseDto
 */
export async function fetchCashflow(months: number = 6): Promise<CashflowResponseDto> {
  const response = await fetch(`${API_BASE}/api/cashflow/monthly?months=${months}`)

  if (!response.ok) {
    throw new Error(`Cashflow fetch failed: ${response.status}`)
  }

  // This is unverified raw payload from the network
  const raw = await response.json()

  // Parse and validate with Zod
  const parsed = CashflowResponseSchema.safeParse(raw)

  if (!parsed.success) {
    console.error('❌ Cashflow API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }

  return parsed.data
}

/**
 * Fetch cashflow summary (total values)
 *
 * @param months - Number of months to include in summary
 * @returns Validated CashflowResponseDto
 */
export async function fetchCashflowSummary(months: number = 6): Promise<CashflowResponseDto> {
  return fetchCashflow(months)
}