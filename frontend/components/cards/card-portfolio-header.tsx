'use client'

import { formatINR, rupeesToPaise } from '@/lib/utils/format'
import type { CardsData } from '@/lib/hooks/use-cards'

interface CardPortfolioHeaderProps {
  data: CardsData | null
  loading: boolean
}

export function CardPortfolioHeader({ data, loading }: CardPortfolioHeaderProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-card border rounded-lg p-4 animate-pulse">
            <div className="h-4 bg-muted rounded mb-2" />
            <div className="h-6 bg-muted rounded" />
          </div>
        ))}
      </div>
    )
  }

  if (!data || data.total_cards === 0) {
    return null
  }

  const utilizationColor = 
    data.total_utilization_percent < 30 ? 'text-green-600' :
    data.total_utilization_percent < 75 ? 'text-amber-600' : 'text-red-600'

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-card border rounded-lg p-4">
        <p className="text-xs text-muted-foreground uppercase tracking-wide">Total Outstanding</p>
        <p className="text-lg font-semibold mt-1">{formatINR(rupeesToPaise(data.total_outstanding))}</p>
      </div>
      
      <div className="bg-card border rounded-lg p-4">
        <p className="text-xs text-muted-foreground uppercase tracking-wide">Total Credit Limit</p>
        <p className="text-lg font-semibold mt-1">{formatINR(rupeesToPaise(data.total_credit_limit))}</p>
      </div>
      
      <div className="bg-card border rounded-lg p-4">
        <p className="text-xs text-muted-foreground uppercase tracking-wide">Overall Utilization</p>
        <p className={`text-lg font-semibold mt-1 ${utilizationColor}`}>
          {data.total_utilization_percent.toFixed(1)}%
        </p>
      </div>
      
      <div className="bg-card border rounded-lg p-4">
        <p className="text-xs text-muted-foreground uppercase tracking-wide">Cards Count</p>
        <p className="text-lg font-semibold mt-1">
          {data.total_cards} {data.total_cards === 1 ? 'card' : 'cards'}
        </p>
      </div>
    </div>
  )
}