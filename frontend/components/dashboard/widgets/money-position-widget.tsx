/**
 * Money Position Widget - Net Worth and Assets Summary
 *
 * Shows where your money is: Net Worth, Cash, Accounts, Investments
 * Uses DataStateWrapper for consistent loading/error/empty handling.
 */

'use client'

import { Wallet, TrendingUp, Info } from 'lucide-react'
import { formatINRCompact } from '@/lib/utils/format'
import { useNetWorth } from '@/lib/hooks/use-networth'
import { useExplainabilityDrawer } from '@/components/explainability'
import { Button } from '@/components/ui/button'
import { DataStateWrapper } from '@/components/runtime'
import type { NetWorthModel } from '@/lib/models/networth'

/**
 * Widget content - only renders when data is available
 */
function MoneyPositionContent({ data }: { data: NetWorthModel }) {
  const { showExplanation } = useExplainabilityDrawer()

  // Use derived trend flag from ViewModel
  const trendColor =
    data.trend === 'up'
      ? 'text-green-500'
      : data.trend === 'down'
        ? 'text-red-500'
        : 'text-muted-foreground'

  // Handle explain button click
  const handleExplain = () => {
    if (data.explanation?.netWorth) {
      showExplanation(data.explanation.netWorth)
    }
  }

  return (
    <div className="space-y-4">
      {/* Net Worth */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Wallet className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">Net Worth</span>
        </div>
        <div className="text-right flex items-center gap-2">
          <p className="font-semibold">{formatINRCompact(data.netWorthPaise)}</p>
          {data.explanation?.netWorth && (
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={handleExplain}
              aria-label="Explain Net Worth calculation"
            >
              <Info className="h-3 w-3" />
            </Button>
          )}
          <p className={`text-xs ${trendColor}`}>
            {data.trend === 'up' ? '+' : ''}
            {formatINRCompact(data.assetsTotalPaise - data.liabilitiesTotalPaise)} this month
          </p>
        </div>
      </div>

      {/* Assets breakdown */}
      <div className="space-y-2 pl-6">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Accounts</span>
          <span>{formatINRCompact(data.assetsAccountsPaise)} ({data.accountCount})</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Investments</span>
          <span className="flex items-center gap-1">
            {formatINRCompact(data.assetsInvestmentsPaise)}
            <TrendingUp className="h-3 w-3 text-green-500" />
          </span>
        </div>
      </div>

      {/* Liabilities */}
      <div className="border-t pt-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Borrowing</span>
          <span>{formatINRCompact(data.liabilitiesTotalPaise)}</span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          {data.loanCount} loans, {data.cardCount} cards
        </p>
      </div>
    </div>
  )
}

/**
 * Money Position Widget - Uses DataStateWrapper for state management
 */
export function MoneyPositionWidget() {
  const query = useNetWorth()

  return (
    <DataStateWrapper
      query={query}
      loadingVariant="spinner"
      loadingMessage="Loading net worth..."
    >
      {(data) => <MoneyPositionContent data={data} />}
    </DataStateWrapper>
  )
}