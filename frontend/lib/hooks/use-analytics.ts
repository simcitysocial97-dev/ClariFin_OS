import { useQuery } from '@tanstack/react-query'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Types based on ACTUAL /api/analytics response
interface TopMerchant {
  merchant: string
  amount_display: string
  count: number
}

interface RecurringCharge {
  description: string
  frequency: number
  avg_display: string
  annual_display: string
}

interface DayOfWeekPoint {
  day: string
  amount: number
  count: number
}

interface SpendingTrendPoint {
  month: string
  amount: number
  average: number
}

interface LargestTransaction {
  rank: number
  date_display: string
  description: string
  amount_display: string
  bank: string
}

interface AnalyticsData {
  highest_month: string
  highest_month_amount: string
  avg_monthly: number
  avg_monthly_display: string
  biggest_transaction: {
    description: string
    amount: number
    date: string
    bank: string
  } | null
  unique_merchants: number
  spending_trend: SpendingTrendPoint[]
  day_of_week: DayOfWeekPoint[]
  top_merchants: TopMerchant[]
  recurring_charges: RecurringCharge[]
  largest_transactions: LargestTransaction[]
}

async function fetchAnalytics(): Promise<AnalyticsData> {
  const response = await fetch(`${API_BASE}/api/analytics`)
  if (!response.ok) throw new Error(`Analytics fetch failed: ${response.status}`)
  return response.json()
}

export function useAnalytics() {
  return useQuery({
    queryKey: ['analytics'],
    queryFn: fetchAnalytics,
    staleTime: 10 * 60 * 1000,
  })
}