import { useQuery } from '@tanstack/react-query'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Types based on ACTUAL /api/behavior/score response
interface BehaviorComponents {
  savings_discipline: number
  habit_stability: number
  impulsivity: number
  financial_stress: number
  loss_aversion: number
}

interface IndiaRiskFlags {
  upi_micro_spend_flag: boolean
  gambling_flag: boolean
  loan_app_pattern_flag: boolean
  loan_credit_count: number
  emi_ratio: number
  monthly_emi_total: number
}

interface RiskFlags {
  india_specific: IndiaRiskFlags
  high_impulsivity: boolean
  high_stress: boolean
  low_savings: boolean
}

interface BehaviorScoreData {
  financial_health_score: number
  confidence: number
  components: BehaviorComponents
  risk_flags: RiskFlags
  summary: string
}

async function fetchBehaviorScore(): Promise<BehaviorScoreData> {
  const response = await fetch(`${API_BASE}/api/behavior/score`)
  if (!response.ok) throw new Error(`Behavior score fetch failed: ${response.status}`)
  return response.json()
}

export function useBehaviorScore() {
  return useQuery({
    queryKey: ['behavior', 'score'],
    queryFn: fetchBehaviorScore,
    staleTime: 10 * 60 * 1000,
  })
}