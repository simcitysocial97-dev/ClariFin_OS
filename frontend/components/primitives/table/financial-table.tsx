/**
 * FinancialTable - Stage 8E Financial OS Visual Language
 *
 * Bloomberg-style dense financial table.
 * Hover-only, no zebra striping, sticky headers, tabular numbers.
 * Row virtualization ready via CSS.
 */

'use client';

import { cva } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';

// ===== Sort Direction =====
export type SortDirection = 'asc' | 'desc' | false;

// ===== Column Definition =====
export interface FinancialColumn<T = unknown> {
  id: string;
  header: string;
  accessor: (row: T) => React.ReactNode;
  align?: 'left' | 'right' | 'center';
  width?: string | number;
  minWidth?: string | number;
  sortable?: boolean;
  pin?: 'left' | 'right';
  className?: string;
}

// ===== Table Variants =====
export const tableVariants = cva('w-full', {
  variants: {
    density: {
      comfortable: '[&_td]:py-3 [&_th]:py-3',
      default: '[&_td]:py-2 [&_th]:py-2',
      compact: '[&_td]:py-1 [&_th]:py-1 text-sm',
      terminal: '[&_td]:py-0.5 [&_th]:py-0.5 text-xs font-mono',
    },
    striped: {
      true: '[&_tr:nth-child(even)]:bg-[var(--surface-raised)]',
      false: '',
    },
  },
  defaultVariants: {
    density: 'default',
    striped: false,
  },
});

// ===== Table Props =====
interface FinancialTableProps<T> {
  columns: FinancialColumn<T>[];
  data: T[];
  sortBy?: string;
  sortDir?: SortDirection;
  onSort?: (columnId: string) => void;
  onRowClick?: (row: T) => void;
  selectedId?: string;
  idAccessor?: (row: T) => string;
  density?: 'comfortable' | 'default' | 'compact' | 'terminal';
  striped?: boolean;
  stickyHeader?: boolean;
  className?: string;
  emptyMessage?: string;
  loading?: boolean;
  loadingRows?: number;
}

// ===== Table Component =====
export function FinancialTable<T>({
  columns,
  data,
  sortBy,
  sortDir,
  onSort,
  onRowClick,
  selectedId,
  idAccessor,
  density = 'default',
  striped = false,
  stickyHeader = true,
  className,
  emptyMessage = 'No data',
  loading = false,
  loadingRows = 5,
}: FinancialTableProps<T>) {
  if (loading) {
    return (
      <div className={cn('w-full', tableVariants({ density, striped }), className)}>
        <table className="w-full">
          {stickyHeader && (
            <thead className={cn('sticky top-0 z-10 bg-[var(--surface-default)]')}>
              <tr>
                {columns.map((col) => (
                  <th
                    key={col.id}
                    className={cn(
                      'px-3 text-left text-xs font-medium text-[var(--text-tertiary)] border-b border-[var(--border-default)]',
                      col.align === 'right' && 'text-right',
                      col.align === 'center' && 'text-center',
                    )}
                  >
                    {col.header}
                  </th>
                ))}
              </tr>
            </thead>
          )}
          <tbody>
            {Array.from({ length: loadingRows }).map((_, i) => (
              <tr key={i}>
                {columns.map((col) => (
                  <td key={col.id} className="px-3 py-2">
                    <div className="h-3 w-3/4 rounded bg-[var(--surface-interactive)] animate-pulse" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="fin-empty">
        <p className="fin-caption">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={cn('w-full', className)}>
      <table className={cn('w-full', tableVariants({ density, striped }))}>
        {stickyHeader && (
          <thead className="sticky top-0 z-10 bg-[var(--surface-default)]">
            <tr>
              {columns.map((col) => (
                <FinancialHeader
                  key={col.id}
                  column={col}
                  sortBy={sortBy}
                  sortDir={sortDir}
                  onSort={onSort}
                />
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {data.map((row, i) => {
            const id = idAccessor?.(row) ?? i.toString();
            return (
              <FinancialRow
                key={id}
                row={row}
                columns={columns}
                isSelected={selectedId === id}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              />
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ===== Financial Header =====
interface FinancialHeaderProps<T> {
  column: FinancialColumn<T>;
  sortBy?: string;
  sortDir?: SortDirection;
  onSort?: (columnId: string) => void;
}

function FinancialHeader<T>({
  column,
  sortBy,
  sortDir,
  onSort,
}: FinancialHeaderProps<T>) {
  const isSorted = sortBy === column.id;
  const canSort = column.sortable && onSort;

  return (
    <th
      className={cn(
        'px-3 text-left text-xs font-medium text-[var(--text-tertiary)] border-b border-[var(--border-default)] whitespace-nowrap select-none',
        column.align === 'right' && 'text-right',
        column.align === 'center' && 'text-center',
        canSort && 'cursor-pointer hover:text-[var(--text-primary)]',
        column.pin === 'left' && 'sticky left-0 bg-[var(--surface-default)] z-20',
        column.className,
      )}
      onClick={canSort ? () => onSort(column.id) : undefined}
      style={{
        width: column.width,
        minWidth: column.minWidth,
      }}
    >
      <div className="inline-flex items-center gap-1">
        {column.header}
        {canSort && (
          isSorted && sortDir ? (
            sortDir === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
          ) : (
            <ArrowUpDown className="h-3 w-3 opacity-30" />
          )
        )}
      </div>
    </th>
  );
}

// ===== Financial Row =====
interface FinancialRowProps<T> {
  row: T;
  columns: FinancialColumn<T>[];
  isSelected?: boolean;
  onClick?: () => void;
}

function FinancialRow<T>({
  row,
  columns,
  isSelected = false,
  onClick,
}: FinancialRowProps<T>) {
  return (
    <tr
      className={cn(
        'border-b border-[var(--border-subtle)] transition-colors duration-[50ms]',
        'hover:bg-[var(--color-hover-overlay)]',
        isSelected && 'bg-[var(--color-selection-halo)]',
        onClick && 'cursor-pointer',
      )}
      onClick={onClick}
      data-selected={isSelected || undefined}
    >
      {columns.map((col) => (
        <FinancialCell
          key={col.id}
          column={col}
          value={col.accessor(row)}
        />
      ))}
    </tr>
  );
}

// ===== Financial Cell =====
interface FinancialCellProps<T> {
  column: FinancialColumn<T>;
  value: React.ReactNode;
}

function FinancialCell<T>({ column, value }: FinancialCellProps<T>) {
  return (
    <td
      className={cn(
        'px-3 whitespace-nowrap',
        column.align === 'right' && 'text-right',
        column.align === 'center' && 'text-center',
        column.pin === 'left' && 'sticky left-0 bg-inherit z-10',
        column.className,
      )}
    >
      <div className="truncate max-w-[300px]">
        {value}
      </div>
    </td>
  );
}