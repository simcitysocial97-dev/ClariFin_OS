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
  amount: number  // In paise (canonical)
}

interface CategoryChartPoint {
  name: string
  value: number  // In paise (canonical)
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

// Convert rupees to paise at the hook boundary
function rupeesToPaise(rupees: number): number {
  return Math.round(rupees * 100)
}

async function fetchOverview(): Promise<OverviewData> {
  const response = await fetch(`${API_BASE}/api/overview`)
  if (!response.ok) throw new Error(`Overview fetch failed: ${response.status}`)
  const raw = await response.json()
  
  // Convert category_chart values from rupees to paise (canonical)
  const category_chart = (raw.category_chart || []).map((item: { name: string; value: number }) => ({
    name: item.name,
    value: rupeesToPaise(item.value),
  }))
  
  // Convert monthly_chart values from rupees to paise (canonical)
  const monthly_chart = (raw.monthly_chart || []).map((item: { month: string; amount: number }) => ({
    month: item.month,
    amount: rupeesToPaise(item.amount),
  }))
  
  return {
    ...raw,
    category_chart,
    monthly_chart,
  }
}

export function useOverview() {
  return useQuery({
    queryKey: ['overview'],
    queryFn: fetchOverview,
    staleTime: 5 * 60 * 1000,
  })
}