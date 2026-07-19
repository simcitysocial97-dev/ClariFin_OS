/**
 * Transaction Table Component - Stage 3 Transaction Intelligence Workspace
 *
 * Main table component for displaying transactions.
 */

'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SkeletonTable } from '@/components/loading/skeleton-row';
import { EmptyState } from '@/components/loading/empty-state';
import { formatINR } from '@/lib/utils/format';
import { cn } from '@/lib/utils';
import type { TransactionViewModel } from '@/types/transaction-view-model';

interface TransactionTableProps {
  transactions: TransactionViewModel[];
  loading?: boolean;
  onRowClick?: (transaction: TransactionViewModel) => void;
  onSelectionChange?: (id: string, selected: boolean) => void;
  selectedIds?: Set<string>;
}

/**
 * Transaction Table Component
 * Displays a list of transactions with selection support
 */
export function TransactionTable({
  transactions,
  loading = false,
  onRowClick,
  onSelectionChange,
  selectedIds = new Set(),
}: TransactionTableProps) {
  if (loading) {
    return (
      <Card className="border-0 rounded-none">
        <CardContent className="p-0">
          <Table>
            <TableBody>
              <SkeletonTable rows={5} columns={6} />
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="p-6">
        <EmptyState />
      </div>
    );
  }

  return (
    <Card className="border-0 rounded-none">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[50px]">Select</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Merchant</TableHead>
              <TableHead className="text-right">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((tx) => (
              <TableRow
                key={tx.id}
                className={cn(
                  'cursor-pointer hover:bg-muted/50 transition-colors',
                  selectedIds.has(tx.id) && 'bg-muted/30'
                )}
                onClick={() => onRowClick?.(tx)}
              >
                <TableCell>
                  <input
                    type="checkbox"
                    checked={selectedIds.has(tx.id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      onSelectionChange?.(tx.id, e.target.checked);
                    }}
                    aria-label={`Select transaction ${tx.id}`}
                  />
                </TableCell>
                <TableCell>{tx.date_formatted || tx.date}</TableCell>
                <TableCell className="max-w-[300px] truncate">
                  {tx.description}
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" className="text-xs">
                    {tx.category_name || 'Uncategorized'}
                  </Badge>
                </TableCell>
                <TableCell>{tx.merchant_name || '-'}</TableCell>
                <TableCell
                  className={cn(
                    'text-right font-mono tabular-nums',
                    tx.transaction_type === 'debit' ? 'text-red-600' : 'text-green-600'
                  )}
                >
                  {formatINR(tx.amount.paise)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}