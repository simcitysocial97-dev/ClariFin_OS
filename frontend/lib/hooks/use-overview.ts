import { useQuery } from '@tanstack/react-query'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Types based on ACTUAL /api/overview response fields
interface BehavioralInsight {
  title: string
  description: string
  severity: 'warning' | 'positive' | 'neutral'
  icon: string
}

interface MonthlyChartPoint {
  month: string
  amount: number  // In rupees (not paise)
}

interface CategoryChartPoint {
  name: string
  value: number  // In rupees (not paise)
}

interface OverviewData {
  total_spend: number
  total_spend_display: string
  this_month: number
  this_month_display: string
  last_month: number
  last_month_display: string
  month_change: string
  transaction_count: number
  card_count: number
  months_of_data: number
  monthly_average: number
  monthly_average_display: string
  above_below_avg: string
  above_avg_is_bad: boolean
  monthly_chart: MonthlyChartPoint[]
  category_chart: CategoryChartPoint[]
  behavioral_insights: BehavioralInsight[]
}

async function fetchOverview(): Promise<OverviewData> {
  const response = await fetch(`${API_BASE}/api/overview`)
  if (!response.ok) throw new Error(`Overview fetch failed: ${response.status}`)
  return response.json()
}

export function useOverview() {
  return useQuery({
    queryKey: ['overview'],
    queryFn: fetchOverview,
    staleTime: 5 * 60 * 1000,
  })
}