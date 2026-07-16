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

  const netChangePaise = data.assets.total_paise - data.liabilities.total_paise;
  const isPositive = netChangePaise > 0;

  return (
    <div className="space-y-4">
      {/* Net Worth */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Wallet className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">Net Worth</span>
        </div>
        <div className="text-right">
          <p className="font-semibold">{formatINRCompact(data.net_worth_paise)}</p>
          <p className={`text-xs ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
            {isPositive ? '+' : ''}₹{(netChangePaise / 100).toFixed(0)} this month
          </p>
        </div>
      </div>

      {/* Assets breakdown */}
      <div className="space-y-2 pl-6">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Accounts</span>
          <span>{formatINRCompact(data.assets.accounts_paise)} ({data.assets.account_count})</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Investments</span>
          <span className="flex items-center gap-1">
            {formatINRCompact(data.assets.investments_paise)}
            <TrendingUp className="h-3 w-3 text-green-500" />
          </span>
        </div>
      </div>

      {/* Liabilities */}
      <div className="border-t pt-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Borrowing</span>
          <span>{formatINRCompact(data.liabilities.total_paise)}</span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          {data.liabilities.loan_count} loans, {data.liabilities.card_count} cards
        </p>
      </div>
    </div>
  );
}