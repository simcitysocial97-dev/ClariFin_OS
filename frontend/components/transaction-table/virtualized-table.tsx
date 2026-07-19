/**
 * Virtualized Table Component - Stage 3 Transaction Intelligence Workspace
 *
 * Virtualized table for efficient rendering of large transaction lists.
 * Uses CSS-based virtualization with fixed height and overflow.
 * Dark mode support with bg-background classes.
 * Accessibility with proper ARIA attributes.
 */

'use client';

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { SkeletonTable } from '@/components/loading/skeleton-row';
import { EmptyState } from '@/components/loading/empty-state';
import { formatINR } from '@/lib/utils/format';
import { cn } from '@/lib/utils';
import type { TransactionViewModel } from '@/types/transaction-view-model';

interface ColumnVisibility {
  select: boolean;
  date: boolean;
  description: boolean;
  category: boolean;
  merchant: boolean;
  amount: boolean;
}

interface VirtualizedTableProps {
  transactions: TransactionViewModel[];
  loading?: boolean;
  error?: Error | null;
  onRowClick?: (transaction: TransactionViewModel) => void;
  onSelectionChange?: (id: string, selected: boolean) => void;
  selectedIds?: Set<string>;
  columnVisibility?: ColumnVisibility;
  // Virtualization
  rowHeight?: number;
  visibleRows?: number;
}

const ROW_HEIGHT = 48; // Default row height in pixels
const VISIBLE_ROWS = 10; // Default number of visible rows

/**
 * Virtualized Table Component
 * Efficiently renders large transaction lists by only showing visible rows
 * Uses CSS-based virtualization with position sticky
 * Dark mode support with bg-background classes
 * Accessibility with ARIA attributes
 */
export function VirtualizedTable({
  transactions,
  loading = false,
  error = null,
  onRowClick,
  onSelectionChange,
  selectedIds = new Set(),
  columnVisibility,
  rowHeight = ROW_HEIGHT,
  visibleRows = VISIBLE_ROWS,
}: VirtualizedTableProps) {
  const [scrollTop, setScrollTop] = useState<number>(0);
  const [focusedRowIndex, setFocusedRowIndex] = useState<number>(-1);
  const containerRef = useRef<HTMLDivElement>(null);

  // Default column visibility
  const visibility = columnVisibility ?? {
    select: true,
    date: true,
    description: true,
    category: true,
    merchant: true,
    amount: true,
  };

  // Calculate visible range
  const startIndex = Math.floor(scrollTop / rowHeight);
  const endIndex = Math.min(
    startIndex + visibleRows + 2, // +2 for buffer
    transactions.length
  );

  // Get visible transactions
  const visibleTransactions = useMemo(() => {
    return transactions.slice(startIndex, endIndex);
  }, [transactions, startIndex, endIndex]);

  // Handle scroll
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if (transactions.length === 0) return;

      const activeElement = document.activeElement;
      if (!activeElement?.closest('table')) return;

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setFocusedRowIndex((prev) => {
            const next = Math.min(prev + 1, transactions.length - 1);
            return next;
          });
          break;
        case 'ArrowUp':
          event.preventDefault();
          setFocusedRowIndex((prev) => {
            const next = Math.max(prev - 1, 0);
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
        <div
          ref={containerRef}
          className="h-[400px] overflow-y-auto"
          onScroll={handleScroll}
        >
          <Table role="table" aria-label="Transactions" style={{ tableLayout: 'fixed' }}>
            <TableHeader>
              <TableRow>
                {visibility.select && (
                  <TableHead className="w-[40px] sm:w-[50px]">
                    <span className="sr-only">Select</span>
                  </TableHead>
                )}
                {visibility.date && (
                  <TableHead className="w-[100px] sm:w-auto">Date</TableHead>
                )}
                {visibility.description && (
                  <TableHead className="min-w-[150px]">Description</TableHead>
                )}
                {visibility.category && (
                  <TableHead className="w-[120px] hidden sm:table-cell">Category</TableHead>
                )}
                {visibility.merchant && (
                  <TableHead className="w-[120px] hidden md:table-cell">Merchant</TableHead>
                )}
                {visibility.amount && (
                  <TableHead className="text-right w-[100px] sm:w-auto">Amount</TableHead>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {/* Spacer for rows before visible range */}
              <TableRow style={{ height: `${startIndex * rowHeight}px` }}>
                <TableCell colSpan={6} className="p-0 border-0" />
              </TableRow>
              {visibleTransactions.map((tx, index) => {
                const actualIndex = startIndex + index;
                return (
                  <TableRow
                    key={tx.id}
                    className={cn(
                      'cursor-pointer hover:bg-muted/50 transition-colors',
                      selectedIds.has(tx.id) && 'bg-muted/30',
                      focusedRowIndex === actualIndex && 'outline-none ring-2 ring-primary'
                    )}
                    onClick={() => onRowClick?.(tx)}
                    onFocus={() => setFocusedRowIndex(actualIndex)}
                    tabIndex={-1}
                    role="row"
                    aria-selected={selectedIds.has(tx.id)}
                  >
                    {visibility.select && (
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
                    )}
                    {visibility.date && (
                      <TableCell className="w-[100px] sm:w-auto text-sm" role="cell">
                        {tx.date_formatted || tx.date}
                      </TableCell>
                    )}
                    {visibility.description && (
                      <TableCell className="max-w-[200px] sm:max-w-[300px] truncate text-sm" role="cell">
                        {tx.description}
                      </TableCell>
                    )}
                    {visibility.category && (
                      <TableCell className="hidden sm:table-cell" role="cell">
                        <Badge variant="secondary" className="text-xs">
                          {tx.category_name || 'Uncategorized'}
                        </Badge>
                      </TableCell>
                    )}
                    {visibility.merchant && (
                      <TableCell className="hidden md:table-cell text-sm" role="cell">
                        {tx.merchant_name || '-'}
                      </TableCell>
                    )}
                    {visibility.amount && (
                      <TableCell
                        className={cn(
                          'text-right font-mono tabular-nums text-sm',
                          tx.transaction_type === 'debit' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'
                        )}
                        role="cell"
                      >
                        {formatINR(tx.amount.paise)}
                      </TableCell>
                    )}
                  </TableRow>
                );
              })}
              {/* Spacer for rows after visible range */}
              <TableRow style={{ height: `${(transactions.length - endIndex) * rowHeight}px` }}>
                <TableCell colSpan={6} className="p-0 border-0" />
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}