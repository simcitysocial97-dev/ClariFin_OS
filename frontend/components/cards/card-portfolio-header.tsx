/**
 * Card Portfolio Header - Stage 8E-C2 Production Visual System Migration
 *
 * Displays credit card portfolio summary with total outstanding, credit limit, and utilization.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Skeleton } from '@/components/ui/skeleton'
import { Surface } from '@/components/primitives/surface/surface'
import { Grid } from '@/components/primitives/layout/grid'
import { MoneyValue } from '@/components/primitives/data-display/money-value'
import type { CardsData } from '@/lib/hooks/use-cards'

interface CardPortfolioHeaderProps {
  data: CardsData | null
  loading: boolean
}

export function CardPortfolioHeader({ data, loading }: CardPortfolioHeaderProps) {
  if (loading) {
    return (
      <Grid gap={4} className="grid-cols-1 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Surface key={i} variant="raised" density="none" className="p-4">
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-6 w-32" />
          </Surface>
        ))}
      </Grid>
    )
  }

  if (!data || data.total_cards === 0) {
    return null
  }

  const utilizationColor = 
    data.total_utilization_percent < 30 ? 'text-[var(--color-positive-600)]' :
    data.total_utilization_percent < 75 ? 'text-[var(--color-warning-600)]' : 'text-[var(--color-negative-600)]'

  return (
    <Grid gap={4} className="grid-cols-1 md:grid-cols-4">
      <Surface variant="raised" density="none" className="p-4">
        <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wide">Total Outstanding</p>
        <MoneyValue paise={data.total_outstanding} variant="default" />
      </Surface>
      
      <Surface variant="raised" density="none" className="p-4">
        <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wide">Total Credit Limit</p>
        <MoneyValue paise={data.total_credit_limit} variant="default" />
      </Surface>
      
      <Surface variant="raised" density="none" className="p-4">
        <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wide">Overall Utilization</p>
        <p className={`text-lg font-semibold mt-1 ${utilizationColor}`}>
          {data.total_utilization_percent.toFixed(1)}%
        </p>
      </Surface>
      
      <Surface variant="raised" density="none" className="p-4">
        <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wide">Cards Count</p>
        <p className="text-lg font-semibold mt-1">
          {data.total_cards} {data.total_cards === 1 ? 'card' : 'cards'}
        </p>
      </Surface>
    </Grid>
  )
}