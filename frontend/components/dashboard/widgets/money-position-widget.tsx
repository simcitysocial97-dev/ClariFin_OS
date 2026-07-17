/**
 * Money Position Widget - Net Worth and Assets Summary
 *
 * Shows where your money is: Net Worth, Cash, Accounts, Investments
 */

'use client';
import { Wallet, TrendingUp } from 'lucide-react';
import { formatINRCompact } from '@/lib/utils/format';
import { useNetWorth } from '@/lib/hooks/use-networth';

export function MoneyPositionWidget() {
  const { data, isLoading } = useNetWorth();

  if (isLoading || !data) return null;

  // Use derived trend flag from ViewModel
  const trendColor = 
    data.trend === 'up' ? 'text-green-500' : 
    data.trend === 'down' ? 'text-red-500' : 
    'text-muted-foreground';

  return (
    <div className="space-y-4">
      {/* Net Worth */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Wallet className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">Net Worth</span>
        </div>
        <div className="text-right">
          <p className="font-semibold">{formatINRCompact(data.netWorthPaise)}</p>
          <p className={`text-xs ${trendColor}`}>
            {data.trend === 'up' ? '+' : ''}{formatINRCompact(data.assetsTotalPaise - data.liabilitiesTotalPaise)} this month
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
  );
}