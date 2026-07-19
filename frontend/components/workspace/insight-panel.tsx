/**
 * Insight Panel Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for displaying transaction insights and summaries.
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatINR } from '@/lib/utils/format';
import type { TransactionViewModel } from '@/types/transaction-view-model';

interface InsightPanelProps {
  transactions: TransactionViewModel[];
  groupBy: 'date' | 'category' | 'merchant' | 'amount' | null;
}

/**
 * Insight Panel Component
 * Displays insights about the current transaction set
 */
export function InsightPanel({ transactions, groupBy }: InsightPanelProps) {
  // Calculate totals
  const totalAmount = transactions.reduce((sum, tx) => sum + tx.amount.paise, 0);
  const debitCount = transactions.filter(tx => tx.transaction_type === 'debit').length;
  const creditCount = transactions.filter(tx => tx.transaction_type === 'credit').length;

  return (
    <div className="border-t bg-background p-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Transaction Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold">{formatINR(totalAmount)}</p>
              <p className="text-xs text-muted-foreground">Total Amount</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{debitCount}</p>
              <p className="text-xs text-muted-foreground">Debits</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{creditCount}</p>
              <p className="text-xs text-muted-foreground">Credits</p>
            </div>
          </div>
          {groupBy && (
            <p className="mt-2 text-xs text-center text-muted-foreground">
              Grouped by: {groupBy}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}