/**
 * Cashflow Hook
 * Fetches monthly cashflow data from the backend API
 */

import { useQuery } from '@tanstack/react-query'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

interface CashflowMonth {
  month_key: string
  month_label: string
  income_paise: number
  expense_paise: number
  net_paise: number
  transaction_count: number
}

interface CashflowData {
  months: CashflowMonth[]
  period_months: number
  total_income_paise: number
  total_expense_paise: number
  total_net_paise: number
}

async function fetchCashflow(months: number = 6): Promise<CashflowData> {
  const response = await fetch(`${API_BASE}/api/cashflow/monthly?months=${months}`)
  if (!response.ok) {
    throw new Error(`Cashflow fetch failed: ${response.status}`)
  }
  return response.json()
}

export function useCashflow(months: number = 6) {
  return useQuery({
    queryKey: ['cashflow', 'monthly', months],
    queryFn: () => fetchCashflow(months),
    staleTime: 5 * 60 * 1000,
  })
}