'use client';

import { ArrowDownRight, ArrowUpRight, Wallet, TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatPaise } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { Transaction } from '@/types/transaction';

interface TransactionSummaryCardsProps {
  transactions: Transaction[];
  totalCount: number;
}

export function TransactionSummaryCards({ transactions, totalCount }: TransactionSummaryCardsProps) {
  // Calculate totals - API returns amount_paise (paise integer)
  const totalDebits = transactions
    .filter((t) => t.type === 'debit')
    .reduce((sum, t) => sum + (t.amount_paise || 0), 0);
  
  const totalCredits = transactions
    .filter((t) => t.type === 'credit')
    .reduce((sum, t) => sum + (t.amount_paise || 0), 0);

  // Find largest expense
  const largestExpense = transactions
    .filter((t) => t.type === 'debit')
    .sort((a, b) => (b.amount_paise || 0) - (a.amount_paise || 0))[0];

  // Count this month's transactions
  const now = new Date();
  const thisMonthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  const thisMonthCount = transactions.filter((t) => {
    const txnDate = new Date(t.date);
    const txnMonthKey = `${txnDate.getFullYear()}-${String(txnDate.getMonth() + 1).padStart(2, '0')}`;
    return txnMonthKey === thisMonthKey;
  }).length;

  // Calculate total volume
  const totalVolume = totalDebits + totalCredits;

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {/* Transactions This Month */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Transactions This Month</CardTitle>
          <Wallet className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{thisMonthCount}</div>
          <p className="text-xs text-muted-foreground">
            of {totalCount} total transactions
          </p>
        </CardContent>
      </Card>

      {/* Largest Expense */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Largest Expense</CardTitle>
          <TrendingDown className="h-4 w-4 text-rose-500" />
        </CardHeader>
        <CardContent>
          <div className={cn("text-2xl font-bold", largestExpense ? 'text-rose-600' : 'text-muted-foreground')}>
            {largestExpense ? formatPaise(largestExpense.amount_paise || 0) : '₹0.00'}
          </div>
          <p className="text-xs text-muted-foreground truncate">
            {largestExpense ? (largestExpense.description_display || largestExpense.description) : 'No expenses found'}
          </p>
        </CardContent>
      </Card>

      {/* Total Volume */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Volume</CardTitle>
          <TrendingUp className="h-4 w-4 text-emerald-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatPaise(totalVolume)}</div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="flex items-center text-emerald-600">
              <ArrowUpRight className="h-3 w-3 mr-1" />
              {formatPaise(totalCredits)}
            </span>
            <span className="flex items-center text-rose-600">
              <ArrowDownRight className="h-3 w-3 mr-1" />
              {formatPaise(totalDebits)}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
