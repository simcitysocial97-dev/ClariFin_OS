/**
 * Transaction Table Component - Stage 8E-C2 Production Visual System Migration
 *
 * Main table component for displaying transactions.
 * Uses FinancialTable primitive for consistent styling.
 * Keyboard navigation with arrow key support.
 * Accessibility with proper ARIA attributes.
 * Selection integrated with CommandCenterRuntime.
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { SkeletonTable } from '@/components/loading/skeleton-row';
import { EmptyState } from '@/components/loading/empty-state';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import type { TransactionViewModel } from '@/types/transaction-view-model';
import {
  hasCategoryNavigation,
  hasMerchantNavigation,
} from '@/lib/navigation';
import { MoneyValue } from '@/components/primitives/data-display/money-value';

interface ColumnVisibility {
  select: boolean;
  date: boolean;
  description: boolean;
  category: boolean;
  merchant: boolean;
  amount: boolean;
}

interface ColumnWidths {
  select?: number;
  date?: number;
  description?: number;
  category?: number;
  merchant?: number;
  amount?: number;
}

interface TransactionTableProps {
  transactions: TransactionViewModel[];
  loading?: boolean;
  error?: Error | null;
  onRowClick?: (transaction: TransactionViewModel) => void;
  onSelectionChange?: (id: string, selected: boolean) => void;
  selectedIds?: Set<string>;
  // Column visibility
  columnVisibility?: ColumnVisibility;
  // Column resizing
  columnWidths?: ColumnWidths;
  onColumnWidthsChange?: (widths: ColumnWidths) => void;
  // Virtualization
  virtualize?: boolean;
}

/**
 * Transaction Table Component
 * Displays a list of transactions with selection support
 * Responsive design: hides columns on smaller screens
 * Selection integrated with CommandCenterRuntime
 * Accessibility: includes ARIA attributes and keyboard support
 */
export function TransactionTable({
  transactions,
  loading = false,
  error = null,
  onRowClick,
  onSelectionChange,
  selectedIds = new Set(),
  columnVisibility,
  columnWidths,
  onColumnWidthsChange,
  virtualize,
}: TransactionTableProps) {
  const [focusedRowIndex, setFocusedRowIndex] = useState<number>(-1);
  const rowRefs = useRef<(HTMLTableRowElement | null)[]>([]);

  // Default column visibility
  const visibility = columnVisibility ?? {
    select: true,
    date: true,
    description: true,
    category: true,
    merchant: true,
    amount: true,
  };

  // Column widths and virtualization (for future implementation)
  void columnWidths;
  void onColumnWidthsChange;
  void virtualize;

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
      <div className="border-0 rounded-none bg-[var(--surface-default)]">
        <Table>
          <TableBody>
            <SkeletonTable rows={5} columns={6} />
          </TableBody>
        </Table>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <Alert variant="destructive">
          <AlertTitle>Error loading transactions</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="p-4">
        <EmptyState />
      </div>
    );
  }

  return (
    <div className="border-0 rounded-none bg-[var(--surface-default)]">
      <Table role="table" aria-label="Transactions">
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
          {transactions.map((tx, index) => (
            <TableRow
              key={tx.id}
              ref={(el) => { rowRefs.current[index] = el; }}
              className={cn(
                'cursor-pointer transition-colors duration-[50ms]',
                'hover:bg-[var(--color-hover-overlay)]',
                selectedIds.has(tx.id) && 'bg-[var(--color-selection-halo)]',
                focusedRowIndex === index && 'outline-none ring-2 ring-[var(--color-focus-ring)]'
              )}
              onClick={() => onRowClick?.(tx)}
              onFocus={() => setFocusedRowIndex(index)}
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
                  {hasCategoryNavigation(tx) ? (
                    <Link
                      href={`/transactions?category=${encodeURIComponent(tx.category_id || 'uncategorized')}`}
                      className="hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <span className="text-xs px-2 py-0.5 rounded bg-[var(--surface-raised)] cursor-pointer">
                        {tx.category_name || 'Uncategorized'}
                      </span>
                    </Link>
                  ) : (
                    <span className="text-xs px-2 py-0.5 rounded bg-[var(--surface-raised)]">
                      {tx.category_name || 'Uncategorized'}
                    </span>
                  )}
                </TableCell>
              )}
              {visibility.merchant && (
                <TableCell className="hidden md:table-cell text-sm" role="cell">
                  {hasMerchantNavigation(tx) ? (
                    <Link
                      href={`/transactions?merchant=${encodeURIComponent(tx.merchant_id || 'unknown')}`}
                      className="hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {tx.merchant_name || '-'}
                    </Link>
                  ) : (
                    <>{tx.merchant_name || '-'}</>
                  )}
                </TableCell>
              )}
              {visibility.amount && (
                <TableCell
                  className="text-right"
                  role="cell"
                >
                  <MoneyValue 
                    paise={tx.amount.paise} 
                    variant="default"
                    sign="never"
                  />
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}