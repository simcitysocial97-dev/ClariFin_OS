/**
 * Transaction Table Component - Stage 3 Transaction Intelligence Workspace
 *
 * Main table component for displaying transactions.
 * Dark mode support with bg-background classes.
 * Keyboard navigation with arrow key support.
 * Accessibility with proper ARIA attributes.
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { SkeletonTable } from '@/components/loading/skeleton-row';
import { EmptyState } from '@/components/loading/empty-state';
import { formatINR } from '@/lib/utils/format';
import { cn } from '@/lib/utils';
import type { TransactionViewModel } from '@/types/transaction-view-model';

interface TransactionTableProps {
  transactions: TransactionViewModel[];
  loading?: boolean;
  error?: Error | null;
  onRowClick?: (transaction: TransactionViewModel) => void;
  onSelectionChange?: (id: string, selected: boolean) => void;
  selectedIds?: Set<string>;
}

/**
 * Transaction Table Component
 * Displays a list of transactions with selection support
 * Responsive design: hides columns on smaller screens
 * Dark mode: uses bg-background for proper theme support
 * Keyboard navigation: arrow keys to navigate rows
 * Accessibility: includes ARIA attributes and keyboard support
 */
export function TransactionTable({
  transactions,
  loading = false,
  error = null,
  onRowClick,
  onSelectionChange,
  selectedIds = new Set(),
}: TransactionTableProps) {
  const [focusedRowIndex, setFocusedRowIndex] = useState<number>(-1);
  const rowRefs = useRef<(HTMLTableRowElement | null)[]>([]);

  // Keyboard navigation for table rows
  useEffect(() => {
    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if (transactions.length === 0) return;

      // Only handle if focus is within the table
      const activeElement = document.activeElement;
      if (!activeElement?.closest('table')) return;

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setFocusedRowIndex((prev) => {
            const next = Math.min(prev + 1, transactions.length - 1);
            rowRefs.current[next]?.focus();
            return next;
          });
          break;
        case 'ArrowUp':
          event.preventDefault();
          setFocusedRowIndex((prev) => {
            const next = Math.max(prev - 1, 0);
            rowRefs.current[next]?.focus();
            return next;
          });
          break;
        case 'Enter':
        case ' ':
          if (focusedRowIndex >= 0) {
            event.preventDefault();
            onRowClick?.(transactions[focusedRowIndex]);
          }
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [transactions, focusedRowIndex, onRowClick]);

  if (loading) {
    return (
      <Card className="border-0 rounded-none bg-background dark:bg-background">
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

  if (error) {
    return (
      <div className="p-4 sm:p-6 bg-background dark:bg-background">
        <Alert variant="destructive">
          <AlertTitle>Error loading transactions</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="p-4 sm:p-6 bg-background dark:bg-background">
        <EmptyState />
      </div>
    );
  }

  return (
    <Card className="border-0 rounded-none bg-background dark:bg-background">
      <CardContent className="p-0">
        <Table role="table" aria-label="Transactions">
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40px] sm:w-[50px]">
                <span className="sr-only">Select</span>
              </TableHead>
              <TableHead className="w-[100px] sm:w-auto">Date</TableHead>
              <TableHead className="min-w-[150px]">Description</TableHead>
              <TableHead className="w-[120px] hidden sm:table-cell">Category</TableHead>
              <TableHead className="w-[120px] hidden md:table-cell">Merchant</TableHead>
              <TableHead className="text-right w-[100px] sm:w-auto">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((tx, index) => (
              <TableRow
                key={tx.id}
                ref={(el) => { rowRefs.current[index] = el; }}
                className={cn(
                  'cursor-pointer hover:bg-muted/50 transition-colors',
                  selectedIds.has(tx.id) && 'bg-muted/30',
                  focusedRowIndex === index && 'outline-none ring-2 ring-primary'
                )}
                onClick={() => onRowClick?.(tx)}
                onFocus={() => setFocusedRowIndex(index)}
                tabIndex={-1}
                role="row"
                aria-selected={selectedIds.has(tx.id)}
              >
                <TableCell className="w-[40px] sm:w-[50px]">
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
                <TableCell className="w-[100px] sm:w-auto text-sm" role="cell">
                  {tx.date_formatted || tx.date}
                </TableCell>
                <TableCell className="max-w-[200px] sm:max-w-[300px] truncate text-sm" role="cell">
                  {tx.description}
                </TableCell>
                <TableCell className="hidden sm:table-cell" role="cell">
                  <Badge variant="secondary" className="text-xs">
                    {tx.category_name || 'Uncategorized'}
                  </Badge>
                </TableCell>
                <TableCell className="hidden md:table-cell text-sm" role="cell">
                  {tx.merchant_name || '-'}
                </TableCell>
                <TableCell
                  className={cn(
                    'text-right font-mono tabular-nums text-sm',
                    tx.transaction_type === 'debit' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'
                  )}
                  role="cell"
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
